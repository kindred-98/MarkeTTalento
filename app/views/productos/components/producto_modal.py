"""Producto modal component"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data
from app.views.productos.utils.helpers import get_estado_producto, color_barra_stock
from app.logic.producto import get_categoria_emoji
from app.logic.inventario import get_color_estado
from app.utils.helpers import calcular_porcentaje

CATEGORIA_POR_DEFECTO = "General"
SIN_PROVEEDOR = "Sin proveedor"
STOCK_MAX_POR_DEFECTO = 100
LONGITUD_DESCRIPCION = 60


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


def _nombre_por_id(coleccion, id_buscado, por_defecto):
    """Devuelve el campo 'nombre' del elemento cuyo id coincide, o el valor por defecto."""
    return next((c.get("nombre") for c in coleccion if c.get("id") == id_buscado), por_defecto)


def _resumen_descripcion(desc):
    """Recorta la descripcion al limite del modal."""
    desc = desc or "Descripción"
    return f"{desc[:LONGITUD_DESCRIPCION]}..." if len(desc) > LONGITUD_DESCRIPCION else desc


def _render_imagen(prod, cat_nombre):
    """Muestra la imagen del producto o el emoji de su categoria."""
    img_url = prod.get("imagen_url")
    if img_url and os.path.exists(img_url):
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image(img_url, width=100)
        st.markdown("</div>", unsafe_allow_html=True)
        return
    st.markdown(f"<div style='width:100%;height:100px;background:linear-gradient(135deg, rgba(6,182,212,0.2), rgba(139,92,246,0.15));display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:2.5rem;'>{get_categoria_emoji(cat_nombre)}</div>", unsafe_allow_html=True)


def _render_barra_stock(stock, unidad, pct, color_barra):
    """Muestra la barra de progreso del stock."""
    st.markdown(f"""
    <div style="background:rgba(0,0,0,0.3);padding:8px;border-radius:6px;">
        <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
            <span style="color:#e2e8f0;font-size:11px;font-weight:600;">📦 {stock} {unidad}</span>
            <span style="color:{color_barra};font-size:11px;font-weight:600;">{pct:.0f}%</span>
        </div>
        <div style="width:100%;height:6px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">
            <div style="width:{pct}%;height:100%;background:{color_barra};border-radius:3px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_rejilla_metricas(metricas, columnas):
    """Renderiza las metricas en filas de 'columnas' columnas."""
    for inicio in range(0, len(metricas), columnas):
        for col, (label, valor) in zip(st.columns(columnas), metricas[inicio:inicio + columnas]):
            with col:
                st.markdown(
                    f"<div class='modal-metric'><p class='modal-metric-label'>{label}</p>"
                    f"<p class='modal-metric-value'>{valor}</p></div>",
                    unsafe_allow_html=True,
                )


def _metricas_producto(prod, prov_nombre):
    """Devuelve las metricas del producto agrupadas por fila."""
    return [
        [
            ("SKU", prod.get('sku', 'N/A')),
            ("Unidad", prod.get('unidad', 'N/A')),
            ("Proveedor", prov_nombre),
            ("Stock máx", prod.get('stock_maximo', 0)),
        ],
        [
            ("Precio coste", f"€{prod.get('precio_coste') or 0:.2f}"),
            ("Días reposición", f"{prod.get('tiempo_reposicion', 3)} días"),
            ("Código barras", prod.get('codigo_barras') or 'N/A'),
        ],
    ]


def _render_acciones(pid):
    """Renderiza los botones de modificar y eliminar."""
    col_modificar, col_eliminar = st.columns(2)

    with col_modificar:
        if st.button("Modificar", key=f"modal_edit_{pid}", width="stretch", type="primary"):
            st.session_state['editar_producto'] = pid
            st.session_state['producto_tab_activo'] = 2
            st.session_state['_modal_cerrar'] = True
            st.rerun()

    with col_eliminar:
        if st.button("Eliminar", key=f"modal_del_{pid}", width="stretch"):
            st.session_state["producto_eliminar"] = pid
            st.session_state['_modal_cerrar'] = True
            st.rerun()


@st.dialog("Detalle del Producto", width="small")
def ver_producto_modal(pid):
    """Muestra el modal de detalle del producto."""
    if st.session_state.get('_modal_cerrar'):
        st.session_state['_modal_cerrar'] = False
        return

    productos, inventarios, categorias, proveedores = get_productos_data()
    prod = next((p for p in productos if p.get("id") == pid), None)
    if not prod:
        st.error("Producto no encontrado")
        return

    inv = next((i for i in inventarios if i.get("producto_id") == pid), None)
    stock = inv.get("cantidad", 0) if inv else 0
    max_s = prod.get("stock_maximo", STOCK_MAX_POR_DEFECTO) or STOCK_MAX_POR_DEFECTO
    estado = get_estado_producto(pid, inventarios, productos)
    cat_nombre = _nombre_por_id(categorias, prod.get("categoria_id"), CATEGORIA_POR_DEFECTO)
    prov_nombre = _nombre_por_id(proveedores, prod.get("proveedor_id"), SIN_PROVEEDOR)
    color_estado = get_color_estado(estado)
    pct = calcular_porcentaje(stock, max_s)
    color_barra = color_barra_stock(pct)

    col_img, col_info = st.columns([1, 1])

    with col_img:
        _render_imagen(prod, cat_nombre)

    with col_info:
        st.markdown(f"<h3 style='color:#f8fafc;margin:0 0 2px 0;font-size:1rem;'>{prod.get('nombre', '')}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;font-size:11px;margin:0 0 4px 0;text-transform:uppercase;'>🏷️ {cat_nombre}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#cbd5e1;font-size:12px;margin:0 0 4px 0;'>{_resumen_descripcion(prod.get('descripcion', ''))}</p>", unsafe_allow_html=True)

        col_precio, col_estado = st.columns([2, 1])
        with col_precio:
            st.markdown(f"<div style='font-size:1.2rem;font-weight:700;color:#3b82f6;'>€{prod.get('precio_venta', 0):.2f} <span style='font-size:10px;color:#94a3b8;font-weight:400;'>€/ud</span></div>", unsafe_allow_html=True)
        with col_estado:
            st.markdown(f"<div style='text-align:right;padding-top:0px;'><span style='display:inline-block;padding:3px 8px;border-radius:8px;font-size:11px;font-weight:600;color:white;background:{color_estado};'>{estado}</span></div>", unsafe_allow_html=True)

        _render_barra_stock(stock, prod.get('unidad', 'uds'), pct, color_barra)

    st.markdown("---")
    st.markdown(CSS_MODAL, unsafe_allow_html=True)

    for fila in _metricas_producto(prod, prov_nombre):
        _render_rejilla_metricas(fila, 4)

    st.markdown("---")
    st.markdown("**Acciones**")
    _render_acciones(pid)