"""
Pagina de Inspector de Producto
Escanea codigo de barras o SKU y muestra ficha completa, stock, prediccion ML e historial.
"""
import streamlit as st
from app.utils.api import api_get
import requests
from app.config import API_URL

CARD_HTML = "<div class='inspector-card'>"
DIV_CLOSE_HTML = "</div>"
SALTO_HTML = "<br/>"
IMAGEN_PLACEHOLDER_HTML = (
    "<div style='height:150px; display:flex; align-items:center; "
    "justify-content:center; color:#64748b; font-size:3rem;'>📦</div>"
)
STOCK_CRITICO = 2


def render():
    """Renderiza el Inspector de Producto."""
    st.markdown("""
    <style>
    .inspector-header {
        background: linear-gradient(90deg, #f59e0b, #ef4444);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .inspector-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 1.2rem;
        height: 100%;
    }
    .inspector-metric {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0ea5e9;
    }
    .inspector-label {
        font-size: 0.8rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-stock-ok { background: rgba(16,185,129,0.15); color: #10b981; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-stock-bajo { background: rgba(245,158,11,0.15); color: #f59e0b; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-stock-critico { background: rgba(239,68,68,0.15); color: #ef4444; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .historial-row {
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.05);
        font-size: 0.85rem;
    }
    </style>
    <div class="inspector-header">🔍 Inspector de Producto</div>
    <p style="color:#94a3b8; margin-top:0;">Escanee codigo de barras, SKU o nombre para ver ficha completa, stock, prediccion ML e historial de ventas.</p>
    """, unsafe_allow_html=True)

    # Barra de busqueda
    col1, col2 = st.columns([3, 1])
    with col1:
        busqueda = st.text_input("Codigo de barras, SKU o nombre", placeholder="Ej: 7622210449283 o CC330 o Coca-Cola", label_visibility="collapsed")
    with col2:
        tipo_busqueda = st.selectbox("Buscar por:", ["Codigo de barras", "SKU", "Nombre"], label_visibility="collapsed")

    if st.button("🔍 Buscar", type="primary", width="stretch"):
        with st.spinner("Buscando producto..."):
            producto = _buscar_producto(busqueda, tipo_busqueda)

        if producto:
            _mostrar_ficha_producto(producto)
        else:
            st.error("❌ Producto no encontrado")
            st.info("💡 Verifica el codigo o ve a la seccion **Productos** para crear uno nuevo.")


def _buscar_producto(texto, tipo):
    """Busca producto por codigo de barras, SKU o nombre."""
    texto = texto.strip()
    if not texto:
        return None

    try:
        if tipo == "Codigo de barras":
            r = requests.get(f"{API_URL}/api/v1/productos/barcode/{texto}", timeout=5)
        elif tipo == "SKU":
            r = requests.get(f"{API_URL}/api/v1/productos/sku/{texto}", timeout=5)
        else:  # Nombre
            productos = api_get("/api/v1/productos")
            for p in productos:
                if texto.lower() in p.get("nombre", "").lower():
                    return p
            return None

        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def _estado_stock(stock, stock_min):
    """Devuelve (clase_css, etiqueta) segun el nivel de stock."""
    if stock <= STOCK_CRITICO:
        return "badge-stock-critico", "CRITICO"
    if stock <= stock_min:
        return "badge-stock-bajo", "BAJO"
    return "badge-stock-ok", "OK"


def _nombre_categoria(producto):
    """Extrae el nombre de la categoria como texto."""
    cat = producto.get("categoria", {})
    return cat.get("nombre", "") if isinstance(cat, dict) else str(cat)


def _nombre_proveedor(producto):
    """Extrae el nombre del proveedor como texto."""
    prov = producto.get("proveedor")
    return prov.get("nombre", "N/A") if isinstance(prov, dict) else "N/A"


def _render_columna_foto(producto):
    """Muestra la foto del producto o un placeholder."""
    st.markdown(CARD_HTML, unsafe_allow_html=True)
    url = producto.get("imagen_url")
    if url:
        try:
            st.image(url, width="stretch")
        except Exception:
            st.markdown(IMAGEN_PLACEHOLDER_HTML, unsafe_allow_html=True)
    else:
        st.markdown(IMAGEN_PLACEHOLDER_HTML, unsafe_allow_html=True)
    st.markdown(DIV_CLOSE_HTML, unsafe_allow_html=True)


def _render_columna_ficha(producto, pid):
    """Muestra nombre, identificadores, precios y proveedor."""
    st.markdown(CARD_HTML, unsafe_allow_html=True)
    st.markdown(f"""
    <h3 style="margin:0 0 8px 0; color:#f1f5f9;">{producto.get('nombre', 'Producto')}</h3>
    <div style="color:#64748b; font-size:0.85rem; margin-bottom:12px;">
        <strong>SKU:</strong> {producto.get('sku', 'N/A')} &nbsp;|&nbsp;
        <strong>ID:</strong> {pid}
    </div>
    <div style="display:flex; gap:20px; margin-bottom:8px;">
        <div>
            <div class="inspector-label">Precio venta</div>
            <div class="inspector-metric" style="color:#10b981;">€{producto.get('precio_venta', 0):.2f}</div>
        </div>
        <div>
            <div class="inspector-label">Unidad</div>
            <div class="inspector-metric" style="color:#f59e0b; font-size:1.2rem;">{producto.get('unidad', 'ud')}</div>
        </div>
        <div>
            <div class="inspector-label">Stock min</div>
            <div class="inspector-metric" style="color:#94a3b8; font-size:1.2rem;">{producto.get('stock_minimo', 5)}</div>
        </div>
    </div>
    <div style="color:#64748b; font-size:0.8rem; margin-top:8px;">
        <strong>Proveedor:</strong> {_nombre_proveedor(producto)}
    </div>
    """, unsafe_allow_html=True)
    st.markdown(DIV_CLOSE_HTML, unsafe_allow_html=True)


def _render_columna_stock(producto, pid):
    """Muestra el stock actual, su estado y la ubicacion."""
    inv = _obtener_inventario(pid)
    stock = inv.get("cantidad", 0) if inv else 0
    ubicacion = inv.get("ubicacion", "—") if inv else "—"
    badge_class, estado = _estado_stock(stock, producto.get("stock_minimo", 5))

    st.markdown(CARD_HTML, unsafe_allow_html=True)
    st.markdown(f"""
    <div style="text-align:center; margin-bottom:12px;">
        <div class="inspector-label">Stock actual</div>
        <div class="inspector-metric" style="font-size:2.2rem; margin:4px 0;">{stock}</div>
        <span class="{badge_class}">{estado}</span>
    </div>
    <div style="text-align:center; color:#64748b; font-size:0.8rem; margin-top:8px;">
        <strong>Ubicacion:</strong>{SALTO_HTML}{ubicacion}
    </div>
    """, unsafe_allow_html=True)
    st.markdown(DIV_CLOSE_HTML, unsafe_allow_html=True)


def _metricas_prediccion(pred):
    """Devuelve las tuplas (label, value, color) de la prediccion ML."""
    return [
        ("Consumo promedio", f"{pred.get('consumo_promedio_diario', 0):.2f} uds/dia", "#0ea5e9"),
        ("Dias hasta agotarse", f"{pred.get('dias_hasta_agotarse', 0):.1f}", "#f59e0b"),
        ("Tendencia", pred.get("tendencia", "ESTABLE"), "#10b981"),
        ("Estado stock", pred.get("estado_stock", "ADECUADO"), "#8b5cf6"),
    ]


def _render_prediccion(pid):
    """Muestra las 4 metricas de la prediccion ML."""
    pred = _obtener_prediccion(pid)
    if not pred:
        return

    for col, (label, value, color) in zip(st.columns(4), _metricas_prediccion(pred)):
        with col:
            st.markdown(f"""
            <div class='inspector-card' style="text-align:center;">
                <div class="inspector-label">{label}</div>
                <div style="font-size:1.4rem; font-weight:700; color:{color}; margin-top:4px;">{value}</div>
            </div>
            """, unsafe_allow_html=True)


ACCIONES_STOCK = (("+1", 1), ("+5", 5), ("-1", -1), ("-5", -5))


def _render_acciones_rapidas(pid):
    """Muestra los botones de ajuste rapido de stock y el acceso a Inventario."""
    st.markdown("#### ⚡ Acciones Rapidas")
    cols = st.columns(len(ACCIONES_STOCK) + 1)
    for col, (etiqueta, delta) in zip(cols, ACCIONES_STOCK):
        with col:
            if st.button(etiqueta, key=f"ins_{etiqueta}"):
                _ajustar_stock(pid, delta)
    with cols[-1]:
        st.markdown(SALTO_HTML, unsafe_allow_html=True)
        st.button("📊 Inventario", key="ins_ver_inv", disabled=True,
                  help="Navega a la pestaña Inventario desde el menu lateral")


COLS_HISTORIAL = [2, 2, 1, 1, 2]
ENCABEZADOS_HISTORIAL = ["Fecha", "Cajero", "Cant.", "Precio", "Ticket"]


def _render_encabezados_historial():
    """Dibuja la fila de encabezados del historial."""
    for col, titulo in zip(st.columns(COLS_HISTORIAL), ENCABEZADOS_HISTORIAL):
        col.markdown(f"**{titulo}**")


def _render_fila_historial(item):
    """Dibuja una fila del historial de ventas en las columnas dadas."""
    fecha_str = item.get("fecha", "")
    if "T" in fecha_str:
        fecha_str = fecha_str.replace("T", " ")[:16]

    valores = [
        f"<div class='historial-row'>{fecha_str}</div>",
        f"<div class='historial-row'>{item.get('cajero', '')}</div>",
        f"<div class='historial-row' style='text-align:center;'><strong>{item.get('cantidad', 0)}</strong></div>",
        f"<div class='historial-row' style='text-align:right;'>€{item.get('precio_unitario', 0):.2f}</div>",
        f"<div class='historial-row' style='text-align:right; color:#64748b;'>#{item.get('numero_ticket', '')} — €{item.get('total_ticket', 0):.2f}</div>",
    ]
    for col, valor in zip(st.columns(COLS_HISTORIAL), valores):
        col.markdown(valor, unsafe_allow_html=True)


def _render_historial(pid):
    """Muestra el historial de ventas recientes del producto."""
    st.markdown("#### 📜 Historial de Ventas Recientes")
    historial = _obtener_historial(pid)
    if not historial:
        st.caption("No hay ventas recientes de este producto.")
        return

    _render_encabezados_historial()
    for item in historial:
        _render_fila_historial(item)


def _mostrar_ficha_producto(producto):
    """Muestra la ficha completa del producto con stock, prediccion e historial."""
    pid = producto.get("id")

    st.markdown(f"""
    <div style="margin-bottom:1rem;">
        <span style="background:rgba(139,92,246,0.15); color:#8b5cf6; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">{_nombre_categoria(producto)}</span>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # FILA 1: FOTO + FICHA + STOCK
    # ==========================================
    col_foto, col_ficha, col_stock = st.columns([1, 2, 1])
    with col_foto:
        _render_columna_foto(producto)
    with col_ficha:
        _render_columna_ficha(producto, pid)
    with col_stock:
        _render_columna_stock(producto, pid)

    # ==========================================
    # FILA 2: PREDICCION ML
    # ==========================================
    st.markdown(SALTO_HTML, unsafe_allow_html=True)
    _render_prediccion(pid)

    # ==========================================
    # FILA 3: ACCIONES RAPIDAS
    # ==========================================
    st.markdown(SALTO_HTML, unsafe_allow_html=True)
    _render_acciones_rapidas(pid)

    # ==========================================
    # FILA 4: HISTORIAL DE VENTAS
    # ==========================================
    st.markdown(SALTO_HTML, unsafe_allow_html=True)
    _render_historial(pid)


def _obtener_inventario(producto_id):
    """Obtiene inventario de un producto."""
    try:
        r = requests.get(f"{API_URL}/api/v1/inventario/{producto_id}", timeout=3)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _obtener_prediccion(producto_id):
    """Obtiene prediccion ML de un producto."""
    try:
        r = requests.get(f"{API_URL}/api/v1/prediccion/producto/{producto_id}?dias_futuro=7", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def _obtener_historial(producto_id):
    """Obtiene historial de ventas de un producto."""
    try:
        r = requests.get(f"{API_URL}/api/v1/tickets/historial/{producto_id}?limite=10", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return []


def _ajustar_stock(producto_id, delta):
    """Ajusta stock de un producto."""
    try:
        # Obtener stock actual
        inv = _obtener_inventario(producto_id)
        if inv:
            nuevo_stock = max(0, inv.get("cantidad", 0) + delta)
            data = {"cantidad": nuevo_stock, "ubicacion": inv.get("ubicacion", "Almacen A")}
            r = requests.post(
                f"{API_URL}/api/v1/inventario/{producto_id}",
                json=data,
                timeout=5
            )
            if r.status_code in [200, 201]:
                st.success(f"Stock ajustado: {nuevo_stock}")
                st.rerun()
            else:
                st.error(f"Error ajustando stock: {r.text}")
        else:
            st.error("No se pudo obtener inventario actual")
    except Exception as e:
        st.error(f"Error: {e}")
