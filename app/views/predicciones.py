"""
Página de Predicciones ML e Inteligencia de Negocio
3 Tabs: Demanda, Inteligencia, Alertas
"""
from datetime import date, datetime

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.db import DatabaseAccess


def _obj_to_dict(obj):
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return obj


def _fecha_a_yyyy_mm(fecha) -> str | None:
    """Convierte fecha de ticket (datetime, date o str ISO) a 'YYYY-MM'."""
    if fecha is None:
        return None
    if isinstance(fecha, datetime):
        return fecha.strftime("%Y-%m")
    if isinstance(fecha, date):
        return fecha.strftime("%Y-%m")
    s = str(fecha).strip()
    return s[:7] if len(s) >= 7 else None


def render():
    st.markdown("""
    <style>
    .pred-header {
        background: linear-gradient(90deg, #0ea5e9, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background: rgba(14,165,233,0.08);
        border: 1px solid rgba(14,165,233,0.2);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .badge-urgente { background: #ef4444; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-atencion { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-oportunidad { background: #3b82f6; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-abc-a { background: #10b981; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-abc-b { background: #f59e0b; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    .badge-abc-c { background: #6b7280; color: white; padding: 2px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; }
    </style>
    <div class="pred-header">🔮 Predicciones ML & Inteligencia de Negocio</div>
    <p style="color:#94a3b8; margin-top:0;">Machine learning real con scikit-learn: demanda, ABC, estacionalidad y precio óptimo.</p>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 Demanda", "🧠 Inteligencia", "🚨 Alertas"])

    with tab1:
        _render_demanda()

    with tab2:
        _render_inteligencia()

    with tab3:
        _render_alertas()


def _render_demanda():
    st.markdown("#### Predicción de Demanda")

    col1, col2 = st.columns([1, 3])
    with col1:
        modo = st.radio("Analizar por:", ["Producto", "Categoría"], horizontal=True)

    db = DatabaseAccess()
    try:
        productos = db.get_productos()
        categorias = db.get_categorias()
        productos = [_obj_to_dict(p) for p in productos]
        categorias = [_obj_to_dict(c) for c in categorias]
    finally:
        db.close()

    if modo == "Producto":
        opciones = {p["nombre"]: p["id"] for p in productos}
        sel = st.selectbox("Selecciona producto:", list(opciones.keys()))
        pid = opciones.get(sel)
        endpoint = f"/api/v1/prediccion/producto/{pid}"
    else:
        opciones = {c["nombre"]: c["id"] for c in categorias}
        sel = st.selectbox("Selecciona categoría:", list(opciones.keys()))
        cid = opciones.get(sel)
        endpoint = f"/api/v1/prediccion/categoria/{cid}"

    if st.button("🔮 Generar Pronóstico", type="primary"):
        st.info("🔮 Las predicciones ML requieren iniciar la API: uvicorn src.api:app --port 8002")
        st.markdown("**Demo - Productos disponibles:**")
        for p in productos[:5]:
            st.markdown(f"- {p.get('nombre', 'N/A')} — €{p.get('precio_venta', 0):.2f}")


def _mostrar_grafico_demanda(data):
    hist = data.get("historico", [])
    pron = data.get("pronostico", [])

    if not hist:
        st.info("Sin datos históricos.")
        return

    fig = go.Figure()

    # Histórico
    fechas_hist = [h["fecha"] for h in hist]
    vals_hist = [h["cantidad"] for h in hist]
    fig.add_trace(go.Scatter(
        x=fechas_hist, y=vals_hist,
        mode='lines', name='Histórico',
        line=dict(color='#0ea5e9', width=2),
        fill='tozeroy', fillcolor='rgba(14,165,233,0.1)'
    ))

    # Pronóstico
    if pron:
        fechas_pron = [p["fecha"] for p in pron]
        vals_pron = [p["cantidad"] for p in pron]
        # Unir último histórico con primero pronóstico para continuidad visual
        if fechas_hist and fechas_pron:
            fechas_pron = [fechas_hist[-1]] + fechas_pron
            vals_pron = [vals_hist[-1]] + vals_pron

        fig.add_trace(go.Scatter(
            x=fechas_pron, y=vals_pron,
            mode='lines', name='Pronóstico ML',
            line=dict(color='#8b5cf6', width=2, dash='dash'),
            fill='tozeroy', fillcolor='rgba(139,92,246,0.1)'
        ))

    fig.update_layout(
        title=f"Demanda: {data.get('producto_nombre', '')}",
        paper_bgcolor="#0f172a",
        plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        xaxis=dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)", showgrid=True),
        height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    st.plotly_chart(fig, width="stretch")


def _mostrar_metricas_demanda(data):
    cols = st.columns(4)
    metricas = [
        ("Consumo promedio/día", f"{data.get('consumo_promedio_diario', 0):.2f} uds", "#0ea5e9"),
        ("Días hasta agotarse", f"{data.get('dias_hasta_agotarse', 0):.1f}", "#f59e0b"),
        ("Tendencia", data.get("tendencia", "ESTABLE"), "#10b981"),
        ("Stock actual", str(data.get("stock_actual", 0)), "#8b5cf6"),
    ]
    for col, (label, value, color) in zip(cols, metricas):
        col.markdown(f"""
        <div class="metric-card">
            <div style="font-size:0.8rem; color:#94a3b8;">{label}</div>
            <div style="font-size:1.4rem; font-weight:700; color:{color};">{value}</div>
        </div>
        """, unsafe_allow_html=True)

    estado = data.get("estado_stock", "ADECUADO")
    color_estado = {"CRITICO": "#ef4444", "BAJO": "#f59e0b", "MODERADO": "#3b82f6", "ADECUADO": "#10b981"}.get(estado, "#94a3b8")
    st.markdown(f"""
    <div style="margin-top:1rem; padding:10px; background:{color_estado}15; border-left:4px solid {color_estado}; border-radius:0 8px 8px 0;">
        <strong style="color:{color_estado};">Estado de stock: {estado}</strong>
        {" — ¡Reponer urgentemente!" if estado == "CRITICO" else (" — Considerar reposición" if estado == "BAJO" else "")}
    </div>
    """, unsafe_allow_html=True)


def _render_inteligencia():
    st.markdown("#### Inteligencia de Negocio")

    subtab1, subtab2, subtab3 = st.tabs(["📊 Análisis ABC", "💰 Precio Óptimo", "📅 Estacionalidad"])

    with subtab1:
        _render_abc()
    with subtab2:
        _render_precios()
    with subtab3:
        _render_estacionalidad()


def _render_abc():
    st.info("📊 Análisis ABC requiere iniciar la API con: uvicorn src.api:app --port 8002")
    st.markdown("O inicia con `python start_api.py` para ver predicciones ML.")
    
    db = DatabaseAccess()
    try:
        productos = db.get_productos()
        productos = [_obj_to_dict(p) for p in productos]
        tickets = db.get_tickets(limite=500)
        tickets = [_obj_to_dict(t) for t in tickets]
    finally:
        db.close()
    
    if not productos:
        st.warning("No hay productos registrados.")
        return
    
    st.markdown("### Top 10 Productos por Nombre")
    nombres = [p["nombre"] for p in productos[:15]]
    precios = [p.get("precio_venta", 0) for p in productos[:15]]
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=nombres, y=precios, marker_color="#10b981"))
    fig.update_layout(title="Productos (demostración)", paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0"), height=400)
    st.plotly_chart(fig, width="stretch")


def _render_precios():
    st.info("💰 Precio óptimo requiere iniciar la API con: uvicorn src.api:app --port 8002")
    st.markdown("Las predicciones ML avanzadas necesitan el backend FastAPI.")

    db = DatabaseAccess()
    try:
        productos = db.get_productos()
        productos = [_obj_to_dict(p) for p in productos]
    finally:
        db.close()

    if not productos:
        st.warning("No hay productos.")
        return

    st.markdown(f"**{len(productos)} productos disponibles**")
    for p in productos[:10]:
        precio = p.get("precio_venta", 0)
        coste = p.get("precio_coste", 0) or 0
        margen = ((precio - coste) / precio * 100) if precio > 0 else 0
        color = "#10b981" if margen > 20 else "#f59e0b" if margen > 10 else "#ef4444"
        st.markdown(f"""
        <div style="padding:12px; margin-bottom:8px; background:rgba(255,255,255,0.03); border-radius:10px; border-left:4px solid {color};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>{p.get("nombre", "N/A")}</strong>
                <span style="color:{color}; font-weight:700;">Margen: {margen:.1f}%</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.85rem; color:#94a3b8;">
                <span>Precio: <strong>€{precio:.2f}</strong></span>
                <span>Coste: <strong>€{coste:.2f}</strong></span>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_estacionalidad():
    st.info("📅 Estacionalidad requiere iniciar la API con: uvicorn src.api:app --port 8002")
    
    db = DatabaseAccess()
    try:
        tickets = db.get_tickets(limite=100)
        tickets = [_obj_to_dict(t) for t in tickets]
    finally:
        db.close()

    if not tickets:
        st.warning("No hay tickets para analizar estacionalidad.")
        return
    
    st.markdown("### Distribución de Tickets por Mes")
    meses = {}
    for t in tickets:
        fecha = t.get("fecha")
        mes = _fecha_a_yyyy_mm(fecha)
        if mes:
            meses[mes] = meses.get(mes, 0) + 1
    
    if meses:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(meses.keys()), y=list(meses.values()), marker_color="#0ea5e9"))
        fig.update_layout(title="Tickets por Mes", paper_bgcolor="#0f172a", plot_bgcolor="#0f172a", font=dict(color="#e2e8f0"), height=300)
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Sin datos de fecha en tickets.")


COLOR_STOCK_AGOTADO = "#ef4444"
COLOR_STOCK_BAJO = "#f59e0b"
STOCK_MAX_POR_DEFECTO = 100
UMBRAL_STOCK_CRITICO = 0.2


def _cargar_datos_alertas():
    """Carga productos e inventario como diccionarios."""
    db = DatabaseAccess()
    try:
        productos = [_obj_to_dict(p) for p in db.get_productos()]
        inventarios = [_obj_to_dict(i) for i in db.get_inventario()]
    finally:
        db.close()
    return productos, inventarios


def _detectar_alertas(productos, inventarios):
    """Devuelve los productos cuyo stock esta por debajo del umbral critico."""
    inv_by_prod = {i["producto_id"]: i for i in inventarios}
    alertas = []

    for p in productos:
        inv = inv_by_prod.get(p["id"])
        if not inv:
            continue
        stock = inv.get("cantidad", 0)
        stock_max = p.get("stock_maximo") or STOCK_MAX_POR_DEFECTO
        if stock <= stock_max * UMBRAL_STOCK_CRITICO:
            alertas.append({
                "nombre": p.get("nombre", "N/A"),
                "stock": stock,
                "stock_max": stock_max,
            })

    return alertas


def _render_alerta(alerta):
    """Dibuja una alerta de reposicion."""
    color = COLOR_STOCK_AGOTADO if alerta["stock"] == 0 else COLOR_STOCK_BAJO
    st.markdown(f"""
    <div style="padding:12px; margin-bottom:8px; background:rgba(239,68,68,0.1); border-radius:10px; border-left:4px solid {color};">
        <strong>⚠️ {alerta['nombre']}</strong> — Stock: {alerta['stock']} / {alerta['stock_max']}
    </div>
    """, unsafe_allow_html=True)


def _render_alertas():
    st.markdown("#### Alertas de Reposición")

    productos, inventarios = _cargar_datos_alertas()
    alertas = _detectar_alertas(productos, inventarios)

    if not alertas:
        st.success("✅ No hay alertas de reposición. Todo el stock está en niveles adecuados.")
        return

    for alerta in alertas:
        _render_alerta(alerta)
