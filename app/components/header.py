"""
Componente de Header para la aplicación
"""
import streamlit as st


def render_header():
    """Renderiza la cabecera principal (estilos en app/styles/dashboard.css)."""
    st.markdown("""
    <div class="hdr-c">
        <div class="hdr-x">
            <span class="hdr-i" aria-hidden="true">📦</span>
            <h1 class="hdr-h">MarkeTTalento</h1>
            <p class="hdr-p">Inventario y punto de venta con <span class="hdr-v">analítica avanzada</span></p>
            <div class="hdr-bad">
                <span class="hdr-b1">ML e IA</span>
                <span class="hdr-b2">Analytics</span>
                <span class="hdr-b3">Predicciones</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
