"""
MarkeTTalento - Dashboard Principal
Aplicación Streamlit modularizada
"""
import streamlit as st
import os

# Configuración de página DEBE ser lo primero
st.set_page_config(page_title="MarkeTTalento", page_icon="📦", layout="wide")

# Importaciones de la aplicación
from app.utils.api import verificar_api, esperar_api
from app.utils.state import init_session_state
from app.components.header import render_header
from app.components.sidebar import render_sidebar

# Importar páginas
from app.views import dashboard, productos, inventario, ventas, predicciones, vision_ai, barcode


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
    """Función principal de la aplicación."""
    # Cargar CSS
    load_css()
    
    # Inicializar estado
    init_session_state()
    
    # Verificar conexión con API
    if not st.session_state.get('api_conectada', False):
        with st.spinner("Conectando con la API..."):
            if esperar_api(intentos=5):
                st.session_state['api_conectada'] = True
            else:
                st.error("❌ No se pudo conectar con la API. Asegúrate de que está corriendo en http://127.0.0.1:8002")
                st.info("💡 Ejecuta: `python run.py` para iniciar todo el sistema")
                return
    
    # Header comentado - ahora el título está en cada página
    # render_header()
    
    # st.markdown("---")
    
    # Renderizar sidebar y obtener menú seleccionado
    menu = render_sidebar()
    
    # Router de páginas
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
    elif menu == "🔍 Barcode":
        barcode.render()
    else:
        dashboard.render()


if __name__ == "__main__":
    main()
