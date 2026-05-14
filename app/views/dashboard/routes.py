"""Dashboard routes - Ensambla tabs"""
import streamlit as st
from app.views.dashboard.tabs.resumen_tab import render as resumen_tab
from app.views.dashboard.tabs.inventario_tab import render as inventario_tab
from app.views.dashboard.tabs.estadisticas_tab import render as estadisticas_tab


def render():
    st.markdown("<h1>📊 Dashboard</h1>", unsafe_allow_html=True)
    
    tab_resumen, tab_inventario, tab_estadisticas = st.tabs([
        "📈 Resumen",
        "📦 Inventario",
        "📊 Estadísticas"
    ])
    
    with tab_resumen:
        resumen_tab()
    
    with tab_inventario:
        inventario_tab()
    
    with tab_estadisticas:
        estadisticas_tab()