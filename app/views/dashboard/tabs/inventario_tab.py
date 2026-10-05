"""Inventario tab - Gráficas de stock"""
import html
import streamlit as st
from app.views.dashboard.data.getters import get_dashboard_data
from app.views.dashboard.components.grafica_pie import grafica_pie
from app.views.dashboard.config import get_stock_status, STOCK_AGOTADO, STOCK_STATUS_ALERTA, STOCK_STATUS_ORDEN


def render():
    data = get_dashboard_data()

    estados = dict.fromkeys(STOCK_STATUS_ORDEN, 0)
    for p in data["productos"]:
        stock = data["inv_map"].get(p.get("id"), 0)
        estados[get_stock_status(stock, p.get("stock_maximo"))] += 1

    stock_data = [
        {"label": estado, "value": estados[estado]}
        for estado in STOCK_STATUS_ORDEN
        if estados[estado] > 0
    ]

    col_pie, col_alertas = st.columns(2)

    with col_pie:
        st.markdown("### 📊 Estado del Stock")
        if stock_data:
            fig = grafica_pie(stock_data)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos")

    with col_alertas:
        st.markdown("### ⚠️ Alertas")
        _render_alertas(data)


def _render_alertas(data):
    alertas = []
    for p in data["productos"]:
        stock = data["inv_map"].get(p.get("id"), 0)
        status = get_stock_status(stock, p.get("stock_maximo"))
        if status in STOCK_STATUS_ALERTA:
            alertas.append(
                {
                    "nombre": p.get("nombre", ""),
                    "stock": stock,
                    "status": status,
                }
            )

    alertas = sorted(alertas, key=lambda x: x["stock"])

    if not alertas:
        st.success("✅ Sin alertas")
        return

    for a in alertas:
        mod = "dash-alert-tile--crit" if a["status"] == STOCK_AGOTADO else "dash-alert-tile--warn"
        nombre = html.escape(a["nombre"])
        st.markdown(
            f"""<div class="dash-alert-tile {mod}">
  <span class="dash-alert-tile__name">⚠️ {nombre}</span>
  <span class="dash-alert-tile__stock">Stock: {a["stock"]}</span>
</div>""",
            unsafe_allow_html=True,
        )
