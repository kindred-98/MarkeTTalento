"""
Pagina de Inspector de Producto
Escanea codigo de barras o SKU y muestra ficha completa, stock, prediccion ML e historial.
"""
import streamlit as st
from datetime import datetime
from app.utils.api import api_get, api_post
import requests
from app.config import API_URL


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
            productos = api_get("/api/v1/productos", use_cache=False)
            for p in productos:
                if texto.lower() in p.get("nombre", "").lower():
                    return p
            return None

        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None


def _mostrar_ficha_producto(producto):
    """Muestra la ficha completa del producto con stock, prediccion e historial."""
    pid = producto.get("id")

    # Encabezado con categoria
    cat = producto.get("categoria", {})
    cat_nombre = cat.get("nombre", "") if isinstance(cat, dict) else str(cat)
    st.markdown(f"""
    <div style="margin-bottom:1rem;">
        <span style="background:rgba(139,92,246,0.15); color:#8b5cf6; padding:4px 12px; border-radius:20px; font-size:0.8rem; font-weight:600;">{cat_nombre}</span>
    </div>
    """, unsafe_allow_html=True)

    # ==========================================
    # FILA 1: FOTO + FICHA + STOCK
    # ==========================================
    col_foto, col_ficha, col_stock = st.columns([1, 2, 1])

    with col_foto:
        st.markdown("<div class='inspector-card'>", unsafe_allow_html=True)
        if producto.get("imagen_url"):
            try:
                st.image(producto["imagen_url"], width="stretch")
            except Exception:
                st.markdown("<div style='height:150px; display:flex; align-items:center; justify-content:center; color:#64748b; font-size:3rem;'>📦</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='height:150px; display:flex; align-items:center; justify-content:center; color:#64748b; font-size:3rem;'>📦</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_ficha:
        st.markdown("<div class='inspector-card'>", unsafe_allow_html=True)
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
            <strong>Proveedor:</strong> {producto.get('proveedor', {}).get('nombre', 'N/A') if isinstance(producto.get('proveedor'), dict) else 'N/A'}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_stock:
        # Obtener inventario
        inv = _obtener_inventario(pid)
        stock = inv.get("cantidad", 0) if inv else 0
        ubicacion = inv.get("ubicacion", "—") if inv else "—"

        # Determinar estado
        stock_min = producto.get("stock_minimo", 5)
        if stock <= 2:
            badge_class = "badge-stock-critico"
            estado = "CRITICO"
        elif stock <= stock_min:
            badge_class = "badge-stock-bajo"
            estado = "BAJO"
        else:
            badge_class = "badge-stock-ok"
            estado = "OK"

        st.markdown("<div class='inspector-card'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="text-align:center; margin-bottom:12px;">
            <div class="inspector-label">Stock actual</div>
            <div class="inspector-metric" style="font-size:2.2rem; margin:4px 0;">{stock}</div>
            <span class="{badge_class}">{estado}</span>
        </div>
        <div style="text-align:center; color:#64748b; font-size:0.8rem; margin-top:8px;">
            <strong>Ubicacion:</strong><br/>{ubicacion}
        </div>
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ==========================================
    # FILA 2: PREDICCION ML
    # ==========================================
    st.markdown("<br/>", unsafe_allow_html=True)
    with st.container():
        pred = _obtener_prediccion(pid)
        if pred:
            cols_pred = st.columns(4)
            metricas = [
                ("Consumo promedio", f"{pred.get('consumo_promedio_diario', 0):.2f} uds/dia", "#0ea5e9"),
                ("Dias hasta agotarse", f"{pred.get('dias_hasta_agotarse', 0):.1f}", "#f59e0b"),
                ("Tendencia", pred.get("tendencia", "ESTABLE"), "#10b981"),
                ("Estado stock", pred.get("estado_stock", "ADECUADO"), "#8b5cf6"),
            ]
            for col, (label, value, color) in zip(cols_pred, metricas):
                with col:
                    st.markdown(f"""
                    <div class='inspector-card' style="text-align:center;">
                        <div class="inspector-label">{label}</div>
                        <div style="font-size:1.4rem; font-weight:700; color:{color}; margin-top:4px;">{value}</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ==========================================
    # FILA 3: ACCIONES RAPIDAS
    # ==========================================
    st.markdown("<br/>", unsafe_allow_html=True)
    with st.container():
        st.markdown("#### ⚡ Acciones Rapidas")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            if st.button("+1", key="ins_plus1"):
                _ajustar_stock(pid, 1)
        with c2:
            if st.button("+5", key="ins_plus5"):
                _ajustar_stock(pid, 5)
        with c3:
            if st.button("-1", key="ins_minus1"):
                _ajustar_stock(pid, -1)
        with c4:
            if st.button("-5", key="ins_minus5"):
                _ajustar_stock(pid, -5)
                with c5:
                    st.markdown("<br/>", unsafe_allow_html=True)
                    st.button("📊 Inventario", key="ins_ver_inv", disabled=True, help="Navega a la pestaña Inventario desde el menu lateral")

    # ==========================================
    # FILA 4: HISTORIAL DE VENTAS
    # ==========================================
    st.markdown("<br/>", unsafe_allow_html=True)
    with st.container():
        st.markdown("#### 📜 Historial de Ventas Recientes")
        historial = _obtener_historial(pid)

        if historial:
            cols_h = st.columns([2, 2, 1, 1, 2])
            cols_h[0].markdown("**Fecha**")
            cols_h[1].markdown("**Cajero**")
            cols_h[2].markdown("**Cant.**")
            cols_h[3].markdown("**Precio**")
            cols_h[4].markdown("**Ticket**")

            for item in historial:
                fecha_str = item.get("fecha", "")
                if "T" in fecha_str:
                    fecha_str = fecha_str.replace("T", " ")[:16]
                cols_h = st.columns([2, 2, 1, 1, 2])
                cols_h[0].markdown(f"<div class='historial-row'>{fecha_str}</div>", unsafe_allow_html=True)
                cols_h[1].markdown(f"<div class='historial-row'>{item.get('cajero', '')}</div>", unsafe_allow_html=True)
                cols_h[2].markdown(f"<div class='historial-row' style='text-align:center;'><strong>{item.get('cantidad', 0)}</strong></div>", unsafe_allow_html=True)
                cols_h[3].markdown(f"<div class='historial-row' style='text-align:right;'>€{item.get('precio_unitario', 0):.2f}</div>", unsafe_allow_html=True)
                cols_h[4].markdown(f"<div class='historial-row' style='text-align:right; color:#64748b;'>#{item.get('numero_ticket', '')} — €{item.get('total_ticket', 0):.2f}</div>", unsafe_allow_html=True)
        else:
            st.caption("No hay ventas recientes de este producto.")


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
