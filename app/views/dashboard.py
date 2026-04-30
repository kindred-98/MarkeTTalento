"""
Página del Dashboard - Optimizada
"""
import streamlit as st
import plotly.graph_objects as go
import hashlib
import json
from app.utils.api import api_get
from app.utils.helpers import calcular_porcentaje
from app.utils.state import get_filtro_dashboard, update_dashboard_metrics, get_dashboard_metrics
from app.logic.inventario import calcular_estado_stock
from app.config import PRODUCTOS_POR_PAGINA


@st.cache_data(ttl=60, show_spinner=False)
def _get_dashboard_data():
    """Cachea datos del dashboard por 60 segundos."""
    inventarios = api_get("/api/v1/inventario", use_cache=False)
    productos = api_get("/api/v1/productos", use_cache=False)
    resumen = api_get("/api/v1/inventario/resumen", use_cache=False)
    return inventarios, productos, resumen


@st.cache_data(ttl=120, show_spinner=False)
def _calcular_estados_inventario(inventarios_json: str, productos_json: str):
    """Cachea cálculos de estados basados en datos serializados."""
    inventarios = json.loads(inventarios_json)
    productos = json.loads(productos_json)
    
    agotados = criticos = bajos = saludables = 0
    datos_stock = []
    
    for inv in inventarios:
        prod = next((p for p in productos if p.get("id") == inv.get("producto_id")), None)
        if prod:
            stock = inv.get("cantidad", 0)
            max_s = prod.get("stock_maximo", 100) or 100
            estado = calcular_estado_stock(stock, max_s)
            pct = calcular_porcentaje(stock, max_s)
            
            if estado == "Agotado":
                agotados += 1
            elif estado == "Crítico":
                criticos += 1
            elif estado == "Bajo":
                bajos += 1
            else:
                saludables += 1
            
            datos_stock.append({
                "producto": prod,
                "stock": stock,
                "max_s": max_s,
                "estado": estado,
                "pct": pct
            })
    
    return {
        "agotados": agotados,
        "criticos": criticos,
        "bajos": bajos,
        "saludables": saludables,
        "datos_stock": datos_stock
    }


def _generar_hash_datos(inventarios, productos) -> str:
    """Genera un hash único de los datos para detectar cambios."""
    # Usar solo IDs y cantidades para el hash
    datos_simples = []
    for inv in inventarios:
        datos_simples.append(f"{inv.get('producto_id')}:{inv.get('cantidad')}")
    datos_str = "|".join(sorted(datos_simples))
    return hashlib.md5(datos_str.encode()).hexdigest()


def render():
    """Renderiza el dashboard optimizado."""
    # Placeholder para carga inicial
    if '_dashboard_loaded' not in st.session_state:
        st.session_state['_dashboard_loaded'] = False
    
    if not st.session_state['_dashboard_loaded']:
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            st.spinner("Cargando dashboard...")
    
    st.markdown("<h2>🏠 Dashboard</h2>", unsafe_allow_html=True)
    
    # Obtener datos con cache
    inventarios, productos, resumen = _get_dashboard_data()
    
    # Generar hash de datos actuales
    datos_hash = _generar_hash_datos(inventarios, productos)
    
    # Verificar si necesitamos recalcular
    _, _, _, _, hash_cacheado = get_dashboard_metrics()
    
    if hash_cacheado != datos_hash:
        # Recalcular métricas solo si los datos cambiaron
        inv_json = json.dumps(inventarios)
        prod_json = json.dumps(productos)
        calculos = _calcular_estados_inventario(inv_json, prod_json)
        
        agotados = calculos["agotados"]
        criticos = calculos["criticos"]
        bajos = calculos["bajos"]
        saludables = calculos["saludables"]
        datos_stock = calculos["datos_stock"]
        
        # Guardar en session_state
        update_dashboard_metrics(agotados, criticos, bajos, saludables, datos_hash)
        st.session_state['_datos_stock_cache'] = datos_stock
    else:
        # Usar métricas cacheadas
        agotados, criticos, bajos, saludables, _ = get_dashboard_metrics()
        datos_stock = st.session_state.get('_datos_stock_cache', [])
    
    # Limpiar placeholder de carga
    if not st.session_state['_dashboard_loaded']:
        loading_placeholder.empty()
        st.session_state['_dashboard_loaded'] = True
    
    # Métricas - Usar st.empty() para evitar parpadeos
    metrics_container = st.container()
    with metrics_container:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8) 0%, rgba(26,35,50,0.6) 100%); border: 1px solid rgba(0,240,255,0.2); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="color: #94a3b8; font-size: 0.9rem;">PRODUCTOS</div>
                <div style="font-size: 2.5rem; font-weight: 700; color: #00f0ff; text-shadow: 0 0 20px rgba(0,240,255,0.5);">{resumen.get('total_productos', 0)}</div>
                <div style="color: #94a3b8; font-size: 1rem;">en catálogo</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8) 0%, rgba(26,35,50,0.6) 100%); border: 1px solid rgba(139,92,246,0.2); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="color: #94a3b8; font-size: 0.9rem;">STOCK TOTAL</div>
                <div style="font-size: 2.5rem; font-weight: 700; color: #8b5cf6; text-shadow: 0 0 20px rgba(139,92,246,0.5);">{resumen.get('total_unidades', 0)}</div>
                <div style="color: #94a3b8; font-size: 1rem;">unidades</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            color_crit = "#ef4444" if criticos > 0 else "#10b981"
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8) 0%, rgba(26,35,50,0.6) 100%); border: 1px solid rgba({color_crit.replace('#', '')},0.2); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="color: #94a3b8; font-size: 0.9rem;">CRÍTICOS</div>
                <div style="font-size: 2.5rem; font-weight: 700; color: {color_crit}; text-shadow: 0 0 20px {color_crit}40;">{criticos}</div>
                <div style="color: #94a3b8; font-size: 1rem;">requieren atención</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            valor = resumen.get("valor_total", 0)
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8) 0%, rgba(26,35,50,0.6) 100%); border: 1px solid rgba(16,185,129,0.2); border-radius: 16px; padding: 20px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
                <div style="color: #94a3b8; font-size: 0.9rem;">VALOR TOTAL</div>
                <div style="font-size: 2.5rem; font-weight: 700; color: #10b981; text-shadow: 0 0 20px rgba(16,185,129,0.5);">€{valor:.0f}</div>
                <div style="color: #94a3b8; font-size: 1rem;">en inventario</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gráfico de torta y alertas
    col_chart1, col_chart2 = st.columns([2, 1])
    
    with col_chart1:
        st.markdown("<h3>📊 Estado del Inventario</h3>", unsafe_allow_html=True)
        
        # Filtros con keys persistentes para evitar re-renders innecesarios
        col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])
        with col_f1:
            filtro_agotados = st.checkbox("Agotados", value=True, key="dash_filtro_agotados")
        with col_f2:
            filtro_criticos = st.checkbox("Críticos", value=True, key="dash_filtro_criticos")
        with col_f3:
            filtro_bajos = st.checkbox("Bajos", value=True, key="dash_filtro_bajos")
        with col_f4:
            filtro_saludables = st.checkbox("Saludables", value=True, key="dash_filtro_saludables")
        
        datos = [
            {"Estado": "Agotados", "Cantidad": agotados, "Color": "#6b7280"},
            {"Estado": "Críticos", "Cantidad": criticos, "Color": "#ef4444"},
            {"Estado": "Bajos", "Cantidad": bajos, "Color": "#f59e0b"},
            {"Estado": "Saludables", "Cantidad": saludables, "Color": "#10b981"},
        ]
        
        datos_filtrados = [d for d in datos if (
            (d["Estado"] == "Agotados" and filtro_agotados) or
            (d["Estado"] == "Críticos" and filtro_criticos) or
            (d["Estado"] == "Bajos" and filtro_bajos) or
            (d["Estado"] == "Saludables" and filtro_saludables)
        )]
        
        if datos_filtrados:
            # Cache de figura plotly para evitar recreación
            fig_key = f"pie_chart_{agotados}_{criticos}_{bajos}_{saludables}_{filtro_agotados}_{filtro_criticos}_{filtro_bajos}_{filtro_saludables}"
            
            if fig_key not in st.session_state:
                fig = go.Figure()
                
                fig.add_trace(go.Pie(
                    labels=[d["Estado"] for d in datos_filtrados],
                    values=[d["Cantidad"] for d in datos_filtrados],
                    marker=dict(colors=[d["Color"] for d in datos_filtrados]),
                    hole=0.6,
                    textinfo='label+percent',
                    textposition='outside',
                    textfont=dict(size=16, color='white', family='Cascadia Code', weight=600),
                    hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
                ))
                
                fig.update_layout(
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, font=dict(color="white", size=12)),
                    height=400,
                    paper_bgcolor="#0a0e17",
                    plot_bgcolor="#0a0e17",
                    font=dict(color="white"),
                    margin=dict(l=20, r=20, t=30, b=80),
                    # Deshabilitar animaciones para mejor rendimiento
                    transition=dict(duration=0),
                )
                
                st.session_state[fig_key] = fig
            else:
                fig = st.session_state[fig_key]
            
            # Usar use_container_width=True para mejor rendimiento
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    with col_chart2:
        st.markdown("<h3>⚡ Alertas</h3>", unsafe_allow_html=True)
        
        # Usar placeholder para evitar parpadeos
        alertas_placeholder = st.empty()
        
        alertas_html = ""
        if criticos > 0:
            alertas_html += f"""
            <div style="padding: 15px; background: rgba(239,68,68,0.2); border-left: 3px solid #ef4444; border-radius: 0 12px 12px 0; margin-bottom: 10px;">
                <div style="color: #ef4444; font-weight: 600; font-size: 1.1rem;">{criticos} Críticos</div>
                <div style="color: #94a3b8; font-size: 1rem;">Reposición urgente</div>
            </div>
            """
        
        if bajos > 0:
            alertas_html += f"""
            <div style="padding: 15px; background: rgba(245,158,11,0.2); border-left: 3px solid #f59e0b; border-radius: 0 12px 12px 0; margin-bottom: 10px;">
                <div style="color: #f59e0b; font-weight: 600; font-size: 1.1rem;">{bajos} Bajos</div>
                <div style="color: #94a3b8; font-size: 1rem;">Revisar pronto</div>
            </div>
            """
        
        if agotados > 0:
            alertas_html += f"""
            <div style="padding: 15px; background: rgba(107,114,128,0.2); border-left: 3px solid #6b7280; border-radius: 0 12px 12px 0; margin-bottom: 10px;">
                <div style="color: #6b7280; font-weight: 600; font-size: 1.1rem;">{agotados} Agotados</div>
                <div style="color: #94a3b8; font-size: 1rem;">Sin existencias</div>
            </div>
            """
        
        if criticos == 0 and bajos == 0 and agotados == 0:
            alertas_html += """
            <div style="padding: 15px; background: rgba(16,185,129,0.2); border-left: 3px solid #10b981; border-radius: 0 12px 12px 0;">
                <div style="color: #10b981; font-weight: 600; font-size: 1.1rem;">✓ Saludable</div>
                <div style="color: #94a3b8; font-size: 1rem;">Inventario en óptimas condiciones</div>
            </div>
            """
        
        alertas_placeholder.markdown(alertas_html, unsafe_allow_html=True)
    
    # Stock por Producto
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0, 240, 255, 0.1), rgba(139, 92, 246, 0.1)); 
                padding: 20px; border-radius: 15px; border: 1px solid rgba(0, 240, 255, 0.3);
                box-shadow: 0 0 30px rgba(0, 240, 255, 0.1); margin-bottom: 20px;">
        <h3 style="margin: 0; color: #00f0ff; text-shadow: 0 0 10px rgba(0, 240, 255, 0.5);">
            📦 Stock por Producto
        </h3>
        <p style="margin: 5px 0 0 0; color: #94a3b8; font-size: 0.85rem;">
            Visualización en tiempo real del inventario
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Filtros para stock por producto
    col_filtro1, col_filtro2, col_filtro3, col_filtro4 = st.columns([1, 1, 1, 1])
    with col_filtro1:
        filtro_stock_agotados = st.checkbox("⚫ Agotados", value=True, key="stock_filtro_agotados")
    with col_filtro2:
        filtro_stock_criticos = st.checkbox("🔴 Críticos", value=True, key="stock_filtro_criticos")
    with col_filtro3:
        filtro_stock_bajos = st.checkbox("🟡 Bajos", value=True, key="stock_filtro_bajos")
    with col_filtro4:
        filtro_stock_saludables = st.checkbox("🟢 Saludables", value=True, key="stock_filtro_saludables")
    
    # Filtrar y ordenar datos
    datos_stock_filtrados = []
    for d in datos_stock:
        if d["estado"] == "Agotado" and filtro_stock_agotados:
            datos_stock_filtrados.append(d)
        elif d["estado"] == "Crítico" and filtro_stock_criticos:
            datos_stock_filtrados.append(d)
        elif d["estado"] == "Bajo" and filtro_stock_bajos:
            datos_stock_filtrados.append(d)
        elif d["estado"] == "Saludable" and filtro_stock_saludables:
            datos_stock_filtrados.append(d)
    
    # Ordenar: Críticos primero
    estado_orden = {"Crítico": 0, "Agotado": 1, "Bajo": 2, "Saludable": 3}
    datos_stock_filtrados.sort(key=lambda x: (estado_orden.get(x["estado"], 3), x["producto"].get("nombre", "")))
    
    # Mostrar tabla de stock con lazy loading (máximo 20 items visibles)
    if datos_stock_filtrados:
        color_map = {
            "Agotado": "#6b7280",
            "Crítico": "#ef4444",
            "Bajo": "#f59e0b",
            "Saludable": "#10b981"
        }
        
        # Usar container para el scroll virtual
        stock_container = st.container()
        
        # Renderizar solo los primeros 20 para rendimiento inicial
        items_a_renderizar = min(20, len(datos_stock_filtrados))
        
        with stock_container:
            for i, d in enumerate(datos_stock_filtrados[:items_a_renderizar]):
                prod = d["producto"]
                stock = d["stock"]
                max_s = d["max_s"]
                estado = d["estado"]
                pct = d["pct"]
                color = color_map.get(estado, "#10b981")
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; background: rgba(30, 41, 59, 0.6); 
                            border-radius: 12px; padding: 16px 20px; margin-bottom: 10px;
                            border-left: 4px solid {color};
                            transition: all 0.3s ease;">
                    <div style="flex: 2; min-width: 150px;">
                        <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc;">{prod.get('nombre', 'Producto')}</div>
                    </div>
                    <div style="flex: 1; text-align: center;">
                        <span style="font-size: 1.5rem; font-weight: 600; color: #ffffff; font-family: 'Cascadia Code', monospace;">
                            {stock}
                        </span>
                        <span style="font-size: 1.3rem; font-weight: 700; color: #ffffff;">/</span>
                        <span style="font-size: 1.3rem; font-weight: 700; color: #10b981;">{max_s}</span>
                    </div>
                    <div style="flex: 1.5; padding: 0 20px;">
                        <div style="width: 100%; height: 12px; background: rgba(0, 0, 0, 0.4); border-radius: 6px; overflow: hidden;">
                            <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 6px;"></div>
                        </div>
                        <div style="text-align: center; font-size: 1rem; font-weight: 700; color: #ffffff; margin-top: 6px;">{pct:.0f}%</div>
                    </div>
                    <div style="flex: 1; text-align: right;">
                        <span style="padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;
                                    background: {color}30; color: {color}; border: 1px solid {color};">
                            {estado}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # Mostrar mensaje si hay más items
        if len(datos_stock_filtrados) > items_a_renderizar:
            st.info(f"ℹ️ Mostrando {items_a_renderizar} de {len(datos_stock_filtrados)} productos. Usa los filtros para ver más.")
    else:
        st.info("ℹ️ No hay productos para mostrar con los filtros seleccionados")
