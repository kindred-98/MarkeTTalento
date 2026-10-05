"""Productos routes - Navegación principal"""
import streamlit as st
from app.views.productos.tabs.catalogo_tab import render as catalogo_tab
from app.views.productos.tabs.nuevo_tab import render as nuevo_tab
from app.views.productos.tabs.edicion_tab import render as edicion_tab
from app.views.productos.data.getters import get_productos_data
from app.db import DatabaseAccess
from app.components.success_modal import show_success_modal
from src.core.logging import log_success, log_error

TAB_CATALOGO = 0
TAB_NUEVO = 1
TAB_EDICION = 2

NOMBRE_POR_DEFECTO = "este producto"

NAVEGACION = (
    (TAB_CATALOGO, "📋 Catálogo", "btn_catalogo_main"),
    (TAB_NUEVO, "➕ Nuevo", "btn_nuevo_main"),
    (TAB_EDICION, "✏️ Edición", "btn_edicion_main"),
)


def _eliminar_producto(pid, nombre):
    """Elimina el producto y notifica el resultado. Devuelve True si se elimino."""
    db = DatabaseAccess()
    try:
        if db.eliminar_producto(pid):
            get_productos_data.clear()
            show_success_modal("¡Producto eliminado!", f"{nombre} ha sido eliminado", duracion=2)
            log_success(f"Producto eliminado: {nombre}")
            return True
        st.error("❌ Error al eliminar el producto")
        log_error("productos", f"Error al eliminar producto {pid}")
    finally:
        db.close()
    return False


def _render_confirmacion_eliminar(pid_eliminar):
    """Muestra el dialogo de confirmacion de borrado. True si se debe salir de la vista."""
    productos, _, _, _ = get_productos_data()
    prod_eliminar = next((p for p in productos if p.get("id") == pid_eliminar), None)
    nombre_eliminar = prod_eliminar.get("nombre", NOMBRE_POR_DEFECTO) if prod_eliminar else NOMBRE_POR_DEFECTO

    st.warning(f"⚠️ ¿Eliminar **{nombre_eliminar}**? Esta acción no se puede deshacer.")
    col_si, col_no = st.columns(2)

    with col_si:
        if st.button("✅ Sí, eliminar", type="primary", width="stretch"):
            if _eliminar_producto(pid_eliminar, nombre_eliminar):
                del st.session_state['producto_eliminar']
                st.rerun()

    with col_no:
        if st.button("❌ Cancelar", width="stretch"):
            del st.session_state['producto_eliminar']
            st.rerun()

    return True


def _render_navegacion(tab_actual):
    """Renderiza la barra de navegacion entre tabs."""
    columnas = st.columns(len(NAVEGACION))
    for col, (indice, etiqueta, key) in zip(columnas, NAVEGACION):
        with col:
            btn = st.button(
                etiqueta,
                width="stretch",
                type="primary" if tab_actual == indice else "secondary",
                key=key,
            )
            if btn and tab_actual != indice:
                st.session_state['producto_tab_activo'] = indice
                st.rerun()


def _render_contenido_tab(tab_actual):
    """Renderiza el contenido del tab activo."""
    if tab_actual == TAB_CATALOGO:
        catalogo_tab()
    elif tab_actual == TAB_NUEVO:
        nuevo_tab()
    else:
        edicion_tab()


def render():
    """Renderiza la página de productos."""
    st.markdown("<h2>📦 Gestión de Productos</h2>", unsafe_allow_html=True)

    if st.session_state.get('producto_eliminar'):
        _render_confirmacion_eliminar(st.session_state['producto_eliminar'])
        return

    if 'producto_tab_activo' not in st.session_state:
        st.session_state['producto_tab_activo'] = TAB_CATALOGO

    tab_actual = st.session_state['producto_tab_activo']

    _render_navegacion(tab_actual)

    st.session_state['_tab_previo_productos'] = tab_actual

    st.markdown("---")

    with st.empty().container():
        _render_contenido_tab(tab_actual)