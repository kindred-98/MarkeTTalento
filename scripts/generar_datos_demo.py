"""
Generador de datos demo para presentación de Predicciones ML.
Crea ~200 tickets de los últimos 6 meses con patrones estacionales realistas.
"""
import sqlite3
import random
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "markettalento.db")
CAJEROS = ["andres", "edu", "carlos", "alberto", "irrael", "YioQueSe", "fernando", "ernesto", "raul"]
METODOS_PAGO = ["efectivo", "tarjeta"]


def obtener_productos(conn):
    cur = conn.execute("SELECT id, nombre, precio_venta, categoria_id FROM productos WHERE activo = 1")
    return [
        {"id": r[0], "nombre": r[1], "precio": r[2], "categoria_id": r[3]}
        for r in cur.fetchall()
        if "test" not in r[1].lower()  # excluir productos de test
    ]


def contar_tickets_existentes(conn):
    cur = conn.execute("SELECT COUNT(*) FROM tickets")
    return cur.fetchone()[0]


def generar_ticket(conn, fecha, productos):
    """Genera un ticket con líneas aleatorias para una fecha dada."""
    cajero = random.choice(CAJEROS)
    metodo = random.choices(METODOS_PAGO, weights=[60, 40])[0]

    # Seleccionar 1-5 productos
    num_items = random.choices([1, 2, 3, 4, 5], weights=[15, 30, 30, 15, 10])[0]
    items = random.sample(productos, min(num_items, len(productos)))

    lineas = []
    total = 0.0
    for prod in items:
        cantidad = random.choices([1, 2, 3], weights=[70, 20, 10])[0]
        subtotal = round(cantidad * prod["precio"], 2)
        lineas.append({
            "producto_id": prod["id"],
            "cantidad": cantidad,
            "precio_unitario": prod["precio"],
            "subtotal": subtotal,
        })
        total += subtotal

    entrega = round(total + random.uniform(0, 20), 2) if metodo == "efectivo" else total
    cambio = round(entrega - total, 2) if metodo == "efectivo" else 0.0

    # Insertar ticket
    cur = conn.execute(
        """
        INSERT INTO tickets (numero_ticket, cajero, fecha, total, metodo_pago, entrega_efectivo, cambio, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("", cajero, fecha.strftime("%Y-%m-%d %H:%M:%S"), round(total, 2), metodo, entrega, cambio, "completado")
    )
    ticket_id = cur.lastrowid

    # Actualizar número de ticket
    conn.execute(
        "UPDATE tickets SET numero_ticket = ? WHERE id = ?",
        (str(ticket_id).zfill(6), ticket_id)
    )

    # Insertar líneas
    for linea in lineas:
        conn.execute(
            """
            INSERT INTO ticket_lineas (ticket_id, producto_id, cantidad, precio_unitario, subtotal)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, linea["producto_id"], linea["cantidad"], linea["precio_unitario"], linea["subtotal"])
        )

    return ticket_id


def calcular_probabilidad_ticket(fecha, productos):
    """Calcula probabilidad de generar un ticket en un día dado con estacionalidad."""
    base = 0.6  # 60% base de generar al menos 1 ticket

    mes = fecha.month
    dia_semana = fecha.weekday()

    # Fin de semana +30%
    if dia_semana >= 5:
        base += 0.25

    # Estacionalidad por mes
    if mes in [12, 1]:  # Navidad / Reyes
        base += 0.2
    elif mes in [7, 8]:  # Verano (si hubiera)
        base += 0.1

    return min(base, 1.0)


def aplicar_estacionalidad_productos(fecha, productos):
    """Aplica pesos estacionales a productos para que ciertos productos se vendan más en ciertas épocas."""
    mes = fecha.month
    dia_semana = fecha.weekday()

    pesos = []
    for p in productos:
        peso = 1.0
        cat = p["categoria_id"]
        nombre = p["nombre"].lower()

        # Bebidas frías / cerveza / verano-primavera
        if any(x in nombre for x in ["cerveza", "aquarius", "fuze", "coca", "agua"]):
            if mes in [3, 4, 5, 6, 7, 8, 9]:
                peso += 1.5
            else:
                peso += 0.5

        # Café / caliente -> invierno
        if any(x in nombre for x in ["cafe", "cortado", "americano", "solo"]):
            if mes in [10, 11, 12, 1, 2]:
                peso += 2.0
            else:
                peso += 0.8

        # Leche / desayuno -> todo el año, ligeramente más en invierno
        if any(x in nombre for x in ["leche", "pan", "harina", "desayuno"]):
            peso += 1.0
            if mes in [11, 12, 1, 2]:
                peso += 0.3

        # Vino / alcohol -> fines de semana
        if any(x in nombre for x in ["vino", "pagos", "estrella"]):
            if dia_semana >= 4:
                peso += 1.0
            else:
                peso += 0.3

        # Aceites / alimentos básicos -> constantes
        if cat == 5 or cat == 6:
            peso += 0.8

        pesos.append(peso)

    return pesos


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")

    existentes = contar_tickets_existentes(conn)
    print(f"Tickets existentes: {existentes}")

    productos = obtener_productos(conn)
    if not productos:
        print("No hay productos activos en la base de datos.")
        conn.close()
        return

    print(f"Productos activos encontrados: {len(productos)}")

    # Generar tickets para los últimos 180 días (~6 meses)
    hoy = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    total_generados = 0

    for i in range(180, -1, -1):
        fecha_dia = hoy - timedelta(days=i)
        prob = calcular_probabilidad_ticket(fecha_dia, productos)

        # Número de tickets en este día (0-3)
        if random.random() < prob:
            num_tickets = random.choices([1, 2, 3], weights=[60, 30, 10])[0]
            for _ in range(num_tickets):
                # Variar hora
                hora = random.randint(8, 22)
                minuto = random.randint(0, 59)
                fecha_ticket = fecha_dia.replace(hour=hora, minute=minuto)

                # Aplicar pesos estacionales a productos para este ticket
                pesos = aplicar_estacionalidad_productos(fecha_ticket, productos)
                productos_ponderados = random.choices(productos, weights=pesos, k=len(productos))
                # Tomar los primeros N únicos
                seleccionados = []
                vistos = set()
                for p in productos_ponderados:
                    if p["id"] not in vistos:
                        vistos.add(p["id"])
                        seleccionados.append(p)
                    if len(seleccionados) >= 5:
                        break

                generar_ticket(conn, fecha_ticket, seleccionados)
                total_generados += 1

    conn.commit()
    conn.close()

    print(f"Tickets generados: {total_generados}")
    print(f"Total tickets en BD: {existentes + total_generados}")


if __name__ == "__main__":
    main()
