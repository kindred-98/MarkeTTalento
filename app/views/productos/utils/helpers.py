"""Productos helpers"""
from app.logic.inventario import calcular_estado_stock

UNIDADES = ["unidad", "kg", "litro", "paquete", "caja", "botella"]
UNIDAD_POR_DEFECTO = "unidad"
STOCK_MAX_POR_DEFECTO = 100
TIEMPO_REPOSICION_POR_DEFECTO = 3
PRECIO_MINIMO = 0.01
LONGITUD_NOMBRE_MAX = 50
LONGITUD_SKU_MIN = 4
LONGITUD_SKU_MAX = 20
DIR_IMAGENES = "docs/img_productos"
SIN_PROVEEDOR = "Sin proveedor"
SIN_NOMBRE_PROVEEDOR = "Sin nombre"
NUEVO_PROVEEDOR = "➕ Nuevo proveedor"
PROVEEDOR_NUEVO = "nuevo"
SIN_CATEGORIA = "Sin categoría"
CATEGORIA_ID_POR_DEFECTO = 1
COLOR_SALUDABLE = "#10b981"
COLOR_BAJO = "#f59e0b"
COLOR_CRITICO = "#ef4444"
PORC_CRITICO = 20
PORC_BAJO = 50


def get_estado_producto(prod_id, inventarios, productos):
    """Obtiene el estado de stock de un producto."""
    inv = next((i for i in inventarios if i.get("producto_id") == prod_id), None)
    prod = next((p for p in productos if p.get("id") == prod_id), None)
    if inv and prod:
        return calcular_estado_stock(
            inv.get("cantidad", 0), prod.get("stock_maximo", STOCK_MAX_POR_DEFECTO) or STOCK_MAX_POR_DEFECTO
        )
    return "Saludable"


def color_barra_stock(pct):
    """Devuelve el color de la barra de progreso segun el porcentaje de stock."""
    if pct <= PORC_CRITICO:
        return COLOR_CRITICO
    if pct <= PORC_BAJO:
        return COLOR_BAJO
    return COLOR_SALUDABLE