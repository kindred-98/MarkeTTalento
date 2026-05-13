"""
Componente de Sidebar para navegación
"""
import streamlit as st
from app.utils.state import get_menu, set_menu


def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='text-align: center; font-family: \"Cascadia Code\", \"Orbitron\", monospace;'>⚡ Menú</h2>", unsafe_allow_html=True)
        
        menu = get_menu()
        
        user = st.session_state.get("auth_user", {})
        if user:
            st.markdown(f"""
            <div style="padding: 10px; background: rgba(255,255,255,0.03); border-radius: 10px; margin-bottom: 10px; text-align: center;">
                <div style="font-size: 1.2rem;">👤</div>
                <div style="font-weight: 600; color: #f1f5f9; font-size: 0.9rem;">{user.get('nombre_completo', user.get('username', 'Usuario'))}</div>
                <div style="color: #64748b; font-size: 0.75rem; text-transform: uppercase;">{user.get('rol', 'cajero')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        menu_items = [
            ("🏠 Dashboard", "card-dashboard"),
            ("📦 Productos", "card-productos"),
            ("📊 Inventario", "card-inventario"),
            ("💰 Ventas", "card-ventas"),
            ("🔮 Predicciones", "card-predicciones"),
            ("🔍 Inspector", "card-link"),
        ]

        for label, card_class in menu_items:
            if st.button(label, key=f"btn_{label.replace(' ', '_').replace('🔍', 'barcode')}"):
                set_menu(label)
                st.rerun()
        
        st.markdown("---")
        st.markdown("<div style='padding: 8px 0;'><hr style='border-color: rgba(255,255,255,0.05);'></div>", unsafe_allow_html=True)

        # API Docs section
        st.markdown("<p style='color: #64748b; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 5px;'><span style='color: #00f0ff;'>⚙</span> Sistema</p>", unsafe_allow_html=True)
        if st.button("📚 API Docs", key="btn_api_docs"):
            set_menu("📚 API Docs")
            st.rerun()
        
        st.markdown("---")
        
        if st.button("🚪 Cerrar Sesión", width="stretch", type="secondary"):
            for key in ["auth_token", "auth_user", "api_conectada"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        st.markdown("""
        <div style="padding: 15px; background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(0, 0, 0, 0.2)); border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.3); margin-bottom: 10px;">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="width: 10px; height: 10px; background: #10b981; border-radius: 50%; margin-right: 8px; animation: pulse 2s infinite;"></span>
                <span style="color: #10b981; font-weight: 600;">Streamlit Online</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        return menu