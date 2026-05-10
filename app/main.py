"""
MarkeTTalento - Dashboard Principal
Aplicacion Streamlit modularizada con autenticacion JWT
"""
import streamlit as st
import os

# Configuracion de pagina DEBE ser lo primero
st.set_page_config(page_title="MarkeTTalento", page_icon="📦", layout="wide")

# Importaciones de la aplicacion
from app.utils.api import verificar_api, esperar_api
from app.utils.state import init_session_state
from app.components.sidebar import render_sidebar

# Importar paginas
from app.views import dashboard, productos, inventario, ventas, predicciones, vision_ai, barcode, login


@st.cache_resource
def get_css_content():
    """Cachea el contenido CSS para evitar lecturas repetidas de archivos."""
    css_files = [
        'app/styles/global.css',
        'app/styles/components.css',
        'app/styles/sidebar.css',
        'app/styles/dashboard.css',
        'app/styles/productos.css',
        'app/styles/inventario.css',
        'app/styles/ventas.css'
    ]
    
    css_content = ""
    for css_file in css_files:
        if os.path.exists(css_file):
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content += f.read() + "\n"
    
    return css_content


def load_css():
    """Carga todos los archivos CSS (usando cache)."""
    css_content = get_css_content()
    st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)


def main():
    """Funcion principal de la aplicacion."""
    # Cargar CSS
    load_css()
    
    # Inicializar estado
    init_session_state()
    
    # Verificar conexion con API
    if not st.session_state.get('api_conectada', False):
        with st.spinner("Conectando con la API..."):
            if esperar_api(intentos=5):
                st.session_state['api_conectada'] = True
            else:
                st.error("No se pudo conectar con la API. Asegurate de que esta corriendo.")
                st.info("Ejecuta: `python run.py` para iniciar todo el sistema")
                return
    
    # Verificar autenticacion
    if not st.session_state.get("auth_token"):
        # Mostrar pantalla de login
        login.render()
        return
    
    # Usuario autenticado: mostrar app completa
    menu = render_sidebar()
    
    # Router de paginas
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
    elif menu == "📸 Visión AI":
        vision_ai.render()
    elif menu == "🔍 Inspector":
        barcode.render()
    else:
        dashboard.render()


if __name__ == "__main__":
    main()
