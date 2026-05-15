"""Productos helpers"""
from app.logic.inventario import calcular_estado_stock


def get_estado_producto(prod_id, inventarios, productos):
    """Obtiene el estado de stock de un producto."""
    inv = next((i for i in inventarios if i.get("producto_id") == prod_id), None)
    prod = next((p for p in productos if p.get("id") == prod_id), None)
    if inv and prod:
        return calcular_estado_stock(inv.get("cantidad", 0), prod.get("stock_maximo", 100) or 100)
    return "Saludable"
