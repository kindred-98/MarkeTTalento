"""
Generador de datos demo para presentación de Predicciones ML.
Crea ~200 tickets de los últimos 6 meses con patrones estacionales realistas.
"""
import sqlite3
import random
from datetime import timedelta
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.utils.fechas import utcnow_naive

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


def calcular_probabilidad_ticket(fecha):
    """Calcula probabilidad de generar un ticket en un día dado con estacionalidad."""
    base = 0.6  # 60% base de generar al menos 1 ticket

    # Fin de semana +30%
    if fecha.weekday() >= MESES_FIN_DE_SEMANA_MIN:
        base += BONO_FIN_DE_SEMANA

    # Estacionalidad por mes
    mes = fecha.month
    if mes in MESES_NAVIDAD:  # Navidad / Reyes
        base += BONO_NAVIDAD
    elif mes in MESES_VERANO:  # Verano (si hubiera)
        base += BONO_VERANO

    return min(base, 1.0)


MESES_FIN_DE_SEMANA_MIN = 5
DIAS_CERVEZA_MIN = 4
BONO_FIN_DE_SEMANA = 0.25
BONO_NAVIDAD = 0.2
BONO_VERANO = 0.1
MESES_NAVIDAD = (12, 1)
MESES_VERANO = (7, 8)

# Reglas de estacionalidad por producto.
# (terminos, meses en temporada, dia_semana_min, peso_base, peso_temporada)
REGLAS_ESTACIONALIDAD = (
    (("cerveza", "aquarius", "fuze", "coca", "agua"), (3, 4, 5, 6, 7, 8, 9), None, 0.5, 1.0),
    (("cafe", "cortado", "americano", "solo"), (10, 11, 12, 1, 2), None, 0.8, 1.2),
    (("leche", "pan", "harina", "desayuno"), (11, 12, 1, 2), None, 1.0, 0.3),
    (("vino", "pagos", "estrella"), (), DIAS_CERVEZA_MIN, 0.3, 0.7),
)
# Categorias de alimentos basicos (aceites, etc.): venta constante.
CATEGORIAS_BASICAS = (5, 6)
PESO_CATEGORIA_BASICA = 0.8


def _regla_en_temporada(regla, mes, dia_semana):
    """Indica si una regla de estacionalidad aplica en la fecha dada."""
    _, meses, dia_min, _, _ = regla
    en_meses = bool(meses) and mes in meses
    en_dias = dia_min is not None and dia_semana >= dia_min
    return en_meses or en_dias


def _peso_producto(producto, mes, dia_semana):
    """Calcula el peso estacional de un producto concreto."""
    nombre = producto["nombre"].lower()
    peso = 1.0

    for regla in REGLAS_ESTACIONALIDAD:
        terminos, _, _, peso_base, peso_temporada = regla
        if not any(termino in nombre for termino in terminos):
            continue
        peso += peso_base
        if _regla_en_temporada(regla, mes, dia_semana):
            peso += peso_temporada

    if producto["categoria_id"] in CATEGORIAS_BASICAS:
        peso += PESO_CATEGORIA_BASICA

    return peso


def aplicar_estacionalidad_productos(fecha, productos):
    """Aplica pesos estacionales a productos para que ciertos productos se vendan más en ciertas épocas."""
    return [_peso_producto(p, fecha.month, fecha.weekday()) for p in productos]


DIAS_HISTORIAL = 180
MAX_LINEAS_POR_TICKET = 5
HORA_MINIMA = 8
HORA_MAXIMA = 22
PESOS_TICKETS_POR_DIA = ([1, 2, 3], [60, 30, 10])


def _elegir_productos(productos, fecha_ticket):
    """Selecciona hasta MAX_LINEAS_POR_TICKET productos según su peso estacional."""
    pesos = aplicar_estacionalidad_productos(fecha_ticket, productos)
    ponderados = random.choices(productos, weights=pesos, k=len(productos))

    seleccionados, vistos = [], set()
    for p in ponderados:
        if p["id"] not in vistos:
            vistos.add(p["id"])
            seleccionados.append(p)
        if len(seleccionados) >= MAX_LINEAS_POR_TICKET:
            break

    return seleccionados


def _generar_ticket_del_dia(conn, fecha_dia, productos):
    """Genera los tickets de un día. Devuelve cuántos se han creado."""
    if random.random() >= calcular_probabilidad_ticket(fecha_dia):
        return 0

    num_tickets = random.choices(*PESOS_TICKETS_POR_DIA)[0]
    for _ in range(num_tickets):
        fecha_ticket = fecha_dia.replace(
            hour=random.randint(HORA_MINIMA, HORA_MAXIMA),
            minute=random.randint(0, 59),
        )
        generar_ticket(conn, fecha_ticket, _elegir_productos(productos, fecha_ticket))

    return num_tickets


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
    hoy = utcnow_naive().replace(hour=12, minute=0, second=0, microsecond=0)
    total_generados = 0

    for i in range(DIAS_HISTORIAL, -1, -1):
        total_generados += _generar_ticket_del_dia(conn, hoy - timedelta(days=i), productos)

    conn.commit()
    conn.close()

    print(f"Tickets generados: {total_generados}")
    print(f"Total tickets en BD: {existentes + total_generados}")


if __name__ == "__main__":
    main()
