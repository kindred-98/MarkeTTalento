"""Data getters for dashboard"""
import streamlit as st
from app.db import DatabaseAccess
from app.views.dashboard.config import CACHE_TTL


def _obj_to_dict(obj):
    if hasattr(obj, '__dict__'):
        result = {}
        for k, v in obj.__dict__.items():
            if k.startswith('_'):
                continue
            if hasattr(v, '__dict__'):
                result[k] = _obj_to_dict(v)
            else:
                result[k] = v
        return result
    return obj


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_productos():
    db = DatabaseAccess()
    try:
        productos = db.get_productos()
        return [_obj_to_dict(p) for p in productos]
    finally:
        db.close()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_inventario():
    db = DatabaseAccess()
    try:
        inventarios = db.get_inventario()
        return [_obj_to_dict(i) for i in inventarios]
    finally:
        db.close()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_tickets():
    db = DatabaseAccess()
    try:
        tickets = db.get_tickets(limite=500)
        return [_obj_to_dict(t) for t in tickets]
    finally:
        db.close()


@st.cache_data(ttl=CACHE_TTL, show_spinner=False)
def get_categorias():
    db = DatabaseAccess()
    try:
        cats = db.get_categorias()
        return [_obj_to_dict(c) for c in cats]
    finally:
        db.close()


def get_dashboard_data():
    productos = get_productos()
    inventarios = get_inventario()
    tickets = get_tickets()
    categorias = get_categorias()
    
    inv_map = {i.get('producto_id'): i.get('cantidad', 0) for i in inventarios}
    tickets_ok = [t for t in tickets if t.get('estado') == 'completado']
    
    total_ingresos = sum(t.get('total', 0) for t in tickets_ok)
    total_tickets = len(tickets_ok)
    total_stock = sum(inv_map.values())
    ticket_prom = total_ingresos / total_tickets if total_tickets > 0 else 0
    
    total_unidades = sum(
        l.get('cantidad', 0)
        for t in tickets_ok
        for l in t.get('lineas', [])
    )
    
    return {
        'productos': productos,
        'inventarios': inventarios,
        'inv_map': inv_map,
        'tickets': tickets,
        'tickets_ok': tickets_ok,
        'categorias': categorias,
        'total_ingresos': total_ingresos,
        'total_tickets': total_tickets,
        'total_stock': total_stock,
        'ticket_prom': ticket_prom,
        'total_unidades': total_unidades,
    }


def invalidate():
    get_productos.clear()
    get_inventario.clear()
    get_tickets.clear()
    get_categorias.clear()