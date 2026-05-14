"""Estadísticas tab - Gráficas de ventas"""
import html
import streamlit as st
from app.views.dashboard.data.getters import get_dashboard_data
from app.views.dashboard.components.grafica_bar import grafica_bar


def render():
    data = get_dashboard_data()

    col_ventas, col_productos = st.columns(2)

    with col_ventas:
        st.markdown("### 📈 Ventas por Mes")
        ventas_mes = {}
        for t in data["tickets_ok"]:
            fecha = str(t.get("fecha", ""))[:7]
            if fecha:
                ventas_mes[fecha] = ventas_mes.get(fecha, 0) + t.get("total", 0)

        ventas_data = [{"label": k, "value": v} for k, v in sorted(ventas_mes.items())]

        if ventas_data:
            fig = grafica_bar(ventas_data)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos de ventas")

    with col_productos:
        st.markdown("### 🏆 Top Productos")
        _render_top_productos(data)


def _render_top_productos(data):
    productos_stock = [
        {"nombre": p.get("nombre", ""), "stock": data["inv_map"].get(p.get("id"), 0)}
        for p in data["productos"]
    ]
    productos_stock = sorted(productos_stock, key=lambda x: x["stock"], reverse=True)[:10]

    if not productos_stock:
        st.info("Sin productos")
        return

    for i, p in enumerate(productos_stock, 1):
        nombre = html.escape(p["nombre"] or "")
        st.markdown(
            f"""<div class="dash-rank-row">
  <span class="dash-rank-row__badge">{i}</span>
  <span class="dash-rank-row__name">{nombre}</span>
  <span class="dash-rank-row__stat">{p["stock"]}</span>
</div>""",
            unsafe_allow_html=True,
        )
