"""Producto modal component"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data
from app.views.productos.utils.helpers import get_estado_producto
from app.logic.producto import get_categoria_emoji
from app.utils.helpers import calcular_porcentaje
from app.utils.state import set_editar_producto


CSS_MODAL = """
<style>
.modal-metric {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 8px;
    transition: all 0.3s ease;
    cursor: pointer;
    margin-bottom: 6px;
}
.modal-metric:hover {
    transform: translateY(-2px);
    box-shadow: 0 0 15px rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.3);
    background: rgba(30, 41, 59, 0.7);
}
.modal-metric-label {
    font-size: 8px;
    color: #64748b;
    text-transform: uppercase;
    margin: 0 0 2px 0;
}
.modal-metric-value {
    font-size: 12px;
    font-weight: 600;
    color: #f8fafc;
    margin: 0;
}
</style>
"""


@st.dialog("Detalle del Producto", width="small")
def ver_producto_modal(pid):
    """Muestra el modal de detalle del producto."""
    productos, inventarios, categorias, proveedores = get_productos_data()
    prod = next((p for p in productos if p.get("id") == pid), None)
    if not prod:
        st.error("Producto no encontrado")
        return

    inv = next((i for i in inventarios if i.get("producto_id") == pid), None)
    stock = inv.get("cantidad", 0) if inv else 0
    max_s = prod.get("stock_maximo", 100) or 100
    estado = get_estado_producto(pid, inventarios, productos)
    cat_nombre = next((c.get("nombre") for c in categorias if c.get("id") == prod.get("categoria_id")), "General")
    prov_nombre = next((p.get("nombre") for p in proveedores if p.get("id") == prod.get("proveedor_id")), "Sin proveedor")
    color_estado = {"Agotado": "#6b7280", "Crítico": "#ef4444", "Bajo": "#f59e0b", "Saludable": "#10b981"}.get(estado, "#10b981")
    pct = calcular_porcentaje(stock, max_s)
    color_barra = "#ef4444" if pct <= 20 else "#f59e0b" if pct <= 50 else "#10b981"
    desc = prod.get("descripcion", "") or "Descripción"

    col_img, col_info = st.columns([1, 1])

    with col_img:
        img_url = prod.get("imagen_url")
        if img_url and os.path.exists(img_url):
            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
            st.image(img_url, width=100)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='width:100%;height:100px;background:linear-gradient(135deg, rgba(6,182,212,0.2), rgba(139,92,246,0.15));display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:2.5rem;'>{get_categoria_emoji(cat_nombre)}</div>", unsafe_allow_html=True)

    with col_info:
        st.markdown(f"<h3 style='color:#f8fafc;margin:0 0 2px 0;font-size:1rem;'>{prod.get('nombre', '')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;font-size:11px;margin:0 0 4px 0;text-transform:uppercase;'>🏷️ {cat_nombre}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#cbd5e1;font-size:12px;margin:0 0 4px 0;'>{desc[:60]}{'...' if len(desc) > 60 else ''}</p>", unsafe_allow_html=True)

        col_precio, col_estado = st.columns([2, 1])
        with col_precio:
            st.markdown(f"<div style='font-size:1.2rem;font-weight:700;color:#3b82f6;'>€{prod.get('precio_venta', 0):.2f} <span style='font-size:10px;color:#94a3b8;font-weight:400;'>€/ud</span></div>", unsafe_allow_html=True)
        with col_estado:
            st.markdown(f"<div style='text-align:right;padding-top:0px;'><span style='display:inline-block;padding:3px 8px;border-radius:8px;font-size:11px;font-weight:600;color:white;background:{color_estado};'>{estado}</span></div>", unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:6px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
                <span style="color:#e2e8f0;font-size:11px;font-weight:600;">📦 {stock} {prod.get('unidad', 'uds')}</span>
                <span style="color:{color_barra};font-size:11px;font-weight:600;">{pct:.0f}%</span>
            </div>
            <div style="width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">
                <div style="width:{pct}%;height:100%;background:{color_barra};border-radius:3px;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown(CSS_MODAL, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"<div class='modal-metric'><p class='modal-metric-label'>SKU</p><p class='modal-metric-value'>{prod.get('sku', 'N/A')}</p></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='modal-metric'><p class='modal-metric-label'>Unidad</p><p class='modal-metric-value'>{prod.get('unidad', 'N/A')}</p></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='modal-metric'><p class='modal-metric-label'>Proveedor</p><p class='modal-metric-value'>{prov_nombre}</p></div>", unsafe_allow_html=True)
    with col4:
        st.markdown(f"<div class='modal-metric'><p class='modal-metric-label'>Stock máx</p><p class='modal-metric-value'>{prod.get('stock_maximo', 0)}</p></div>", unsafe_allow_html=True)

    col5, col6, col7 = st.columns(3)
    with col5:
        st.markdown(f"<div class='modal-metric'><p class='modal-metric-label'>Precio coste</p><p class='modal-metric-value'>€{prod.get('precio_coste') or 0:.2f}</p></div>", unsafe_allow_html=True)
    with col6:
        st.markdown(f"<div class='modal-metric'><p class='modal-metric-label'>Días reposición</p><p class='modal-metric-value'>{prod.get('tiempo_reposicion', 3)} días</p></div>", unsafe_allow_html=True)
    with col7:
        st.markdown(f"<div class='modal-metric'><p class='modal-metric-label'>Código barras</p><p class='modal-metric-value'>{prod.get('codigo_barras') or 'N/A'}</p></div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("**Acciones**")
    a1, a2 = st.columns(2)
    with a1:
        if st.button("Modificar", key=f"modal_edit_{pid}", width="stretch", type="primary"):
            set_editar_producto(pid)
            st.session_state["producto_tab_activo"] = 2
            st.rerun()
    with a2:
        if st.button("Eliminar", key=f"modal_del_{pid}", width="stretch"):
            st.session_state["producto_eliminar"] = pid
            st.rerun()