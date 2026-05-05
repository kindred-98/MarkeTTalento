"""
Dashboard de Ventas Profesional
Con gráficos, métricas, filtros y exportación PDF
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from collections import Counter
from app.utils.api import api_get, api_post
from app.utils.helpers import to_excel, format_currency
from app.logic.venta import (
    calcular_total_venta,
    validar_venta,
    preparar_venta_data,
    preparar_datos_ventas,
    calcular_totales_ventas
)


def render():
    """Renderiza el dashboard completo de ventas."""
    st.markdown("<h2>💰 Dashboard de Ventas</h2>", unsafe_allow_html=True)
    
    # Cargar datos
    ventas = api_get("/api/v1/ventas", use_cache=False)
    productos = api_get("/api/v1/productos", use_cache=False)
    inventarios = api_get("/api/v1/inventario", use_cache=False)
    
    if not ventas:
        st.info("📊 No hay ventas registradas. ¡Comienza registrando tu primera venta!")
        render_nueva_venta(productos, inventarios)
        return
    
    # Preparar datos
    datos_ventas = preparar_datos_ventas(ventas, productos)
    df_ventas = pd.DataFrame(datos_ventas)
    
    # Tabs
    tab_dashboard, tab_historial, tab_nueva = st.tabs([
        "📊 Dashboard", 
        "📋 Historial Completo", 
        "➕ Nueva Venta"
    ])
    
    with tab_dashboard:
        render_dashboard(df_ventas, datos_ventas, productos)
    
    with tab_historial:
        render_historial_completo(df_ventas, datos_ventas)
    
    with tab_nueva:
        render_nueva_venta(productos, inventarios)


def render_dashboard(df_ventas, datos_ventas, productos):
    """Renderiza el dashboard con métricas y gráficos."""
    
    # Filtros de fecha
    col_filtro, col_export = st.columns([3, 1])
    
    with col_filtro:
        filtro_fecha = st.selectbox(
            "📅 Período",
            ["Hoy", "Últimos 7 días", "Últimos 30 días", "Este mes", "Mes pasado", "Todo"],
            key="filtro_fecha_ventas"
        )
    
    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📄 Exportar PDF", use_container_width=True, type="secondary"):
            exportar_pdf_dashboard(df_ventas, filtro_fecha)
    
    # Aplicar filtro
    df_filtrado = aplicar_filtro_fecha(df_ventas, filtro_fecha)
    
    if df_filtrado.empty:
        st.warning(f"📭 No hay ventas en el período: {filtro_fecha}")
        return
    
    # Métricas principales
    totales = calcular_totales_ventas(df_filtrado.to_dict('records'))
    
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Ingresos",
            value=f"€{totales['total_ingresos']:.2f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="🛒 Total Ventas",
            value=f"{totales['total_ventas']}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="📦 Unidades Vendidas",
            value=f"{totales['total_unidades']}",
            delta=None
        )
    
    with col4:
        ticket_promedio = totales['total_ingresos'] / totales['total_ventas'] if totales['total_ventas'] > 0 else 0
        st.metric(
            label="🎫 Ticket Promedio",
            value=f"€{ticket_promedio:.2f}",
            delta=None
        )
    
    st.markdown("---")
    
    # Gráficos
    col_izq, col_der = st.columns(2)
    
    with col_izq:
        st.markdown("#### 📈 Tendencia de Ventas")
        render_grafico_tendencia(df_filtrado)
    
    with col_der:
        st.markdown("#### 🥇 Top Productos Vendidos")
        render_top_productos(df_filtrado)
    
    st.markdown("---")
    
    # Ventas por hora/día
    col_izq2, col_der2 = st.columns(2)
    
    with col_izq2:
        st.markdown("#### ⏰ Ventas por Hora")
        render_ventas_por_hora(df_filtrado)
    
    with col_der2:
        st.markdown("#### 📊 Distribución de Ingresos")
        render_distribucion_ingresos(df_filtrado)


def render_historial_completo(df_ventas, datos_ventas):
    """Renderiza el historial completo con filtros."""
    
    # Filtros
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        busqueda = st.text_input("🔍 Buscar producto", placeholder="Nombre del producto...")
    
    with col2:
        cant_min = st.number_input("Cantidad mínima", min_value=0, value=0)
    
    with col3:
        cant_max = st.number_input("Cantidad máxima", min_value=0, value=9999)
    
    # Aplicar filtros
    df_filtrado = df_ventas.copy()
    
    if busqueda:
        df_filtrado = df_filtrado[df_filtrado['producto_nombre'].str.contains(busqueda, case=False, na=False)]
    
    df_filtrado = df_filtrado[(df_filtrado['cantidad'] >= cant_min) & (df_filtrado['cantidad'] <= cant_max)]
    
    # Exportar
    col_exp, _ = st.columns([1, 3])
    with col_exp:
        if not df_filtrado.empty:
            excel_data = to_excel(df_filtrado[['fecha_formateada', 'producto_nombre', 'cantidad', 'precio_unitario', 'total']])
            st.download_button(
                "📥 Excel",
                data=excel_data,
                file_name=f"ventas_{datetime.now().strftime('%Y%m%d')}.xlsx",
                use_container_width=True
            )
    
    # Mostrar ventas
    if df_filtrado.empty:
        st.info("No hay ventas que coincidan con los filtros")
        return
    
    # Paginación
    ventas_por_pagina = 10
    total_paginas = max(1, (len(df_filtrado) + ventas_por_pagina - 1) // ventas_por_pagina)
    
    if 'pagina_ventas_hist' not in st.session_state:
        st.session_state['pagina_ventas_hist'] = 1
    
    pagina_actual = min(st.session_state['pagina_ventas_hist'], total_paginas)
    inicio = (pagina_actual - 1) * ventas_por_pagina
    fin = min(inicio + ventas_por_pagina, len(df_filtrado))
    
    # Mostrar tarjetas
    for _, venta in df_filtrado.iloc[inicio:fin].iterrows():
        render_tarjeta_venta(venta)
    
    # Controles de paginación
    if total_paginas > 1:
        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
        with col_pag1:
            if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, key="btn_hist_ant"):
                st.session_state['pagina_ventas_hist'] = pagina_actual - 1
                st.rerun()
        with col_pag2:
            st.markdown(f"<p style='text-align: center;'>Página {pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
        with col_pag3:
            if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, key="btn_hist_sig"):
                st.session_state['pagina_ventas_hist'] = pagina_actual + 1
                st.rerun()


def render_nueva_venta(productos, inventarios):
    """Renderiza el formulario para nueva venta."""
    
    if not productos:
        st.warning("⚠️ No hay productos disponibles")
        return
    
    st.markdown("### ➕ Registrar Nueva Venta")
    
    # Mostrar productos en grid
    st.markdown("#### 📦 Selecciona un producto:")
    
    # Crear grid de productos seleccionables
    cols = st.columns(4)
    producto_seleccionado = None
    
    for idx, prod in enumerate(productos[:12]):  # Mostrar primeros 12
        with cols[idx % 4]:
            stock = get_stock_vista(prod.get('id'), inventarios)
            
            # Determinar si hay stock
            sin_stock = stock <= 0
            opacity = "0.5" if sin_stock else "1"
            cursor = "not-allowed" if sin_stock else "pointer"
            border = "2px solid #ef4444" if sin_stock else "1px solid rgba(255,255,255,0.1)"
            
            card_html = f'''
            <div style="opacity: {opacity}; border: {border}; border-radius: 8px; padding: 10px; margin-bottom: 10px; background: rgba(30,41,59,0.8); cursor: {cursor};">
                <div style="font-size: 13px; font-weight: 600; color: #f8fafc;">{prod.get('nombre')}</div>
                <div style="font-size: 11px; color: #64748b;">{prod.get('sku')}</div>
                <div style="font-size: 14px; color: #00f0ff; margin-top: 5px;">€{prod.get('precio_venta', 0):.2f}</div>
                <div style="font-size: 11px; color: {"#ef4444" if sin_stock else "#10b981"}; margin-top: 3px;">
                    {"❌ Sin stock" if sin_stock else f"✅ Stock: {stock}"}
                </div>
            </div>
            '''
            st.markdown(card_html, unsafe_allow_html=True)
            
            if not sin_stock:
                if st.button(f"Seleccionar", key=f"sel_prod_{prod.get('id')}", use_container_width=True):
                    st.session_state['producto_venta_id'] = prod.get('id')
                    st.rerun()
    
    # Formulario de venta
    if 'producto_venta_id' in st.session_state:
        prod_id = st.session_state['producto_venta_id']
        producto = next((p for p in productos if p.get('id') == prod_id), None)
        
        if producto:
            stock_disponible = get_stock_vista(prod_id, inventarios)
            precio = producto.get('precio_venta', 0)
            
            st.markdown("---")
            st.markdown(f"### 🛍️ Venta: **{producto.get('nombre')}**")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                st.markdown(f"**Precio:** €{precio:.2f}")
                st.markdown(f"**Stock disponible:** {stock_disponible}")
            
            with col2:
                cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    max_value=stock_disponible,
                    value=1,
                    key="cantidad_venta"
                )
            
            with col3:
                total = cantidad * precio
                st.markdown(f"<h3 style='color: #10b981; margin-top: 20px;'>€{total:.2f}</h3>", unsafe_allow_html=True)
            
            # Validaciones
            errores = []
            if cantidad > stock_disponible:
                errores.append(f"Stock insuficiente. Máximo: {stock_disponible}")
            
            if errores:
                for error in errores:
                    st.error(f"❌ {error}")
            else:
                # Confirmación
                st.markdown("<div style='background: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; border-radius: 8px; padding: 15px; margin: 15px 0;'>", unsafe_allow_html=True)
                st.markdown(f"**⚠️ Confirmar venta:**")
                st.markdown(f"- Producto: {producto.get('nombre')}")
                st.markdown(f"- Cantidad: {cantidad}")
                st.markdown(f"- Total: €{total:.2f}")
                st.markdown("</div>", unsafe_allow_html=True)
                
                confirmar = st.checkbox("✅ Confirmo los datos de la venta", key="confirmar_venta")
                
                col_btn1, col_btn2 = st.columns([1, 1])
                
                with col_btn1:
                    if st.button("💾 Registrar Venta", type="primary", disabled=not confirmar, use_container_width=True):
                        with st.spinner("💾 Registrando venta..."):
                            result = api_post("/api/v1/ventas", {
                                "producto_id": prod_id,
                                "cantidad": cantidad,
                                "precio_unitario": precio
                            })
                            
                            if result:
                                st.success("✅ ¡Venta registrada exitosamente!")
                                st.balloons()  # 🎉 Efecto de celebración
                                del st.session_state['producto_venta_id']
                                if 'confirmar_venta' in st.session_state:
                                    del st.session_state['confirmar_venta']
                                st.rerun()
                            else:
                                st.error("❌ Error al registrar la venta")
                
                with col_btn2:
                    if st.button("❌ Cancelar", use_container_width=True):
                        del st.session_state['producto_venta_id']
                        if 'confirmar_venta' in st.session_state:
                            del st.session_state['confirmar_venta']
                        st.rerun()


# Funciones auxiliares para gráficos

def render_grafico_tendencia(df):
    """Renderiza gráfico de tendencia de ventas."""
    if df.empty:
        st.info("Sin datos para mostrar")
        return
    
    # Agrupar por fecha
    df['fecha'] = pd.to_datetime(df['fecha'])
    df_grouped = df.groupby(df['fecha'].dt.date).agg({
        'total': 'sum',
        'cantidad': 'sum'
    }).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_grouped['fecha'],
        y=df_grouped['total'],
        mode='lines+markers',
        name='Ingresos',
        line=dict(color='#00f0ff', width=3),
        marker=dict(size=8, color='#00f0ff'),
        fill='tozeroy',
        fillcolor='rgba(0, 240, 255, 0.1)'
    ))
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8',
        xaxis_gridcolor='rgba(255,255,255,0.1)',
        yaxis_gridcolor='rgba(255,255,255,0.1)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_top_productos(df):
    """Renderiza top productos vendidos (vertical)."""
    if df.empty:
        st.info("Sin datos para mostrar")
        return
    
    top_productos = df.groupby('producto_nombre').agg({
        'cantidad': 'sum',
        'total': 'sum'
    }).sort_values('cantidad', ascending=True).head(5)  # Ascending para que el mayor quede arriba
    
    fig = go.Figure(data=[
        go.Bar(
            x=top_productos.index,
            y=top_productos['cantidad'],
            marker_color='#10b981',
            text=top_productos['cantidad'],
            textposition='auto',
            textfont=dict(size=16, color='white'),
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8',
        xaxis_gridcolor='rgba(255,255,255,0.1)',
        yaxis_gridcolor='rgba(255,255,255,0.1)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        xaxis_tickangle=-45  # Rotar labels para mejor lectura
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_ventas_por_hora(df):
    """Renderiza distribución de ventas por hora."""
    if df.empty or 'fecha' not in df.columns:
        st.info("Sin datos para mostrar")
        return
    
    df['hora'] = pd.to_datetime(df['fecha']).dt.hour
    ventas_por_hora = df.groupby('hora').size().reset_index(name='ventas')
    
    fig = go.Figure(data=[
        go.Bar(
            x=ventas_por_hora['hora'],
            y=ventas_por_hora['ventas'],
            marker_color='#f59e0b',
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8',
        xaxis_gridcolor='rgba(255,255,255,0.1)',
        yaxis_gridcolor='rgba(255,255,255,0.1)',
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        xaxis_title="Hora del día",
        yaxis_title="N° Ventas"
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_distribucion_ingresos(df):
    """Renderiza distribución de ingresos."""
    if df.empty:
        st.info("Sin datos para mostrar")
        return
    
    # Crear rangos de ingresos
    df['rango'] = pd.cut(df['total'], 
                         bins=[0, 10, 25, 50, 100, float('inf')],
                         labels=['€0-10', '€10-25', '€25-50', '€50-100', '€100+'])
    
    distribucion = df['rango'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=distribucion.index,
            values=distribucion.values,
            hole=0.4,
            marker_colors=["#b21798", "#116025", "#ffa200", "#dd1f1f", "#5c1bf3"],
            textfont=dict(size=16, color='white'),
        )
    ])
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#94a3b8',
        margin=dict(l=0, r=0, t=0, b=0),
        height=250,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def render_tarjeta_venta(venta):
    """Renderiza una tarjeta de venta individual."""
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8), rgba(26,35,50,0.6)); 
                border: 1px solid rgba(0,240,255,0.15); border-radius: 10px; padding: 12px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 16px; font-weight: 600; color: #f8fafc;">{venta['producto_nombre']}</div>
            <div style="color: #94a3b8; font-size: 14px;">{venta['fecha_formateada']}</div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 8px;">
            <div style="font-size: 16px; color: #64748b;">
                {venta['cantidad']} x €{venta['precio_unitario']:.2f}
            </div>
            <div style="font-size: 16px; font-weight: 700; color: #10b981;">
                €{venta['total']:.2f}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# Funciones utilitarias

def aplicar_filtro_fecha(df, filtro):
    """Aplica filtro de fecha al dataframe."""
    if df.empty:
        return df
    
    df['fecha'] = pd.to_datetime(df['fecha'])
    hoy = datetime.now().date()
    
    if filtro == "Hoy":
        return df[df['fecha'].dt.date == hoy]
    elif filtro == "Últimos 7 días":
        fecha_limite = hoy - timedelta(days=7)
        return df[df['fecha'].dt.date >= fecha_limite]
    elif filtro == "Últimos 30 días":
        fecha_limite = hoy - timedelta(days=30)
        return df[df['fecha'].dt.date >= fecha_limite]
    elif filtro == "Este mes":
        return df[(df['fecha'].dt.year == hoy.year) & (df['fecha'].dt.month == hoy.month)]
    elif filtro == "Mes pasado":
        mes_pasado = hoy.replace(day=1) - timedelta(days=1)
        return df[(df['fecha'].dt.year == mes_pasado.year) & (df['fecha'].dt.month == mes_pasado.month)]
    else:  # Todo
        return df


def get_stock_vista(producto_id, inventarios):
    """Obtiene stock para la vista de ventas."""
    for inv in inventarios:
        if inv.get("producto_id") == producto_id:
            return inv.get("cantidad", 0)
    return 0


def exportar_pdf_dashboard(df, filtro_periodo):
    """Exporta el dashboard a PDF."""
    try:
        from fpdf import FPDF
        import tempfile
        
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 16)
                self.cell(0, 10, 'Reporte de Ventas - MarkeTTalento', 0, 1, 'C')
                self.ln(10)
        
        pdf = PDF()
        pdf.add_page()
        pdf.set_font('Arial', '', 12)
        
        # Fecha y período
        pdf.cell(0, 10, f'Período: {filtro_periodo}', 0, 1)
        pdf.cell(0, 10, f'Generado: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1)
        pdf.ln(10)
        
        # Métricas
        totales = calcular_totales_ventas(df.to_dict('records'))
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Resumen', 0, 1)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'Total Ingresos: €{totales["total_ingresos"]:.2f}', 0, 1)
        pdf.cell(0, 10, f'Total Ventas: {totales["total_ventas"]}', 0, 1)
        pdf.cell(0, 10, f'Unidades Vendidas: {totales["total_unidades"]}', 0, 1)
        pdf.ln(10)
        
        # Tabla de ventas
        if not df.empty:
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, 'Detalle de Ventas', 0, 1)
            pdf.set_font('Arial', '', 10)
            
            # Encabezados
            pdf.set_fill_color(200, 200, 200)
            pdf.cell(60, 8, 'Producto', 1, 0, 'C', True)
            pdf.cell(30, 8, 'Fecha', 1, 0, 'C', True)
            pdf.cell(25, 8, 'Cantidad', 1, 0, 'C', True)
            pdf.cell(35, 8, 'P. Unitario', 1, 0, 'C', True)
            pdf.cell(35, 8, 'Total', 1, 1, 'C', True)
            
            # Datos
            for _, row in df.head(20).iterrows():
                pdf.cell(60, 8, str(row['producto_nombre'])[:25], 1)
                pdf.cell(30, 8, str(row['fecha_formateada'])[:10], 1)
                pdf.cell(25, 8, str(row['cantidad']), 1, 0, 'C')
                pdf.cell(35, 8, f"€{row['precio_unitario']:.2f}", 1, 0, 'R')
                pdf.cell(35, 8, f"€{row['total']:.2f}", 1, 1, 'R')
        
        # Guardar
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            pdf.output(tmp.name)
            with open(tmp.name, 'rb') as f:
                pdf_bytes = f.read()
        
        st.download_button(
            "⬇️ Descargar PDF",
            data=pdf_bytes,
            file_name=f"reporte_ventas_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        st.info("💡 Asegúrate de tener instalada la librería: pip install fpdf2")
