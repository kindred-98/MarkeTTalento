"""
Componente de Badge de Estado para Stock
"""
import streamlit as st
from app.logic.inventario import get_estado_info, get_color_estado


def render_stock_badge(estado: str):
    """
    Renderiza un badge de estado.
    
    Args:
        estado: Estado del stock (Agotado, Crítico, Bajo, Saludable)
    """
    info = get_estado_info(estado)
    color = get_color_estado(estado)
    
    st.markdown(f"""
    <span style="padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;
                background: {color}30; color: {color}; border: 1px solid {color};">
        {info['texto']}
    </span>
    """, unsafe_allow_html=True)
