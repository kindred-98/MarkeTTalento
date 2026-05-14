"""Dashboard tabs"""
from app.views.dashboard.tabs.resumen_tab import render as resumen_tab
from app.views.dashboard.tabs.inventario_tab import render as inventario_tab
from app.views.dashboard.tabs.estadisticas_tab import render as estadisticas_tab

__all__ = ['resumen_tab', 'inventario_tab', 'estadisticas_tab']