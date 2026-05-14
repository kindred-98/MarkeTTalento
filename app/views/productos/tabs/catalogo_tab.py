"""Catálogo de productos tab"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data
from app.views.productos.utils.helpers import get_estado_producto
from app.logic.producto import get_categoria_emoji
from app.utils.helpers import calcular_porcentaje
from app.views.productos.components.producto_modal import ver_producto_modal


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
    height: 75px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
    transition: transform 0.3s ease;
}
.product-img-container img {
    max-height: 65px !important;
    max-width: 90% !important;
    object-fit: contain;
    border-radius: 6px;
}
.product-name-dark {
    font-size: 12px;
    font-weight: 600;
    color: #f1f5f9;
    margin: 0 0 2px 0;
    line-height: 1.3;
}
.product-category-dark {
    font-size: 9px;
    color: #06b6d4;
    margin: 0 0 6px 0;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    font-weight: 500;
}
.product-price-dark {
    font-size: 15px;
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
    padding: 8px 10px 4px 10px;
    text-align: center;
    background: linear-gradient(180deg, rgba(6, 182, 212, 0.08) 0%, rgba(139, 92, 246, 0.05) 100%);
    border-radius: 12px 12px 0 0;
}
.product-card-img-block .stButton button {
    margin-top: 4px;
    font-size: 11px !important;
    padding: 4px 8px !important;
}
@media (max-width: 1400px) {
    .product-card-dark { margin-bottom: 10px; }
}
@media (max-width: 992px) {
    .product-card-dark { margin-bottom: 8px; }
    .product-img-container { height: 70px; }
    .product-name-dark { font-size: 11px; }
}
@media (max-width: 768px) {
    .product-card-dark { margin-bottom: 6px; }
    .product-img-container { height: 60px; }
    .product-name-dark { font-size: 10px; }
    .product-price-dark { font-size: 12px; }
}
</style>
"""


def render():
    """Renderiza el catálogo de productos."""
    loading = st.empty()
    with loading:
        st.spinner("Cargando catálogo...")

    productos, inventarios, categorias, _ = get_productos_data()

    loading.empty()

    st.markdown("<h3 style='color: #3b82f6;'>🏪 Catálogo de Productos</h3>", unsafe_allow_html=True)

    col_busq1, col_busq2, col_busq3 = st.columns([2, 1, 1])

    with col_busq1:
        busqueda = st.text_input("🔍 Buscar", placeholder="Nombre o SKU...", key="cat_busqueda")

    with col_busq2:
        cat_options = ["Todas"] + [c.get("nombre", "Sin categoría") for c in categorias]
        cat_filtro = st.selectbox("Categoría", cat_options, key="cat_categoria")

    with col_busq3:
        estado_options = ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"]
        estado_filtro = st.selectbox("Estado", estado_options, key="cat_estado")

    productos_filtrados = productos

    if busqueda:
        busq_lower = busqueda.lower()
        productos_filtrados = [p for p in productos_filtrados
                              if busq_lower in p.get("nombre", "").lower()
                              or busq_lower in p.get("sku", "").lower()]

    if cat_filtro != "Todas":
        cat_id = next((c.get("id") for c in categorias if c.get("nombre") == cat_filtro), None)
        productos_filtrados = [p for p in productos_filtrados if p.get("categoria_id") == cat_id]

    if estado_filtro != "Todos":
        productos_filtrados = [p for p in productos_filtrados
                              if get_estado_producto(p.get("id"), inventarios, productos) == estado_filtro]

    st.markdown(f"<span style='color: #3b82f6; font-weight: 600;'>{len(productos_filtrados)}</span> <span style='color: #94a3b8;'>productos encontrados</span>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown(CSS_CATALOGO, unsafe_allow_html=True)

    if productos_filtrados:
        productos_por_pagina = 12
        if 'cat_pagina' not in st.session_state:
            st.session_state['cat_pagina'] = 1

        total_paginas = max(1, (len(productos_filtrados) + productos_por_pagina - 1) // productos_por_pagina)
        pagina_actual = min(st.session_state['cat_pagina'], total_paginas)

        inicio = (pagina_actual - 1) * productos_por_pagina
        fin = min(inicio + productos_por_pagina, len(productos_filtrados))
        productos_pagina = productos_filtrados[inicio:fin]

        cols_config = {"desktop": 6, "tablet": 4, "mobile": 2}

        rows = [productos_pagina[i:i+cols_config["desktop"]] for i in range(0, len(productos_pagina), cols_config["desktop"])]

        st.markdown("""
        <style>
        @media (max-width: 1200px) {
            div[data-testid="stHorizontalBlock"] > div > div > .product-card-dark { min-width: calc(25% - 10px); }
        }
        @media (max-width: 768px) {
            div[data-testid="stHorizontalBlock"] > div > div > .product-card-dark { min-width: calc(50% - 8px); }
        }
        </style>
        """, unsafe_allow_html=True)

        for row in rows:
            cols = st.columns(6)
            for idx, prod in enumerate(row):
                pid = prod.get("id")
                inv = next((i for i in inventarios if i.get("producto_id") == pid), None)
                stock = inv.get("cantidad", 0) if inv else 0
                max_s = prod.get("stock_maximo", 100) or 100
                estado = get_estado_producto(pid, inventarios, productos_filtrados)

                cat_nombre = next((c.get("nombre") for c in categorias if c.get("id") == prod.get("categoria_id")), "General")

                color_estado = {"Agotado": "#6b7280", "Crítico": "#ef4444", "Bajo": "#f59e0b", "Saludable": "#10b981"}.get(estado, "#10b981")

                img_url = prod.get("imagen_url")
                tiene_img = img_url and os.path.exists(img_url)

                descripcion = prod.get("descripcion", "") or f"{prod.get('unidad', 'unidad')} • {cat_nombre}"

                with cols[idx]:
                    st.markdown("<div class='product-card-dark'>", unsafe_allow_html=True)
                    st.markdown("<div class='product-card-img-block'>", unsafe_allow_html=True)

                    if tiene_img:
                        try:
                            st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
                            st.image(img_url, width=80)
                            st.markdown("</div>", unsafe_allow_html=True)
                        except Exception:
                            st.markdown(
                                f"<div style='width:100%;height:70px;background:linear-gradient(135deg, rgba(6,182,212,0.2), rgba(139,92,246,0.15));display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:2rem;'>{get_categoria_emoji(cat_nombre)}</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            f"<div style='width:100%;height:70px;background:linear-gradient(135deg, rgba(6,182,212,0.2), rgba(139,92,246,0.15));display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:2rem;'>{get_categoria_emoji(cat_nombre)}</div>",
                            unsafe_allow_html=True,
                        )

                    if st.button(
                        "Abrir ficha",
                        key=f"open_card_{pid}",
                        width="stretch",
                        type="tertiary",
                        help="Ver detalle, modificar o eliminar",
                    ):
                        ver_producto_modal(pid)

                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("<div style='padding:6px 10px;'>", unsafe_allow_html=True)
                    st.markdown(f"<p class='product-name-dark'>{prod.get('nombre', 'Producto')}</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='product-category-dark'>🏷️ {cat_nombre}</p>", unsafe_allow_html=True)

                    stock_pct = calcular_porcentaje(stock, max_s)
                    color_barra = "#ef4444" if stock_pct <= 20 else "#f59e0b" if stock_pct <= 50 else "#10b981"

                    st.markdown(f"""
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <span class='product-price-dark'>€{prod.get('precio_venta', 0):.2f} <span style='font-size:10px;color:#94a3b8;font-weight:400;'>€/ud</span></span>
                        <span class='product-badge-dark' style='background:{color_estado};'>{estado}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    stock_txt = f"{stock} {prod.get('unidad', 'uds')}"

                    st.markdown(f"""
                    <div style="background:rgba(0,0,0,0.2);padding:6px 8px;border-radius:6px;margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
                            <span style="font-size:10px;color:#e2e8f0;font-weight:600;">📦 {stock_txt}</span>
                            <span style="font-size:10px;color:{color_barra};font-weight:600;">{stock_pct:.0f}%</span>
                        </div>
                        <div style="width:100%;height:5px;background:rgba(255,255,255,0.1);border-radius:3px;overflow:hidden;">
                            <div style="width:{stock_pct}%;height:100%;background:{color_barra};border-radius:3px;"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("</div></div>", unsafe_allow_html=True)

        if total_paginas > 1:
            col_pag1, col_pag2, col_pag3 = st.columns([1, 7.7, 1])
            with col_pag1:
                if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, key="btn_pag_ant"):
                    st.session_state['cat_pagina'] = pagina_actual - 1
                    st.rerun()
            with col_pag2:
                st.markdown(f"<p style='text-align: center; color: #94a3b8;'>Página {pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
            with col_pag3:
                if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, key="btn_pag_sig"):
                    st.session_state['cat_pagina'] = pagina_actual + 1
                    st.rerun()

    else:
        st.info("No hay productos en el catálogo")