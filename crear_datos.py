from main import app
from src.core.database.database import SessionLocal, engine
from src.dominio.entidades.entidades import Categoria, Proveedor, Producto, Inventario, Venta, Base
from datetime import datetime, timedelta
import random

DATOS_PRODUCTOS = [
    {"nombre": "Leche", "categoria": "Lacteos", "precio": 1.20, "unidad": "litro", "stock_minimo": 5, "stock_maximo": 30, "tiempo_reposicion": 2},
    {"nombre": "Huevos", "categoria": "Huevos", "precio": 2.50, "unidad": "docena", "stock_minimo": 3, "stock_maximo": 20, "tiempo_reposicion": 1},
    {"nombre": "Pan", "categoria": "Panaderia", "precio": 0.90, "unidad": "unidad", "stock_minimo": 10, "stock_maximo": 50, "tiempo_reposicion": 1},
    {"nombre": "Agua", "categoria": "Bebidas", "precio": 0.60, "unidad": "botella", "stock_minimo": 15, "stock_maximo": 100, "tiempo_reposicion": 3},
    {"nombre": "Cafe", "categoria": "Bebidas", "precio": 4.50, "unidad": "paquete", "stock_minimo": 3, "stock_maximo": 25, "tiempo_reposicion": 5},
    {"nombre": "Arroz", "categoria": "Alimentos", "precio": 1.80, "unidad": "kg", "stock_minimo": 10, "stock_maximo": 60, "tiempo_reposicion": 4},
    {"nombre": "Aceite", "categoria": "Aceites", "precio": 4.20, "unidad": "litro", "stock_minimo": 8, "stock_maximo": 40, "tiempo_reposicion": 4},
    {"nombre": "Azucar", "categoria": "Alimentos", "precio": 1.50, "unidad": "kg", "stock_minimo": 10, "stock_maximo": 50, "tiempo_reposicion": 3},
    {"nombre": "Harina", "categoria": "Alimentos", "precio": 1.20, "unidad": "kg", "stock_minimo": 10, "stock_maximo": 60, "tiempo_reposicion": 3},
    {"nombre": "Galletas", "categoria": "Snacks", "precio": 2.30, "unidad": "paquete", "stock_minimo": 12, "stock_maximo": 45, "tiempo_reposicion": 2},
    {"nombre": "Cereal", "categoria": "Desayuno", "precio": 3.80, "unidad": "caja", "stock_minimo": 6, "stock_maximo": 30, "tiempo_reposicion": 5},
]

CATEGORIAS = ["Lacteos", "Huevos", "Panaderia", "Bebidas", "Alimentos", "Aceites", "Snacks", "Desayuno"]


def populate():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    print("Creando categorias...")
    cats = {}
    for cat_nombre in CATEGORIAS:
        cat = Categoria(nombre=cat_nombre, descripcion=f"Categoria {cat_nombre}")
        db.add(cat)
        db.flush()
        cats[cat_nombre] = cat.id
    
    print("Creando proveedor...")
    proveedor = Proveedor(nombre="DistribuidorLocal", contacto="Local", email="local@distribuidor.com")
    db.add(proveedor)
    db.flush()
    
    print("Creando productos...")
    for i, prod in enumerate(DATOS_PRODUCTOS):
        producto = Producto(
            sku=f"PROD{i+1:03d}",
            nombre=prod["nombre"],
            precio_venta=prod["precio"],
            precio_coste=prod["precio"] * 0.7,
            unidad=prod["unidad"],
            stock_minimo=prod["stock_minimo"],
            stock_maximo=prod["stock_maximo"],
            tiempo_reposicion=prod["tiempo_reposicion"],
            categoria_id=cats[prod["categoria"]],
            proveedor_id=proveedor.id
        )
        db.add(producto)
        db.flush()
        
        inventario = Inventario(
            producto_id=producto.id,
            cantidad=random.randint(prod["stock_minimo"], prod["stock_maximo"]),
            ubicacion="Estanteria A"
        )
        db.add(inventario)
    
    db.commit()
    print(f"OK: Creados {len(DATOS_PRODUCTOS)} productos")
    
    db.close()


if __name__ == "__main__":
    populate()