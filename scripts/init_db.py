"""
Inicializa la base de datos con datos de demo.
Compatible con SQLite y PostgreSQL.
"""
import os
import sys
from datetime import datetime, timezone, timedelta
from random import choice, randint
from sqlalchemy import func

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database.database import SessionLocal, engine, init_db
from src.core.security.auth import get_password_hash
from src.dominio.entidades.entidades import (
    Base, Usuario, Categoria, Proveedor, Producto, Inventario, Ticket, TicketLinea
)


def crear_usuarios(db):
    """Crea usuarios por defecto si no existen."""
    if db.query(Usuario).filter(Usuario.username == "admin").first():
        print("[SKIP] Usuarios ya existen")
        return

    admin = Usuario(
        username="admin",
        email="admin@markettalento.com",
        hashed_password=get_password_hash("admin123"),
        nombre_completo="Administrador",
        rol="admin",
        activo=True,
    )
    db.add(admin)

    cajeros = ["andres", "edu", "carlos", "alberto", "irrael", "YioQueSe", "fernando", "ernesto", "raul"]
    for c in cajeros:
        db.add(Usuario(
            username=c,
            hashed_password=get_password_hash(c),
            nombre_completo=c.capitalize(),
            rol="cajero",
            activo=True,
        ))

    db.commit()
    print(f"[OK] {1 + len(cajeros)} usuarios creados")


def crear_categorias(db):
    """Crea categorias por defecto."""
    if db.query(Categoria).first():
        print("[SKIP] Categorias ya existen")
        return

    categorias = [
        Categoria(nombre="Bebidas", descripcion="Refrescos, agua, zumos"),
        Categoria(nombre="Lacteos", descripcion="Leche, yogures, quesos"),
        Categoria(nombre="Panaderia", descripcion="Pan, bolleria"),
        Categoria(nombre="Frutas", descripcion="Fruta fresca"),
        Categoria(nombre="Verduras", descripcion="Verduras frescas"),
        Categoria(nombre="Carnes", descripcion="Carne fresca y congelada"),
        Categoria(nombre="Pescados", descripcion="Pescado fresco y congelado"),
        Categoria(nombre="Dulces", descripcion="Chocolates, caramelos"),
        Categoria(nombre="Snacks", descripcion="Patatas fritas, frutos secos"),
        Categoria(nombre="Congelados", descripcion="Helados, pizzas congeladas"),
    ]
    db.add_all(categorias)
    db.commit()
    print(f"[OK] {len(categorias)} categorias creadas")


def crear_proveedores(db):
    """Crea proveedores por defecto."""
    if db.query(Proveedor).first():
        print("[SKIP] Proveedores ya existen")
        return

    proveedores = [
        Proveedor(nombre="Distribuciones Gonzalez", contacto="Juan Gonzalez", telefono="912345678", email="juan@gonzalez.com"),
        Proveedor(nombre="Lacteos del Valle", contacto="Maria Lopez", telefono="913456789", email="maria@valle.com"),
        Proveedor(nombre="Panaderia Artesanal", contacto="Carlos Ruiz", telefono="914567890", email="carlos@panaderia.com"),
        Proveedor(nombre="Frutas y Verduras SL", contacto="Ana Martinez", telefono="915678901", email="ana@fysl.com"),
        Proveedor(nombre="Carniceria Selecta", contacto="Pedro Sanchez", telefono="916789012", email="pedro@carniceria.com"),
    ]
    db.add_all(proveedores)
    db.commit()
    print(f"[OK] {len(proveedores)} proveedores creados")


def crear_productos_e_inventario(db):
    """Crea productos e inventario inicial."""
    if db.query(Producto).first():
        print("[SKIP] Productos ya existen")
        return

    productos_data = [
        ("Coca-Cola", "8431234567890", "BEB001", 1.50, 1, 1),
        ("Leche Entera", "8431234567891", "LAC001", 1.20, 2, 2),
        ("Pan de Barra", "8431234567892", "PAN001", 0.80, 3, 3),
        ("Manzanas", "8431234567893", "FRU001", 2.50, 4, 4),
        ("Tomates", "8431234567894", "VER001", 1.80, 5, 4),
        ("Pollo Entero", "8431234567895", "CAR001", 6.50, 6, 5),
        ("Salmon Fresco", "8431234567896", "PES001", 12.00, 7, 4),
        ("Chocolate Nestle", "8431234567897", "DUL001", 2.00, 8, 1),
        ("Patatas Lays", "8431234567898", "SNA001", 1.50, 9, 1),
        ("Pizza Congelada", "8431234567899", "CON001", 3.50, 10, 1),
        ("Agua Mineral", "8431234567900", "BEB002", 0.60, 1, 1),
        ("Yogur Natural", "8431234567901", "LAC002", 1.10, 2, 2),
        ("Croissant", "8431234567902", "PAN002", 1.00, 3, 3),
        ("Platanos", "8431234567903", "FRU002", 1.90, 4, 4),
        ("Lechuga", "8431234567904", "VER002", 1.50, 5, 4),
        ("Ternera", "8431234567905", "CAR002", 15.00, 6, 5),
        ("Atun Enlatado", "8431234567906", "PES002", 2.50, 7, 1),
        ("Galletas Maria", "8431234567907", "DUL002", 1.30, 8, 1),
        ("Frutos Secos", "8431234567908", "SNA002", 3.00, 9, 1),
        ("Helado Vainilla", "8431234567909", "CON002", 4.00, 10, 1),
        ("Zumo de Naranja", "8431234567910", "BEB003", 2.20, 1, 1),
    ]

    productos = []
    for nombre, barcode, sku, precio, cat_id, prov_id in productos_data:
        p = Producto(
            nombre=nombre,
            descripcion=f"Producto {nombre}",
            precio_venta=precio,
            unidad="ud",
            codigo_barras=barcode,
            sku=sku,
            categoria_id=cat_id,
            proveedor_id=prov_id,
            activo=True,
        )
        db.add(p)
        db.flush()  # Para obtener el ID
        productos.append(p)

        inv = Inventario(
            producto_id=p.id,
            cantidad=randint(10, 50),
            ubicacion="Almacen Principal",
        )
        db.add(inv)

    db.commit()
    print(f"[OK] {len(productos)} productos e inventario creados")
    return productos


def crear_tickets_demo(db, productos):
    """Crea tickets de demo con patrones estacionales."""
    if db.query(Ticket).first():
        print("[SKIP] Tickets ya existen")
        return

    cajeros = ["andres", "edu", "carlos", "alberto", "irrael", "YioQueSe", "fernando", "ernesto", "raul"]
    metodos = ["efectivo", "tarjeta", "movil"]

    hoy = datetime.now(timezone.utc)
    tickets_creados = 0

    ultimo_id = db.query(func.max(Ticket.id)).scalar() or 0

    for dias_atras in range(180, 0, -1):
        fecha = hoy - timedelta(days=dias_atras)
        # Mas tickets en fines de semana
        num_tickets = randint(2, 5) if fecha.weekday() >= 5 else randint(1, 3)

        for _ in range(num_tickets):
            total = 0.0
            lineas = []
            num_lineas = randint(1, 4)

            for _ in range(num_lineas):
                prod = choice(productos)
                cantidad = randint(1, 3)
                precio = prod.precio_venta
                linea = TicketLinea(
                    producto_id=prod.id,
                    cantidad=cantidad,
                    precio_unitario=precio,
                    subtotal=cantidad * precio,
                )
                lineas.append(linea)
                total += cantidad * precio

            ticket = Ticket(
                numero_ticket=str(ultimo_id + tickets_creados + 1).zfill(6),
                fecha=fecha,
                total=round(total, 2),
                cajero=choice(cajeros),
                metodo_pago=choice(metodos),
                estado="completado",
                lineas=lineas,
            )
            db.add(ticket)
            tickets_creados += 1

    db.commit()
    print(f"[OK] {tickets_creados} tickets de demo creados")


def main():
    print("=== Inicializacion de Base de Datos ===")
    init_db()
    print("[OK] Tablas creadas")

    db = SessionLocal()
    try:
        crear_usuarios(db)
        crear_categorias(db)
        crear_proveedores(db)
        productos = crear_productos_e_inventario(db)
        if productos:
            crear_tickets_demo(db, productos)
        print("\n[OK] Base de datos inicializada correctamente")
    finally:
        db.close()


if __name__ == "__main__":
    main()
