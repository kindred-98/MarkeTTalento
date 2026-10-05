"""Productos helpers"""
from app.logic.inventario import calcular_estado_stock, color_barra_stock

STOCK_MAX_POR_DEFECTO = 100
UNIDADES = ["unidad", "kg", "litro", "paquete", "caja", "botella"]
UNIDAD_POR_DEFECTO = "unidad"
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

__all__ = [
    "UNIDADES", "UNIDAD_POR_DEFECTO", "STOCK_MAX_POR_DEFECTO",
    "TIEMPO_REPOSICION_POR_DEFECTO", "PRECIO_MINIMO", "LONGITUD_NOMBRE_MAX",
    "LONGITUD_SKU_MIN", "LONGITUD_SKU_MAX", "DIR_IMAGENES", "SIN_PROVEEDOR",
    "SIN_NOMBRE_PROVEEDOR", "NUEVO_PROVEEDOR", "PROVEEDOR_NUEVO",
    "SIN_CATEGORIA", "CATEGORIA_ID_POR_DEFECTO",
    "color_barra_stock", "get_estado_producto",
]


def get_estado_producto(prod_id, inventarios, productos):
    """Obtiene el estado de stock de un producto."""
    inv = next((i for i in inventarios if i.get("producto_id") == prod_id), None)
    prod = next((p for p in productos if p.get("id") == prod_id), None)
    if inv and prod:
        return calcular_estado_stock(
            inv.get("cantidad", 0), prod.get("stock_maximo", STOCK_MAX_POR_DEFECTO) or STOCK_MAX_POR_DEFECTO
        )
    return "Saludable"