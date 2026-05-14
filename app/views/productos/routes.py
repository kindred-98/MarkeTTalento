"""Productos routes - Navegación principal"""
import streamlit as st
from app.views.productos.data.getters import get_productos_data, export_to_json, export_to_excel
from app.views.productos.tabs.catalogo_tab import render as catalogo_tab
from app.views.productos.tabs.nuevo_tab import render as nuevo_tab
from app.views.productos.tabs.edicion_tab import render as edicion_tab
from app.db import DatabaseAccess
from app.components.success_modal import show_success_modal
from app.views.productos.data.getters import get_productos_data as clear_cache


def render():
    """Renderiza la página de productos."""
    st.markdown("<h2>📦 Gestión de Productos</h2>", unsafe_allow_html=True)

    if st.session_state.get('_cerrar_modal_edicion'):
        del st.session_state['_cerrar_modal_edicion']
        st.rerun()
    
    if st.session_state.get('_cerrar_modal_eliminar'):
        del st.session_state['_cerrar_modal_eliminar']
        st.rerun()

    if 'producto_eliminar' in st.session_state and st.session_state['producto_eliminar']:
        pid_eliminar = st.session_state['producto_eliminar']
        productos, _, _, _ = get_productos_data()
        prod_eliminar = next((p for p in productos if p.get("id") == pid_eliminar), None)
        nombre_eliminar = prod_eliminar.get("nombre", "este producto") if prod_eliminar else "este producto"

        st.warning(f"⚠️ ¿Eliminar **{nombre_eliminar}**? Esta acción no se puede deshacer.")
        col_si, col_no = st.columns(2)
        with col_si:
            if st.button("✅ Sí, eliminar", type="primary", width="stretch"):
                resultado = api_delete(f"/api/v1/productos/{pid_eliminar}", authenticated=False)
                if resultado:
                    get_productos_data.clear()
                    show_success_modal("¡Producto eliminado!", f"{nombre_eliminar} ha sido eliminado", duracion=2)
                    del st.session_state['producto_eliminar']
                    st.rerun()
                else:
                    st.error("❌ Error al eliminar el producto")
        with col_no:
            if st.button("❌ Cancelar", width="stretch"):
                del st.session_state['producto_eliminar']
                st.rerun()
        return

    if 'producto_tab_activo' not in st.session_state:
        st.session_state['producto_tab_activo'] = 0

    col_nav1, col_nav2, col_nav3 = st.columns(3)

    tab_previo = st.session_state.get('_tab_previo_productos', 0)
    tab_actual = st.session_state['producto_tab_activo']

    with col_nav1:
        btn_catalogo = st.button(
            "📋 Catálogo",
            width="stretch",
            type="primary" if tab_actual == 0 else "secondary",
            key="btn_catalogo_main"
        )
        if btn_catalogo and tab_actual != 0:
            st.session_state['producto_tab_activo'] = 0
            st.rerun()

    with col_nav2:
        btn_nuevo = st.button(
            "➕ Nuevo",
            width="stretch",
            type="primary" if tab_actual == 1 else "secondary",
            key="btn_nuevo_main"
        )
        if btn_nuevo and tab_actual != 1:
            st.session_state['producto_tab_activo'] = 1
            st.rerun()

    with col_nav3:
        btn_edicion = st.button(
            "✏️ Edición",
            width="stretch",
            type="primary" if tab_actual == 2 else "secondary",
            key="btn_edicion_main"
        )
        if btn_edicion and tab_actual != 2:
            st.session_state['producto_tab_activo'] = 2
            st.rerun()

    st.session_state['_tab_previo_productos'] = tab_actual

    st.markdown("---")

    productos_exp, inventarios_exp, categorias_exp, proveedores_exp = get_productos_data()
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        st.download_button(
            label="📥 Exportar JSON",
            data=export_to_json(productos_exp, inventarios_exp, categorias_exp, proveedores_exp),
            file_name="productos.json",
            mime="application/octet-stream",
            width="stretch",
            type="secondary"
        )
    with col_exp2:
        st.download_button(
            label="📊 Exportar Excel",
            data=export_to_excel(productos_exp, inventarios_exp, categorias_exp, proveedores_exp),
            file_name="productos.xlsx",
            mime="application/octet-stream",
            width="stretch",
            type="secondary"
        )

    st.markdown("---")

    content_placeholder = st.empty()

    if tab_actual == 0:
        with content_placeholder.container():
            catalogo_tab()
    elif tab_actual == 1:
        with content_placeholder.container():
            nuevo_tab()
    else:
        with content_placeholder.container():
            edicion_tab()