"""Productos helpers"""
import os
from app.logic.inventario import calcular_estado_stock


def get_image_path(img_url):
    """Resuelve la ruta de una imagen."""
    if not img_url:
        return None
    if os.path.isabs(img_url):
        return img_url
    return os.path.join(os.getcwd(), img_url)


def get_estado_producto(prod_id, inventarios, productos):
    """Obtiene el estado de stock de un producto."""
    inv = next((i for i in inventarios if i.get("producto_id") == prod_id), None)
    prod = next((p for p in productos if p.get("id") == prod_id), None)
    if inv and prod:
        return calcular_estado_stock(inv.get("cantidad", 0), prod.get("stock_maximo", 100) or 100)
    return "Saludable"


def build_search_index(productos, inventarios):
    """Construye índice de búsqueda."""
    index = {}
    for p in productos:
        pid = p.get("id")
        nombre_lower = p.get("nombre", "").lower()
        sku_lower = p.get("sku", "").lower()
        estado = get_estado_producto(pid, inventarios, productos)
        index[pid] = {
            "nombre": nombre_lower,
            "sku": sku_lower,
            "estado": estado,
            "categoria_id": p.get("categoria_id")
        }
    return index