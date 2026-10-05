"""Catálogo de productos tab"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data, export_to_json, export_to_excel
from app.views.productos.utils.helpers import get_estado_producto, color_barra_stock, STOCK_MAX_POR_DEFECTO
from app.logic.producto import get_categoria_emoji
from app.logic.inventario import get_color_estado
from app.utils.helpers import calcular_porcentaje
from app.views.productos.components.producto_modal import ver_producto_modal

PRODUCTOS_POR_PAGINA = 12
PRODUCTOS_POR_FILA = 6
CATEGORIA_POR_DEFECTO = "General"
CATEGORIA_SIN_NOMBRE = "Sin categoría"
LONGITUD_DESCRIPCION = 80
FILTRO_TODAS = "Todas"
FILTRO_TODOS = "Todos"
ESTADOS_FILTRABLES = ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"]

CSS_CATALOGO = """
<style>
.product-card-dark {
    background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid rgba(6, 182, 212, 0.25);
    border-radius: 12px;
    padding: 0;
    margin-bottom: 12px;
    transition: all 0.3s ease;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.product-card-dark:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 25px rgba(6, 182, 212, 0.25), 0 4px 12px rgba(139, 92, 246, 0.15);
    border-color: rgba(6, 182, 212, 0.5);
}
.product-card-dark:hover .product-img-container {
    transform: scale(1.05);
}
.product-img-container {
    width: 100%;
    height: 160px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
    transition: transform 0.3s ease;
}
.product-img-container img {
    max-height: 150px !important;
    max-width: 95% !important;
    object-fit: contain;
    border-radius: 6px;
}
.product-name-dark {
    font-size: 11px;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0 0 1px 0;
    line-height: 1.2;
}
.product-category-dark {
    font-size: 8px;
    color: #06b6d4;
    margin: 0 0 3px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
}
.product-price-dark {
    font-size: 13px;
    font-weight: 700;
    color: #06b6d4;
}
.product-badge-dark {
    font-size: 10px;
    padding: 3px 8px;
    border-radius: 10px;
    color: white;
    font-weight: 600;
}
.product-card-img-block {
    padding: 0px !important;
    margin: 0px !important;
    text-align: center;
    background: linear-gradient(180deg, rgba(6, 182, 212, 0.08) 0%, rgba(139, 92, 246, 0.05) 100%);
    border-radius: 12px 12px 0 0;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 0px !important;
}
.product-card-img-block > * {
    margin: 0 !important;
    padding: 0 !important;
}
.product-card-img-block .stImage {
    margin: 0 !important;
    padding: 0 !important;
}
.product-card-img-block .stImage img {
    display: block !important;
    margin: 0 !important;
}
.product-card-img-block .stButton {
    margin: 0 !important;
    padding: 0 !important;
    width: 100% !important;
}
.product-card-img-block .stButton button {
    margin: 0 !important;
    padding: 0px 8px !important;
    font-size: 9px !important;
    line-height: 1 !important;
    min-height: auto !important;
    height: auto !important;
}
@media (max-width: 1400px) {
    .product-card-dark { margin-bottom: 8px; }
    .product-img-container { height: 150px; }
}
@media (max-width: 992px) {
    .product-card-dark { margin-bottom: 6px; }
    .product-img-container { height: 140px; }
    .product-img-container img { max-height: 130px !important; }
    .product-name-dark { font-size: 10px; }
}
@media (max-width: 768px) {
    .product-card-dark { margin-bottom: 5px; }
    .product-img-container { height: 120px; }
    .product-img-container img { max-height: 110px !important; }
    .product-name-dark { font-size: 9px; }
    .product-price-dark { font-size: 11px; }
}
</style>
"""


CSS_IMAGEN_FALLBACK = (
    "<div style='width:100%;height:150px;background:linear-gradient(135deg, rgba(6,182,212,0.2), "
    "rgba(139,92,246,0.15));display:flex;align-items:center;justify-content:center;"
    "border-radius:6px;font-size:4rem;'>{}</div>"
)

CSS_CARD = "<div class='product-card-dark'>"
CSS_IMG_BLOCK = "<div class='product-card-img-block' style='display:flex;flex-direction:column;align-items:center;gap:0;'>"
DIV_CLOSE = "</div>"
DIV_CLOSE_2 = "</div></div>"


def _nombre_categoria(categorias, categoria_id):
    """Devuelve el nombre de la categoria del producto."""
    return next((c.get("nombre") for c in categorias if c.get("id") == categoria_id), CATEGORIA_POR_DEFECTO)


def _descripcion_truncada(desc):
    """Recorta la descripcion al limite de la tarjeta."""
    return f"{desc[:LONGITUD_DESCRIPCION]}..." if len(desc) > LONGITUD_DESCRIPCION else desc


def _render_bloque_imagen(prod, cat_nombre):
    """Muestra la imagen del producto o el emoji de su categoria."""
    img_url = prod.get("imagen_url")
    if img_url and os.path.exists(img_url):
        try:
            st.image(img_url, width=300, use_container_width=False)
            return
        except Exception:
            pass
    st.markdown(CSS_IMAGEN_FALLBACK.format(get_categoria_emoji(cat_nombre)), unsafe_allow_html=True)


def _render_boton_ficha(pid):
    """Muestra el boton que abre la ficha del producto."""
    if st.button(
        "Abrir ficha",
        key=f"open_card_{pid}",
        width="stretch",
        type="tertiary",
        help="Ver detalle, modificar o eliminar",
    ):
        if not st.session_state.get('_modal_cerrar'):
            ver_producto_modal(pid)
        else:
            st.session_state['_modal_cerrar'] = False


def _render_barra_stock(stock, unidad, stock_pct, color_barra):
    """Muestra la barra de progreso del stock de la tarjeta."""
    st.markdown(f"""
    <div style="background:rgba(0,0,0,0.2);padding:4px 6px;border-radius:4px;margin-bottom:4px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
            <span style="font-size:9px;color:#e2e8f0;font-weight:600;">📦 {stock} {unidad}</span>
            <span style="font-size:13px;color:{color_barra};font-weight:700;">{stock_pct:.0f}%</span>
        </div>
        <div style="width:100%;height:8px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden;">
            <div style="width:{stock_pct}%;height:100%;background:{color_barra};border-radius:4px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def _render_precio_y_estado(prod, estado, color_estado):
    """Muestra el precio y el badge de estado del producto."""
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
        <span class='product-price-dark'>€{prod.get('precio_venta', 0):.2f} <span style='font-size:9px;color:#94a3b8;font-weight:400;'>€/ud</span></span>
        <span class='product-badge-dark' style='background:{color_estado};'>{estado}</span>
    </div>
    """, unsafe_allow_html=True)


def _render_tarjeta_producto(prod, inventarios, productos, categorias):
    """Renderiza la tarjeta completa de un producto del catalogo."""
    pid = prod.get("id")
    inv = next((i for i in inventarios if i.get("producto_id") == pid), None)
    stock = inv.get("cantidad", 0) if inv else 0
    max_s = prod.get("stock_maximo", STOCK_MAX_POR_DEFECTO) or STOCK_MAX_POR_DEFECTO
    estado = get_estado_producto(pid, inventarios, productos)
    cat_nombre = _nombre_categoria(categorias, prod.get("categoria_id"))

    st.markdown(CSS_CARD, unsafe_allow_html=True)
    st.markdown(CSS_IMG_BLOCK, unsafe_allow_html=True)
    _render_bloque_imagen(prod, cat_nombre)
    _render_boton_ficha(pid)
    st.markdown(DIV_CLOSE, unsafe_allow_html=True)
    st.markdown("<div style='padding:2px 8px;'>", unsafe_allow_html=True)
    st.markdown(f"<p class='product-name-dark'>{prod.get('nombre', 'Producto')}</p>", unsafe_allow_html=True)
    st.markdown(f"<p class='product-category-dark'>🏷️ {cat_nombre}</p>", unsafe_allow_html=True)

    desc = prod.get('descripcion', '') or ''
    if desc:
        st.markdown(f"<p style='font-size:9px;color:#94a3b8;margin:0 0 4px 0;line-height:1.3;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;'>{_descripcion_truncada(desc)}</p>", unsafe_allow_html=True)

    _render_precio_y_estado(prod, estado, get_color_estado(estado))

    stock_pct = calcular_porcentaje(stock, max_s)
    _render_barra_stock(stock, prod.get('unidad', 'uds'), stock_pct, color_barra_stock(stock_pct))
    st.markdown(DIV_CLOSE_2, unsafe_allow_html=True)


def _render_exportaciones(productos, inventarios, categorias, proveedores):
    """Muestra los botones de exportacion a JSON y Excel."""
    col_json, col_excel = st.columns(2)

    with col_json:
        st.download_button(
            label="📥 Exportar JSON",
            data=export_to_json(productos, inventarios, categorias, proveedores),
            file_name="productos.json",
            mime="application/octet-stream",
            width="stretch",
            type="secondary"
        )
    with col_excel:
        st.download_button(
            label="📊 Exportar Excel",
            data=export_to_excel(productos, inventarios, categorias, proveedores),
            file_name="productos.xlsx",
            mime="application/octet-stream",
            width="stretch",
            type="secondary"
        )


def _render_filtros(categorias):
    """Renderiza busqueda, filtro de categoria y filtro de estado."""
    col_busq, col_cat, col_estado = st.columns([2, 1, 1])

    with col_busq:
        busqueda = st.text_input("🔍 Buscar", placeholder="Nombre o SKU...", key="cat_busqueda")
    with col_cat:
        cat_options = [FILTRO_TODAS] + [c.get("nombre", CATEGORIA_SIN_NOMBRE) for c in categorias]
        cat_filtro = st.selectbox("Categoría", cat_options, key="cat_categoria")
    with col_estado:
        estado_filtro = st.selectbox("Estado", ESTADOS_FILTRABLES, key="cat_estado")

    return busqueda, cat_filtro, estado_filtro


def _filtrar_por_busqueda(productos, busqueda):
    """Filtra por nombre o SKU."""
    if not busqueda:
        return productos
    busq_lower = busqueda.lower()
    return [p for p in productos
            if busq_lower in p.get("nombre", "").lower() or busq_lower in p.get("sku", "").lower()]


def _filtrar_por_categoria(productos, categorias, cat_filtro):
    """Filtra por id de categoria resuelto a partir de su nombre."""
    if cat_filtro == FILTRO_TODAS:
        return productos
    cat_id = next((c.get("id") for c in categorias if c.get("nombre") == cat_filtro), None)
    return [p for p in productos if p.get("categoria_id") == cat_id]


def _filtrar_por_estado(productos, inventarios, estado_filtro):
    """Filtra por estado de stock calculado."""
    if estado_filtro == FILTRO_TODOS:
        return productos
    return [p for p in productos
            if get_estado_producto(p.get("id"), inventarios, productos) == estado_filtro]


def _paginar(productos_filtrados):
    """Devuelve (productos_pagina, pagina_actual, total_paginas)."""
    if 'cat_pagina' not in st.session_state:
        st.session_state['cat_pagina'] = 1

    total_paginas = max(1, (len(productos_filtrados) + PRODUCTOS_POR_PAGINA - 1) // PRODUCTOS_POR_PAGINA)
    pagina_actual = min(st.session_state['cat_pagina'], total_paginas)
    inicio = (pagina_actual - 1) * PRODUCTOS_POR_PAGINA
    fin = min(inicio + PRODUCTOS_POR_PAGINA, len(productos_filtrados))

    return productos_filtrados[inicio:fin], pagina_actual, total_paginas


def _render_paginacion(pagina_actual, total_paginas):
    """Muestra los controles de paginacion."""
    if total_paginas <= 1:
        return

    col_ant, col_info, col_sig = st.columns([1, 7.7, 1])
    with col_ant:
        if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, key="btn_pag_ant"):
            st.session_state['cat_pagina'] = pagina_actual - 1
            st.rerun()
    with col_info:
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>Página {pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
    with col_sig:
        if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, key="btn_pag_sig"):
            st.session_state['cat_pagina'] = pagina_actual + 1
            st.rerun()


CSS_REJILLA = """
<style>
@media (max-width: 1200px) {
    div[data-testid="stHorizontalBlock"] > div > div > .product-card-dark { min-width: calc(25% - 10px); }
}
@media (max-width: 768px) {
    div[data-testid="stHorizontalBlock"] > div > div > .product-card-dark { min-width: calc(50% - 8px); }
}
</style>
"""


def _render_rejilla(productos_pagina, inventarios, productos, categorias):
    """Renderiza la rejilla de tarjetas del catalogo."""
    st.markdown(CSS_REJILLA, unsafe_allow_html=True)

    for inicio in range(0, len(productos_pagina), PRODUCTOS_POR_FILA):
        cols = st.columns(PRODUCTOS_POR_FILA)
        for col, prod in zip(cols, productos_pagina[inicio:inicio + PRODUCTOS_POR_FILA]):
            with col:
                _render_tarjeta_producto(prod, inventarios, productos, categorias)


def render():
    """Renderiza el catálogo de productos."""
    loading = st.empty()
    with loading:
        st.spinner("Cargando catálogo...")

    productos, inventarios, categorias, proveedores = get_productos_data()

    loading.empty()

    st.markdown("<h3 style='color: #3b82f6;'>🏪 Catálogo de Productos</h3>", unsafe_allow_html=True)

    _render_exportaciones(productos, inventarios, categorias, proveedores)

    st.markdown("---")

    busqueda, cat_filtro, estado_filtro = _render_filtros(categorias)

    productos_filtrados = _filtrar_por_busqueda(productos, busqueda)
    productos_filtrados = _filtrar_por_categoria(productos_filtrados, categorias, cat_filtro)
    productos_filtrados = _filtrar_por_estado(productos_filtrados, inventarios, estado_filtro)

    st.markdown(f"<span style='color: #3b82f6; font-weight: 600;'>{len(productos_filtrados)}</span> <span style='color: #94a3b8;'>productos encontrados</span>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(CSS_CATALOGO, unsafe_allow_html=True)

    if not productos_filtrados:
        st.info("No hay productos en el catálogo")
        return

    productos_pagina, pagina_actual, total_paginas = _paginar(productos_filtrados)

    _render_rejilla(productos_pagina, inventarios, productos, categorias)
    _render_paginacion(pagina_actual, total_paginas)
