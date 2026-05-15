"""Productos data getters"""
import json
import pandas as pd
import streamlit as st
from app.db import DatabaseAccess
from app.utils.helpers import to_excel


def _to_dict(obj):
    """Convierte objeto a dict."""
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


@st.cache_data(show_spinner=False)
def get_productos_data():
    """Obtiene datos de productos, inventarios, categorías y proveedores desde SQLite."""
    db = DatabaseAccess()
    try:
        productos = db.get_productos()
        inventarios = db.get_inventario()
        categorias = db.get_categorias()
        proveedores = db.get_proveedores()

        productos = [_to_dict(p) for p in productos]
        inventarios = [_to_dict(i) for i in inventarios]
        categorias = [_to_dict(c) for c in categorias]
        proveedores = [_to_dict(p) for p in proveedores]

        return productos, inventarios, categorias, proveedores
    finally:
        db.close()


def export_to_json(productos, inventarios, categorias, proveedores):
    """Exporta productos a JSON con datos relacionados."""
    cat_map = {c.get("id"): c.get("nombre") for c in categorias}
    prov_map = {p.get("id"): p.get("nombre") for p in proveedores}
    inv_map = {i.get("producto_id"): i.get("cantidad", 0) for i in inventarios}

    exportar = []
    for p in productos:
        pid = p.get("id")
        exportar.append({
            "sku": p.get("sku"),
            "nombre": p.get("nombre"),
            "descripcion": p.get("descripcion"),
            "categoria": cat_map.get(p.get("categoria_id"), "Sin categoría"),
            "proveedor": prov_map.get(p.get("proveedor_id"), "Sin proveedor"),
            "precio_venta": p.get("precio_venta"),
            "precio_coste": p.get("precio_coste"),
            "unidad": p.get("unidad"),
            "stock": inv_map.get(pid, 0),
            "stock_maximo": p.get("stock_maximo"),
            "codigo_barras": p.get("codigo_barras"),
            "tiempo_reposicion": p.get("tiempo_reposicion")
        })
    return json.dumps(exportar, ensure_ascii=False, indent=2)


def export_to_excel(productos, inventarios, categorias, proveedores):
    """Exporta productos a Excel."""
    cat_map = {c.get("id"): c.get("nombre") for c in categorias}
    prov_map = {p.get("id"): p.get("nombre") for p in proveedores}
    inv_map = {i.get("producto_id"): i.get("cantidad", 0) for i in inventarios}

    data = []
    for p in productos:
        pid = p.get("id")
        data.append({
            "SKU": p.get("sku"),
            "Nombre": p.get("nombre"),
            "Descripción": p.get("descripcion"),
            "Categoría": cat_map.get(p.get("categoria_id"), "Sin categoría"),
            "Proveedor": prov_map.get(p.get("proveedor_id"), "Sin proveedor"),
            "Precio Venta": p.get("precio_venta"),
            "Precio Coste": p.get("precio_coste"),
            "Unidad": p.get("unidad"),
            "Stock": inv_map.get(pid, 0),
            "Stock Máximo": p.get("stock_maximo"),
            "Código Barras": p.get("codigo_barras"),
            "Días Reposición": p.get("tiempo_reposicion")
        })

    df = pd.DataFrame(data)
    return to_excel(df)