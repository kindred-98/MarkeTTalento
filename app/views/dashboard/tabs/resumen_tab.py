"""Resumen tab - KPIs y métricas principales"""
import streamlit as st
from app.views.dashboard.data.getters import get_dashboard_data
from app.views.dashboard.components.metricas import metric_card
from app.views.dashboard.config import COLORS


def render():
    data = get_dashboard_data()
    
    metrics = [
        ("💰", "Ticket Promedio", f"€{data['ticket_prom']:.2f}", COLORS["success"], "VENTAS"),
        ("📦", "Stock Total", data["total_stock"], COLORS["primary"], "STOCK"),
        ("⚠️", "Alertas", _get_alertas(data), COLORS["danger"], "RIESGO"),
        ("🎫", "Tickets", data["total_tickets"], COLORS["purple"], "TPV"),
    ]

    cols = st.columns(4)
    for col, (icon, label, value, color, tag) in zip(cols, metrics):
        metric_card(col, icon, label, value, color, tag=tag)


def _get_alertas(data):
    from app.views.dashboard.config import get_stock_status
    count = 0
    for p in data['productos']:
        stock = data['inv_map'].get(p.get('id'), 0)
        if get_stock_status(stock, p.get('stock_maximo')) in ['Crítico', 'Agotado']:
            count += 1
    return count