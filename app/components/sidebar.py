"""
Componente de Sidebar para navegación
"""
import streamlit as st
from app.utils.state import get_menu, set_menu


def render_sidebar():
    """Renderiza el menú lateral completo."""
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; font-family: \"Cascadia Code\", \"Orbitron\", monospace;'>⚡ Menú</h2>", unsafe_allow_html=True)
        
        menu = get_menu()
        
        st.markdown("---")
        
        # Botones de navegación
        cols = st.columns(1)
        
        menu_items = [
            ("🏠 Dashboard", "card-dashboard"),
            ("📦 Productos", "card-productos"),
            ("📊 Inventario", "card-inventario"),
            ("💰 Ventas", "card-ventas"),
            ("🔮 Predicciones", "card-predicciones"),
            ("📸 Visión AI", "card-vision"),
            ("🔍 Barcode", "card-link"),
        ]
        
        for label, card_class in menu_items:
            if st.button(label, use_container_width=True, key=f"btn_{label.replace(' ', '_').replace('🔍', 'barcode')}"):
                set_menu(label)
                st.rerun()
        
        st.markdown("---")
        
        # Status de API
        st.markdown("""
        <div style="padding: 15px; background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(0, 0, 0, 0.2)); border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3); margin-bottom: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="width: 10px; height: 10px; background: #10b981; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite;"></span>
                <span style="color: #10b981; font-weight: 600;">API Online</span>
                <span style="color: #64748b; margin-left: auto; font-size: 0.85rem;">Puerto: 8002</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Link a API Docs
        st.markdown("""
        <a href="http://localhost:8002/docs" target="_blank" style="display: block; padding: 10px; background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(0, 0, 0, 0.1)); border-radius: 10px; border: 1px solid rgba(139, 92, 246, 0.2); text-decoration: none; text-align: center;">
            <span style="color: #8b5cf6;">📚 API Docs</span>
        </a>
        """, unsafe_allow_html=True)
        
        return menu
