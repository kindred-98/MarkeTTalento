"""
Página de Predicciones ML e Inteligencia de Negocio
3 Tabs: Demanda, Inteligencia, Alertas
"""
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from app.utils.api import api_get


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

    productos = api_get("/api/v1/productos") or []
    categorias = api_get("/api/v1/categorias") or []

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
        with st.spinner("Entrenando modelo..."):
            data = api_get(endpoint, use_cache=False)

        if not data:
            st.error("No hay datos suficientes para generar la predicción.")
            return

        _mostrar_grafico_demanda(data)
        _mostrar_metricas_demanda(data)


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
    st.plotly_chart(fig, use_container_width=True)


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
    with st.spinner("Calculando análisis ABC..."):
        abc = api_get("/api/v1/prediccion/abc", use_cache=False)

    if not abc:
        st.info("No hay datos suficientes para el análisis ABC.")
        return

    # Gráfico Pareto
    nombres = [p["nombre"] for p in abc[:15]]
    ingresos = [p["ingresos_totales"] for p in abc[:15]]
    clases = [p["clasificacion"] for p in abc[:15]]
    colores = {"A": "#10b981", "B": "#f59e0b", "C": "#6b7280"}
    bar_colors = [colores.get(c, "#94a3b8") for c in clases]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=nombres, y=ingresos,
        marker_color=bar_colors,
        text=clases, textposition='outside'
    ))
    fig.update_layout(
        title="Ingresos por Producto (Top 15) — Clasificación ABC",
        paper_bgcolor="#0f172a", plot_bgcolor="#0f172a",
        font=dict(color="#e2e8f0"),
        xaxis=dict(tickangle=-45, gridcolor="rgba(255,255,255,0.05)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
        height=400,
        showlegend=False,
        margin=dict(l=40, r=40, t=60, b=100)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Resumen
    total = len(abc)
    a_count = len([p for p in abc if p["clasificacion"] == "A"])
    b_count = len([p for p in abc if p["clasificacion"] == "B"])
    c_count = len([p for p in abc if p["clasificacion"] == "C"])

    cols = st.columns(4)
    cols[0].metric("Total Productos", total)
    cols[1].metric("Clase A", a_count, delta=f"~{a_count/total*100:.0f}%")
    cols[2].metric("Clase B", b_count, delta=f"~{b_count/total*100:.0f}%")
    cols[3].metric("Clase C", c_count, delta=f"~{c_count/total*100:.0f}%")

    # Tabla
    st.markdown("**Detalle por producto**")
    for p in abc:
        badge = f'<span class="badge-abc-{p["clasificacion"].lower()}">{p["clasificacion"]}</span>'
        st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid rgba(255,255,255,0.05);">
            <div>{badge} <strong>{p["nombre"]}</strong> <span style="color:#64748b; font-size:0.8rem;">({p["categoria"]})</span></div>
            <div style="text-align:right; font-size:0.85rem;">
                <div>€{p["ingresos_totales"]:,.2f}</div>
                <div style="color:#64748b;">{p["unidades_vendidas"]} uds</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_precios():
    with st.spinner("Analizando elasticidad de precios..."):
        precios = api_get("/api/v1/prediccion/precios", use_cache=False)

    if not precios:
        st.info("No hay sugerencias de precio disponibles.")
        return

    st.markdown(f"**{len(precios)} sugerencias encontradas**")

    for s in precios:
        color_sug = {"SUBIR": "#10b981", "BAJAR": "#ef4444", "MANTENER": "#94a3b8"}[s["sugerencia"]]
        icon = {"SUBIR": "⬆️", "BAJAR": "⬇️", "MANTENER": "➡️"}[s["sugerencia"]]
        st.markdown(f"""
        <div style="padding:12px; margin-bottom:8px; background:rgba(255,255,255,0.03); border-radius:10px; border-left:4px solid {color_sug};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <strong>{icon} {s["nombre"]}</strong>
                <span style="color:{color_sug}; font-weight:700;">{s["sugerencia"]}</span>
            </div>
            <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.85rem; color:#94a3b8;">
                <span>Precio actual: <strong>€{s["precio_actual"]:.2f}</strong></span>
                <span>Ajuste: <strong style="color:{color_sug};">{s["ajuste_pct"]:+.1f}%</strong></span>
                <span>Impacto estimado: <strong>€{s["impacto_estimado"]:,.2f}</strong>/mes</span>
            </div>
            <div style="margin-top:4px; font-size:0.75rem; color:#64748b;">
                Demanda diaria: {s["demanda_diaria"]:.2f} uds · Rotación: {s["rotacion"]}
            </div>
        </div>
        """, unsafe_allow_html=True)


def _render_estacionalidad():
    with st.spinner("Analizando estacionalidad..."):
        est = api_get("/api/v1/prediccion/estacionalidad", use_cache=False)

    if not est:
        st.info("No hay datos de estacionalidad disponibles.")
        return

    st.markdown(f"**Comparativa: {est.get('mes_actual', '')} vs {est.get('mes_anterior', '')}**")

    variacion = est.get("variacion_pct", {})
    actual = est.get("metricas_actual", {})
    anterior = est.get("metricas_anterior", {})

    cols = st.columns(3)
    for i, (label, key) in enumerate([("Ingresos", "ingresos"), ("Tickets", "tickets"), ("Unidades", "unidades")]):
        var = variacion.get(key, 0)
        delta_color = "normal" if var >= 0 else "inverse"
        cols[i].metric(
            label,
            f"{actual.get(key, 0):,.0f}",
            delta=f"{var:+.1f}% vs mes ant.",
            delta_color=delta_color
        )

    tendencia = est.get("tendencia", "ESTABLE")
    color_tend = {"ALZA": "#10b981", "BAJA": "#ef4444", "ESTABLE": "#f59e0b"}.get(tendencia, "#94a3b8")
    st.markdown(f"""
    <div style="margin-top:1rem; padding:12px; background:{color_tend}15; border-radius:8px; text-align:center;">
        <span style="font-size:1.2rem; font-weight:700; color:{color_tend};">Tendencia general: {tendencia}</span>
    </div>
    """, unsafe_allow_html=True)


def _render_alertas():
    st.markdown("#### Alertas de Reposición")

    with st.spinner("Escaneando inventario..."):
        alertas = api_get("/api/v1/prediccion/alertas", use_cache=False)

    if not alertas:
        st.success("✅ No hay alertas de reposición. Todo el stock está en niveles adecuados.")
        return

    # Resumen
    urgente = len([a for a in alertas if a["nivel"] == "URGENTE"])
    atencion = len([a for a in alertas if a["nivel"] == "ATENCION"])
    oportunidad = len([a for a in alertas if a["nivel"] == "OPORTUNIDAD"])

    cols = st.columns(4)
    cols[0].metric("Total Alertas", len(alertas))
    cols[1].metric("🔴 Urgentes", urgente)
    cols[2].metric("🟠 Atención", atencion)
    cols[3].metric("🔵 Oportunidad", oportunidad)

    st.markdown("---")

    # Filtro
    nivel_filtro = st.multiselect("Filtrar por nivel:", ["URGENTE", "ATENCION", "OPORTUNIDAD"],
                                   default=["URGENTE", "ATENCION", "OPORTUNIDAD"])

    for a in alertas:
        if a["nivel"] not in nivel_filtro:
            continue

        badge_class = {
            "URGENTE": "badge-urgente",
            "ATENCION": "badge-atencion",
            "OPORTUNIDAD": "badge-oportunidad"
        }.get(a["nivel"], "badge-oportunidad")

        st.markdown(f"""
        <div style="padding:12px; margin-bottom:8px; background:rgba(255,255,255,0.03); border-radius:10px; border-left:4px solid {'#ef4444' if a['nivel']=='URGENTE' else ('#f59e0b' if a['nivel']=='ATENCION' else '#3b82f6')};">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div><span class="{badge_class}">{a['nivel']}</span> <strong>{a['nombre']}</strong></div>
                <div style="text-align:right; font-size:0.85rem;">
                    <div>Stock: <strong>{a['stock_actual']}</strong> uds</div>
                    <div style="color:#ef4444;">Agotamiento: <strong>{a['dias_hasta_agotarse']:.1f} días</strong></div>
                </div>
            </div>
            <div style="margin-top:6px; font-size:0.8rem; color:#94a3b8;">
                Cantidad recomendada de reposición: <strong>{a['cantidad_recomendada']} uds</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)
