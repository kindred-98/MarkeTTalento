"""
Ventas - TPV Profesional + Dashboard + Historial
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import base64

from app.utils.api import api_get, api_post, api_delete
from app.utils.helpers import to_excel, format_currency
from app.utils.state import (
    init_tpv_state, get_tpv_carrito, set_tpv_carrito, limpiar_carrito,
    agregar_linea_carrito, actualizar_cantidad_linea, calcular_total_carrito, get_cajeros
)


# ============================================================================
# CONSTANTES
# ============================================================================

CAJEROS = get_cajeros()
METODOS_PAGO = ["efectivo", "tarjeta", "transferencia"]
PRODUCTOS_POR_PAGINA = 12


def _buscar_imagen_producto(producto: dict) -> str:
    """Intenta encontrar una imagen para el producto."""
    imagen_url = producto.get('imagen_url')
    if imagen_url and os.path.exists(imagen_url):
        return imagen_url
    # Buscar en docs/productos/
    nombre = producto.get('nombre', '').lower().replace(' ', '_')
    docs_dir = 'docs/productos'
    if os.path.exists(docs_dir):
        for ext in ['.jpg', '.jpeg', '.png']:
            for fname in os.listdir(docs_dir):
                if fname.lower().endswith(ext):
                    # Match parcial del nombre
                    if nombre in fname.lower() or fname.lower().replace(ext, '') in nombre:
                        return os.path.join(docs_dir, fname)
    return None


def _get_stock(producto_id: int, inventarios: list) -> int:
    for inv in inventarios:
        if inv.get('producto_id') == producto_id:
            return inv.get('cantidad', 0)
    return 0


# ============================================================================
# RENDER PRINCIPAL
# ============================================================================

def render():
    st.markdown("<h2 style='margin-bottom: 20px;'>💰 Gestión de Ventas</h2>", unsafe_allow_html=True)

    tab_dashboard, tab_historial, tab_tpv = st.tabs([
        "📊 Dashboard",
        "📋 Historial de Tickets",
        "💰 TPV"
    ])

    with tab_tpv:
        render_tpv()

    with tab_dashboard:
        render_dashboard()

    with tab_historial:
        render_historial()


# ============================================================================
# TAB TPV
# ============================================================================

def render_tpv():
    init_tpv_state()

    # Si se acaba de cobrar y hay ticket para mostrar
    if st.session_state.get('tpv_mostrar_ticket') and st.session_state.get('tpv_ticket_reciente'):
        render_ticket_post_cobro()
        return

    col_izq, col_der = st.columns([35, 65])

    with col_izq:
        render_panel_ticket()

    with col_der:
        render_panel_productos()


def render_panel_ticket():
    """Panel izquierdo: Ticket actual."""
    st.markdown("<div style='background: rgba(30,41,59,0.6); border-radius: 10px; padding: 15px; border: 1px solid rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    # Header
    cajero = st.selectbox("🧑‍💼 Cajero", CAJEROS, key="tpv_cajero_select")
    st.session_state['tpv_cajero'] = cajero
    st.markdown(f"<p style='color: #64748b; font-size: 0.8rem;'>📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>", unsafe_allow_html=True)

    st.markdown("---")

    carrito = get_tpv_carrito()

    # Lista de líneas
    if not carrito:
        st.markdown("<p style='color: #64748b; text-align: center; padding: 30px 0;'>🛒 Ticket vacío<br>Haz clic en un producto para agregarlo</p>", unsafe_allow_html=True)
    else:
        for idx, linea in enumerate(carrito):
            seleccionada = st.session_state.get('tpv_linea_seleccionada') == idx
            bg_color = "rgba(0,240,255,0.1)" if seleccionada else "transparent"
            border_color = "#00f0ff" if seleccionada else "rgba(255,255,255,0.05)"

            cols = st.columns([1, 4, 2, 2, 1, 1, 1])
            with cols[0]:
                if st.button(f"{'●' if seleccionada else '○'}", key=f"sel_linea_{idx}", help="Seleccionar línea"):
                    st.session_state['tpv_linea_seleccionada'] = idx
                    st.session_state['tpv_teclado_buffer'] = ''
                    st.rerun()
            with cols[1]:
                st.markdown(f"<div style='font-size: 0.9rem; color: #f8fafc;'>{linea['cantidad']} x {linea['nombre']}</div>", unsafe_allow_html=True)
            with cols[2]:
                st.markdown(f"<div style='font-size: 0.85rem; color: #94a3b8; text-align: right;'>€{linea['precio_unitario']:.2f}</div>", unsafe_allow_html=True)
            with cols[3]:
                st.markdown(f"<div style='font-size: 0.9rem; color: #10b981; text-align: right; font-weight: 600;'>€{linea['subtotal']:.2f}</div>", unsafe_allow_html=True)
            with cols[4]:
                if st.button("➖", key=f"btn_menos_{idx}"):
                    actualizar_cantidad_linea(idx, linea['cantidad'] - 1)
                    st.rerun()
            with cols[5]:
                if st.button("➕", key=f"btn_mas_{idx}"):
                    actualizar_cantidad_linea(idx, linea['cantidad'] + 1)
                    st.rerun()
            with cols[6]:
                if st.button("🗑️", key=f"btn_del_{idx}"):
                    actualizar_cantidad_linea(idx, 0)
                    st.rerun()

            st.markdown(f"<div style='background: {bg_color}; border: 1px solid {border_color}; border-radius: 6px; margin: 2px -5px; padding: 4px 8px;'></div>", unsafe_allow_html=True)

    st.markdown("---")

    # Teclado numérico funcional
    if carrito:
        render_teclado_numerico()

    st.markdown("---")

    # Total
    total = calcular_total_carrito()
    st.markdown(f"<h2 style='text-align: center; color: #00f0ff; margin: 10px 0;'>Total: €{total:.2f}</h2>", unsafe_allow_html=True)

    # Botones de acción
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💶 Efectivo", use_container_width=True, type="primary", disabled=not carrito):
            st.session_state['tpv_metodo_pago'] = 'efectivo'
            st.session_state['tpv_mostrar_cobro'] = True
            st.rerun()
    with col2:
        if st.button("💳 Tarjeta", use_container_width=True, type="primary", disabled=not carrito):
            st.session_state['tpv_metodo_pago'] = 'tarjeta'
            st.session_state['tpv_mostrar_cobro'] = True
            st.rerun()
    with col3:
        if st.button("🧹 Limpiar", use_container_width=True, type="secondary"):
            limpiar_carrito()
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Modal de cobro (usando expander/conditional)
    if st.session_state.get('tpv_mostrar_cobro'):
        render_cobro_modal()


def render_teclado_numerico():
    """Teclado numérico funcional para cambiar cantidades."""
    linea_sel = st.session_state.get('tpv_linea_seleccionada')
    if linea_sel is None:
        st.markdown("<p style='color: #64748b; font-size: 0.8rem; text-align: center;'>👆 Selecciona una línea y usa el teclado para cambiar la cantidad</p>", unsafe_allow_html=True)
        return

    buffer = st.session_state.get('tpv_teclado_buffer', '')
    st.markdown(f"<p style='color: #00f0ff; font-size: 1.2rem; text-align: center; margin: 5px 0;'>Cantidad: {buffer if buffer else '...'}</p>", unsafe_allow_html=True)

    teclas = [
        ['7', '8', '9'],
        ['4', '5', '6'],
        ['1', '2', '3'],
        ['0', '.', 'CLR']
    ]

    for fila in teclas:
        cols = st.columns(3)
        for i, tecla in enumerate(fila):
            with cols[i]:
                if st.button(tecla, key=f"tecla_{tecla}", use_container_width=True):
                    if tecla == 'CLR':
                        st.session_state['tpv_teclado_buffer'] = ''
                    else:
                        st.session_state['tpv_teclado_buffer'] += tecla
                    st.rerun()

    # Botón aplicar
    if buffer:
        try:
            cantidad = int(float(buffer))
            if st.button("✅ Aplicar Cantidad", use_container_width=True, type="primary"):
                actualizar_cantidad_linea(linea_sel, cantidad)
                st.rerun()
        except ValueError:
            st.error("Cantidad inválida")


def render_cobro_modal():
    """Pantalla de cobro."""
    total = calcular_total_carrito()
    metodo = st.session_state.get('tpv_metodo_pago', 'efectivo')

    with st.container():
        st.markdown("---")
        st.markdown(f"<h3 style='color: #00f0ff; text-align: center;'>💰 Cobrar - Total: €{total:.2f}</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: #94a3b8;'>Método: {metodo.upper()}</p>", unsafe_allow_html=True)

        entrega = total
        cambio = 0.0

        if metodo == 'efectivo':
            entrega = st.number_input("💶 Entrega (€)", min_value=float(total), value=float(total * 1.1), step=0.5, format="%.2f")
            cambio = round(entrega - total, 2)
            st.markdown(f"<h4 style='color: #10b981; text-align: center;'>Cambio: €{cambio:.2f}</h4>", unsafe_allow_html=True)

        confirmar = st.checkbox("✅ Confirmar cobro", key="confirmar_cobro")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state['tpv_mostrar_cobro'] = False
                st.rerun()
        with col2:
            if st.button("✅ Finalizar Venta", use_container_width=True, type="primary", disabled=not confirmar):
                with st.spinner("Registrando venta..."):
                    lineas_api = []
                    for linea in get_tpv_carrito():
                        lineas_api.append({
                            "producto_id": linea['producto_id'],
                            "cantidad": linea['cantidad'],
                            "precio_unitario": linea['precio_unitario']
                        })

                    payload = {
                        "cajero": st.session_state['tpv_cajero'],
                        "metodo_pago": metodo,
                        "entrega_efectivo": entrega if metodo == 'efectivo' else None,
                        "cambio": cambio if metodo == 'efectivo' else None,
                        "lineas": lineas_api
                    }

                    result = api_post("/api/v1/tickets", payload)
                    if result:
                        st.session_state['tpv_mostrar_cobro'] = False
                        st.session_state['tpv_mostrar_ticket'] = True
                        st.session_state['tpv_ticket_reciente'] = result
                        limpiar_carrito()
                        st.rerun()
                    else:
                        st.error("❌ Error al registrar el ticket")
        st.markdown("---")


def render_ticket_post_cobro():
    """Muestra el ticket simplificado después del cobro."""
    ticket = st.session_state['tpv_ticket_reciente']

    st.markdown("<div style='background: rgba(30,41,59,0.8); border-radius: 12px; padding: 25px; border: 1px solid rgba(0,240,255,0.3); max-width: 400px; margin: 0 auto;'>", unsafe_allow_html=True)

    st.markdown("<h3 style='text-align: center; color: #00f0ff; margin-bottom: 5px;'>MARKE TTALENTO</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 0.9rem;'>Ticket N° {ticket['numero_ticket']}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>{ticket['fecha'][:16].replace('T', ' ')}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>Cajero: {ticket['cajero']}</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    for linea in ticket['lineas']:
        nombre = linea.get('producto', {}).get('nombre', f"Producto {linea['producto_id']}")
        st.markdown(f"""
        <div style="display: flex; justify-content: space-between; margin: 4px 0;">
            <span style="color: #f8fafc; font-size: 0.9rem;">{linea['cantidad']} x {nombre}</span>
            <span style="color: #10b981; font-size: 0.9rem;">€{linea['subtotal']:.2f}</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    st.markdown(f"<h4 style='text-align: right; color: #00f0ff;'>TOTAL: €{ticket['total']:.2f}</h4>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: right; color: #94a3b8; font-size: 0.85rem;'>Método: {ticket['metodo_pago'].upper()}</p>", unsafe_allow_html=True)

    if ticket.get('entrega_efectivo'):
        st.markdown(f"<p style='text-align: right; color: #94a3b8; font-size: 0.85rem;'>Entrega: €{ticket['entrega_efectivo']:.2f}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: right; color: #10b981; font-size: 0.85rem;'>Cambio: €{ticket['cambio']:.2f}</p>", unsafe_allow_html=True)

    st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.8rem; margin-top: 15px;'>¡Gracias por su visita!</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Botón descargar ticket
    ticket_txt = generar_ticket_txt(ticket)
    st.download_button(
        "📥 Descargar Ticket",
        data=ticket_txt,
        file_name=f"ticket_{ticket['numero_ticket']}.txt",
        mime="text/plain",
        use_container_width=True
    )

    if st.button("🔄 Nueva Venta", use_container_width=True, type="primary"):
        st.session_state['tpv_mostrar_ticket'] = False
        st.session_state['tpv_ticket_reciente'] = None
        st.rerun()


def generar_ticket_txt(ticket: dict) -> str:
    """Genera el contenido del ticket en formato texto."""
    lineas = []
    lineas.append("-" * 42)
    lineas.append("           MARKE TTALENTO")
    lineas.append(f"         Ticket N° {ticket['numero_ticket']}")
    lineas.append(f"    {ticket['fecha'][:16].replace('T', ' ')}")
    lineas.append(f"    Cajero: {ticket['cajero']}")
    lineas.append("-" * 42)
    for linea in ticket['lineas']:
        nombre = linea.get('producto', {}).get('nombre', f"Prod {linea['producto_id']}")
        lineas.append(f"{linea['cantidad']} x {nombre:<20} {linea['subtotal']:>7.2f} €")
    lineas.append("-" * 42)
    lineas.append(f"TOTAL:{'':>28} {ticket['total']:>7.2f} €")
    lineas.append(f"Metodo: {ticket['metodo_pago'].upper()}")
    if ticket.get('entrega_efectivo'):
        lineas.append(f"Entrega:{'':>27} {ticket['entrega_efectivo']:>7.2f} €")
        lineas.append(f"Cambio:{'':>28} {ticket['cambio']:>7.2f} €")
    lineas.append("-" * 42)
    lineas.append("      ¡Gracias por su visita!")
    lineas.append("-" * 42)
    return "\n".join(lineas)


def render_panel_productos():
    """Panel derecho: Categorías y productos."""
    productos = api_get("/api/v1/productos", use_cache=False)
    categorias = api_get("/api/v1/categorias", use_cache=False)
    inventarios = api_get("/api/v1/inventario", use_cache=False)

    if not productos:
        st.warning("⚠️ No hay productos disponibles")
        return

    cat_activa = st.session_state.get('tpv_categoria_activa', 'todos')

    # Fila de categorías
    cats_filtradas = [{"id": "todos", "nombre": "Todos"}] + [{"id": c["id"], "nombre": c["nombre"]} for c in categorias]
    cols_cats = st.columns(min(len(cats_filtradas), 6))
    for i, cat in enumerate(cats_filtradas[:6]):
        with cols_cats[i]:
            es_activa = cat_activa == cat["id"]
            color = "#00f0ff" if es_activa else "#64748b"
            bg = "rgba(0,240,255,0.15)" if es_activa else "rgba(30,41,59,0.6)"
            if st.button(cat["nombre"], key=f"cat_{cat['id']}", use_container_width=True):
                st.session_state['tpv_categoria_activa'] = cat["id"]
                st.rerun()

    st.markdown("<hr style='margin: 10px 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

    # Filtrar productos
    productos_filtrados = productos
    if cat_activa != 'todos':
        productos_filtrados = [p for p in productos if p.get('categoria_id') == cat_activa]

    # Grid de productos
    cols_grid = st.columns(4)
    for idx, prod in enumerate(productos_filtrados):
        stock = _get_stock(prod.get('id'), inventarios)
        sin_stock = stock <= 0
        imagen = _buscar_imagen_producto(prod)

        with cols_grid[idx % 4]:
            opacity = "0.4" if sin_stock else "1"
            cursor = "not-allowed" if sin_stock else "pointer"
            border = "2px solid #ef4444" if sin_stock else "1px solid rgba(255,255,255,0.1)"

            # Tarjeta de producto
            card_html = f"""
            <div style="opacity: {opacity}; border: {border}; border-radius: 10px; padding: 10px;
                        background: rgba(30,41,59,0.8); cursor: {cursor}; text-align: center;
                        margin-bottom: 10px; height: 140px; display: flex; flex-direction: column;
                        justify-content: space-between;">
            """

            if imagen and os.path.exists(imagen):
                try:
                    with open(imagen, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode()
                    card_html += f'<img src="data:image/jpeg;base64,{img_b64}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 6px; margin: 0 auto;">'
                except Exception:
                    card_html += f'<div style="font-size: 2rem; margin: 0 auto;">📦</div>'
            else:
                card_html += f'<div style="font-size: 2rem; margin: 0 auto;">📦</div>'

            card_html += f"""
                <div style="font-size: 0.85rem; font-weight: 600; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">{prod.get('nombre')}</div>
                <div style="font-size: 0.9rem; color: #00f0ff; font-weight: 700;">€{prod.get('precio_venta', 0):.2f}</div>
                <div style="font-size: 0.75rem; color: {'#ef4444' if sin_stock else '#10b981'};">{'❌ Sin stock' if sin_stock else f'✅ Stock: {stock}'}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

            if not sin_stock:
                if st.button("Agregar", key=f"add_prod_{prod.get('id')}", use_container_width=True):
                    agregar_linea_carrito(prod)
                    st.rerun()


# ============================================================================
# TAB DASHBOARD
# ============================================================================

def render_dashboard():
    """Dashboard completo con métricas y 10 gráficas."""
    # Cargar datos
    resumen = api_get("/api/v1/tickets/estadisticas/resumen", use_cache=False)
    tendencia = api_get("/api/v1/tickets/estadisticas/tendencia?dias=30", use_cache=False)
    por_categoria = api_get("/api/v1/tickets/estadisticas/por-categoria?dias=30", use_cache=False)
    por_hora = api_get("/api/v1/tickets/estadisticas/por-hora?dias=30", use_cache=False)
    mapa_calor = api_get("/api/v1/tickets/estadisticas/mapa-calor?dias=30", use_cache=False)
    comparativa = api_get("/api/v1/tickets/estadisticas/comparativa-mes", use_cache=False)
    top_productos_u = api_get("/api/v1/tickets/estadisticas/top-productos?dias=30&por=unidades", use_cache=False)
    top_productos_e = api_get("/api/v1/tickets/estadisticas/top-productos?dias=30&por=ingresos", use_cache=False)
    ticket_promedio = api_get("/api/v1/tickets/estadisticas/ticket-promedio?dias=30", use_cache=False)

    if not resumen or resumen.get('total_tickets', 0) == 0:
        st.info("📊 No hay tickets registrados aún. ¡Usa el TPV para registrar ventas!")
        return

    # Métricas principales
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("💰 Total Ingresos", f"€{resumen['total_ingresos']:.2f}")
    with c2:
        st.metric("🎫 Tickets", resumen['total_tickets'])
    with c3:
        st.metric("📦 Unidades", resumen['total_unidades'])
    with c4:
        st.metric("📈 Ticket Promedio", f"€{resumen['ticket_promedio']:.2f}")
    st.markdown("---")

    # Gráficas fila 1
    col1, col2 = st.columns(2)
    with col1:
        grafica_tendencia(tendencia)
    with col2:
        grafica_top_productos_unidades(top_productos_u)

    # Gráficas fila 2
    col3, col4 = st.columns(2)
    with col3:
        grafica_ventas_por_hora(por_hora)
    with col4:
        grafica_distribucion_ingresos(resumen)

    # Gráficas fila 3
    col5, col6 = st.columns(2)
    with col5:
        grafica_ventas_por_categoria(por_categoria)
    with col6:
        grafica_ticket_promedio(ticket_promedio)

    # Gráficas fila 4
    col7, col8 = st.columns(2)
    with col7:
        grafica_top_productos_ingresos(top_productos_e)
    with col8:
        grafica_mapa_calor(mapa_calor)

    # Gráficas fila 5
    col9, col10 = st.columns(2)
    with col9:
        grafica_metodos_pago(resumen)
    with col10:
        grafica_comparativa_mes(comparativa)


def _plotly_config(fig, height=280):
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8',
        margin=dict(l=0, r=0, t=30, b=0),
        height=height,
        xaxis_gridcolor='rgba(255,255,255,0.05)',
        yaxis_gridcolor='rgba(255,255,255,0.05)',
    )
    return fig


def grafica_tendencia(datos):
    st.markdown("#### 📈 Tendencia de Ventas")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['ingresos'],
        mode='lines+markers',
        name='Ingresos',
        line=dict(color='#00f0ff', width=3),
        fill='tozeroy', fillcolor='rgba(0,240,255,0.1)'
    ))
    fig.update_layout(title_text="Ingresos por día", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_top_productos_unidades(datos):
    st.markdown("#### 🥇 Top Productos (Unidades)")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Bar(
        x=df['producto'], y=df['unidades'],
        marker_color='#10b981', text=df['unidades'], textposition='auto'
    )])
    fig.update_layout(title_text="Más vendidos por cantidad", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_ventas_por_hora(datos):
    st.markdown("#### ⏰ Ventas por Hora")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Bar(
        x=df['hora'], y=df['ventas'],
        marker_color='#f59e0b'
    )])
    fig.update_layout(title_text="Distribución horaria", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_distribucion_ingresos(resumen):
    st.markdown("#### 📊 Distribución Ingresos")
    # Crear rangos simulados a partir de tickets
    tickets = api_get("/api/v1/tickets?limite=500", use_cache=False)
    if not tickets:
        st.info("Sin datos")
        return
    rangos = {"€0-10": 0, "€10-25": 0, "€25-50": 0, "€50-100": 0, "€100+": 0}
    for t in tickets:
        total = t.get('total', 0)
        if total <= 10:
            rangos["€0-10"] += 1
        elif total <= 25:
            rangos["€10-25"] += 1
        elif total <= 50:
            rangos["€25-50"] += 1
        elif total <= 100:
            rangos["€50-100"] += 1
        else:
            rangos["€100+"] += 1
    fig = go.Figure(data=[go.Pie(
        labels=list(rangos.keys()), values=list(rangos.values()),
        hole=0.4,
        marker_colors=["#b21798", "#116025", "#ffa200", "#dd1f1f", "#5c1bf3"]
    )])
    fig.update_layout(title_text="Por rango de ticket", title_font_size=12, showlegend=True,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_ventas_por_categoria(datos):
    st.markdown("#### 🏷️ Ventas por Categoría")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Pie(
        labels=df['categoria'], values=df['ingresos'],
        hole=0.5,
        marker_colors=px.colors.sequential.Plasma
    )])
    fig.update_layout(title_text="Ingresos por categoría", title_font_size=12,
                      legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_ticket_promedio(datos):
    st.markdown("#### 📉 Ticket Promedio")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df['fecha'], y=df['ticket_promedio'],
        mode='lines+markers',
        line=dict(color='#8b5cf6', width=3),
        fill='tozeroy', fillcolor='rgba(139,92,246,0.1)'
    ))
    fig.update_layout(title_text="Evolución del ticket promedio", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_top_productos_ingresos(datos):
    st.markdown("#### 💶 Top Productos (Ingresos)")
    if not datos:
        st.info("Sin datos")
        return
    df = pd.DataFrame(datos)
    fig = go.Figure(data=[go.Bar(
        x=df['ingresos'], y=df['producto'], orientation='h',
        marker_color='#00f0ff', text=[f"€{x:.2f}" for x in df['ingresos']], textposition='auto'
    )])
    fig.update_layout(title_text="Más rentables", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_mapa_calor(datos):
    st.markdown("#### 🔥 Mapa de Calor (Día/Hora)")
    if not datos:
        st.info("Sin datos")
        return
    # Construir matriz
    horas = list(range(24))
    dias = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    matriz = [[0 for _ in horas] for _ in dias]
    for fila in datos:
        d = fila['dia_num']
        for h_data in fila['horas']:
            matriz[d][h_data['hora']] = h_data['ventas']

    fig = go.Figure(data=go.Heatmap(
        z=matriz,
        x=[f"{h:02d}h" for h in horas],
        y=dias,
        colorscale='YlOrRd'
    ))
    fig.update_layout(title_text="Tickets por día y hora", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_metodos_pago(resumen):
    st.markdown("#### 💳 Métodos de Pago")
    metodos = resumen.get('metodos_pago', {})
    if not metodos:
        st.info("Sin datos")
        return
    fig = go.Figure(data=[go.Bar(
        x=list(metodos.keys()), y=list(metodos.values()),
        marker_color=['#10b981', '#3b82f6', '#f59e0b']
    )])
    fig.update_layout(title_text="Preferencia de pago", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


def grafica_comparativa_mes(datos):
    st.markdown("#### 📅 Mes Actual vs Anterior")
    if not datos:
        st.info("Sin datos")
        return
    actual = datos.get('mes_actual', {})
    anterior = datos.get('mes_anterior', {})
    categorias = ['Ingresos', 'Tickets', 'Unidades']
    valores_actual = [actual.get('ingresos', 0), actual.get('tickets', 0), actual.get('unidades', 0)]
    valores_anterior = [anterior.get('ingresos', 0), anterior.get('tickets', 0), anterior.get('unidades', 0)]

    fig = go.Figure()
    fig.add_trace(go.Bar(name=datos.get('nombre_mes_actual', 'Actual'), x=categorias, y=valores_actual, marker_color='#00f0ff'))
    fig.add_trace(go.Bar(name=datos.get('nombre_mes_anterior', 'Anterior'), x=categorias, y=valores_anterior, marker_color='#64748b'))
    fig.update_layout(barmode='group', title_text="Comparativa mensual", title_font_size=12)
    st.plotly_chart(_plotly_config(fig), use_container_width=True)


# ============================================================================
# TAB HISTORIAL
# ============================================================================

def render_historial():
    """Historial de tickets con filtros y anulación."""
    st.markdown("### 📋 Historial de Tickets")

    # Filtros
    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

    with col1:
        cajeros_opciones = ["Todos"] + CAJEROS
        filtro_cajero = st.selectbox("Cajero", cajeros_opciones, key="hist_cajero")

    with col2:
        fecha_desde = st.date_input("Desde", value=None, key="hist_desde")

    with col3:
        fecha_hasta = st.date_input("Hasta", value=None, key="hist_hasta")

    with col4:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()

    # Construir query params
    params = {"limite": 200}
    if filtro_cajero != "Todos":
        params["cajero"] = filtro_cajero
    if fecha_desde:
        params["fecha_desde"] = fecha_desde.isoformat()
    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta.isoformat()

    # Cargar tickets
    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    tickets = api_get(f"/api/v1/tickets?{query_string}", use_cache=False)

    if not tickets:
        st.info("📭 No hay tickets en el período seleccionado")
        return

    # Exportar
    if tickets:
        df_export = []
        for t in tickets:
            for linea in t.get('lineas', []):
                df_export.append({
                    "ticket": t['numero_ticket'],
                    "fecha": t['fecha'][:16].replace('T', ' '),
                    "cajero": t['cajero'],
                    "estado": t['estado'],
                    "metodo_pago": t['metodo_pago'],
                    "producto": linea.get('producto', {}).get('nombre', ''),
                    "cantidad": linea['cantidad'],
                    "precio_unitario": linea['precio_unitario'],
                    "subtotal": linea['subtotal'],
                    "total_ticket": t['total']
                })
        if df_export:
            excel_data = to_excel(pd.DataFrame(df_export))
            st.download_button("📥 Exportar Excel", data=excel_data,
                               file_name=f"historial_tickets_{datetime.now().strftime('%Y%m%d')}.xlsx",
                               use_container_width=True)

    # Paginación
    pagina = st.session_state.get('tpv_pagina_historial', 1)
    por_pagina = 10
    total_paginas = max(1, (len(tickets) + por_pagina - 1) // por_pagina)
    pagina = min(pagina, total_paginas)
    inicio = (pagina - 1) * por_pagina
    fin = min(inicio + por_pagina, len(tickets))

    # Mostrar tickets
    for t in tickets[inicio:fin]:
        estado_color = "#10b981" if t['estado'] == 'completado' else "#ef4444"
        with st.expander(f"🎫 Ticket N° {t['numero_ticket']} | €{t['total']:.2f} | {t['cajero']} | {t['fecha'][:16].replace('T', ' ')}"):
            st.markdown(f"<p style='color: {estado_color}; font-weight: 600;'>Estado: {t['estado'].upper()}</p>", unsafe_allow_html=True)
            st.markdown(f"**Método de pago:** {t['metodo_pago'].upper()}")
            if t.get('entrega_efectivo'):
                st.markdown(f"**Entrega:** €{t['entrega_efectivo']:.2f} | **Cambio:** €{t['cambio']:.2f}")

            # Tabla de líneas
            lineas_data = []
            for linea in t.get('lineas', []):
                nombre = linea.get('producto', {}).get('nombre', f"Producto {linea['producto_id']}")
                lineas_data.append({
                    "Producto": nombre,
                    "Cantidad": linea['cantidad'],
                    "P. Unitario": f"€{linea['precio_unitario']:.2f}",
                    "Subtotal": f"€{linea['subtotal']:.2f}"
                })
            if lineas_data:
                st.table(pd.DataFrame(lineas_data))

            # Botón anular (solo si está completado)
            if t['estado'] == 'completado':
                col_a, _ = st.columns([1, 3])
                with col_a:
                    if st.button("❌ Anular Ticket", key=f"anular_{t['id']}", use_container_width=True):
                        with st.spinner("Anulando..."):
                            result = api_delete(f"/api/v1/tickets/{t['id']}")
                            if result:
                                st.success("Ticket anulado correctamente")
                                st.rerun()
                            else:
                                st.error("Error al anular")

    # Controles paginación
    if total_paginas > 1:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c1:
            if st.button("⬅️ Anterior", disabled=pagina <= 1, key="hist_ant"):
                st.session_state['tpv_pagina_historial'] = pagina - 1
                st.rerun()
        with c2:
            st.markdown(f"<p style='text-align: center;'>Página {pagina} de {total_paginas}</p>", unsafe_allow_html=True)
        with c3:
            if st.button("Siguiente ➡️", disabled=pagina >= total_paginas, key="hist_sig"):
                st.session_state['tpv_pagina_historial'] = pagina + 1
                st.rerun()
