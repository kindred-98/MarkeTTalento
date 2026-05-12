"""
MarkeTTalento - Dashboard Principal
Acceso directo a SQLite, sin API externa
"""
import streamlit as st
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

st.set_page_config(page_title="MarkeTTalento", page_icon="📦", layout="wide")

from app.utils.state import init_session_state
from app.components.sidebar import render_sidebar
from app.views import dashboard, productos, inventario, ventas, predicciones, barcode, login, api_docs
from app.db import DatabaseAccess


@st.cache_resource
def get_css_content():
    css_files = ['app/styles/global.css', 'app/styles/components.css', 'app/styles/sidebar.css',
                 'app/styles/dashboard.css', 'app/styles/productos.css', 'app/styles/inventario.css', 'app/styles/ventas.css']
    css_content = ""
    for css_file in css_files:
        if os.path.exists(css_file):
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content += f.read() + "\n"
    return css_content


def load_css():
    css_content = get_css_content()
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def verificar_db():
    try:
        db_path = "data/markettalento.db"
        if not os.path.exists(db_path):
            return False
        db = DatabaseAccess()
        cats = db.get_categorias()
        return len(cats) >= 0
    except Exception:
        return False


def main():
    load_css()
    init_session_state()
    
    if not verificar_db():
        st.error("⚠️ Base de datos no encontrada. Ejecuta: python scripts/init_db.py")
        st.info("Consulta la documentación para configurar la base de datos.")
        return
    
    from app.auth_local import autenticar_usuario
    if not st.session_state.get("auth_token"):
        login.render()
        return
    
    menu = render_sidebar()
    
    if menu == "🏠 Dashboard":
        dashboard.render()
    elif menu == "📦 Productos":
        productos.render()
    elif menu == "📊 Inventario":
        inventario.render()
    elif menu == "💰 Ventas":
        ventas.render()
    elif menu == "🔮 Predicciones":
        predicciones.render()
    elif menu == "🔍 Inspector":
        barcode.render()
    elif menu == "📚 API Docs":
        api_docs.render()


if __name__ == "__main__":
    main()