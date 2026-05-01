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
    
    # Título pequeño y discreto (como en la imagen)
    st.markdown("<h3 style='margin-bottom: 20px; color: #94a3b8; font-size: 1.2rem;'>Dashboard</h3>", unsafe_allow_html=True)
    
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
            <div style="background: rgba(26,35,50,0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 15px;">
                <div style="width: 40px; height: 40px; background: rgba(0,240,255,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">📦</div>
                <div>
                    <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">Productos en Catálogo</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #00f0ff;">{resumen.get('total_productos', 0)}</div>
                    <div style="color: #64748b; font-size: 0.75rem;">en catálogo</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="background: rgba(26,35,50,0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 15px;">
                <div style="width: 40px; height: 40px; background: rgba(139,92,246,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">📊</div>
                <div>
                    <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">Stock Total Unidades</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #8b5cf6;">{resumen.get('total_unidades', 0)}</div>
                    <div style="color: #64748b; font-size: 0.75rem;">unidades</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            color_crit = "#ef4444" if criticos > 0 else "#10b981"
            st.markdown(f"""
            <div style="background: rgba(26,35,50,0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 15px;">
                <div style="width: 40px; height: 40px; background: rgba({color_crit.replace('#', '')},0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">⚠️</div>
                <div>
                    <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">Índice Críticos</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: {color_crit};">{criticos}</div>
                    <div style="color: #64748b; font-size: 0.75rem;">requieren atención</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            valor = resumen.get("valor_total", 0)
            st.markdown(f"""
            <div style="background: rgba(26,35,50,0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 15px; display: flex; align-items: center; gap: 15px;">
                <div style="width: 40px; height: 40px; background: rgba(16,185,129,0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">💰</div>
                <div>
                    <div style="color: #64748b; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.5px;">Valor Total Inventario</div>
                    <div style="font-size: 1.8rem; font-weight: 700; color: #10b981;">€{valor:.0f}</div>
                    <div style="color: #64748b; font-size: 0.75rem;">en inventario</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # LAYOUT PRINCIPAL: Dos columnas (izquierda 2/3, derecha 1/3)
    col_main_left, col_main_right = st.columns([2, 1])
    
    # ============================================
    # COLUMNA IZQUIERDA: Stock por Producto
    # ============================================
    with col_main_left:
        # Header de Stock por Producto con buscador
        col_header, col_search = st.columns([2, 1])
        with col_header:
            st.markdown("""
            <div style="margin-bottom: 5px;">
                <h3 style="margin: 0; color: #00f0ff; font-size: 1.1rem;">
                    📦 Stock por Producto
                </h3>
                <p style="margin: 0; color: #64748b; font-size: 0.75rem;">
                    Visualización en tiempo real del inventario
                </p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_search:
            busqueda = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed", key="search_productos")
        
        # Filtros independientes para la LISTA de productos
        if 'filtros_lista' not in st.session_state:
            st.session_state['filtros_lista'] = {
                'agotados': True,
                'criticos': True,
                'bajos': True,
                'saludables': True
            }
        
        st.markdown("<p style='color: #94a3b8; font-size: 0.75rem; margin-bottom: 8px;'>💡 Haz clic para filtrar productos:</p>", unsafe_allow_html=True)
        
        # Badge visual de filtros activos (clickeables!)
        filtros_config = [
            ("⚫ Agotados", 'agotados', "#6b7280"),
            ("🔴 Críticos", 'criticos', "#ef4444"),
            ("🟡 Bajos", 'bajos', "#f59e0b"),
            ("🟢 Saludables", 'saludables', "#10b981"),
        ]
        
        # Crear badges clickeables usando botones
        filtros_cols = st.columns([1, 1, 1, 1])
        
        col_idx = 0
        for label, filtro_nombre, color in filtros_config:
            with filtros_cols[col_idx]:
                is_active = st.session_state['filtros_lista'][filtro_nombre]
                
                btn_label = f"{'✓' if is_active else '✕'} {label}"
                clicked = st.button(
                    btn_label, 
                    key=f"btn_lista_{filtro_nombre}",
                    use_container_width=True,
                    type="primary" if is_active else "secondary"
                )
                if clicked:
                    st.session_state['filtros_lista'][filtro_nombre] = not is_active
                    st.rerun()
            col_idx += 1
        
        # Filtrar datos por estado y búsqueda
        datos_stock_filtrados = []
        for d in datos_stock:
            # Filtrar por estado
            if d["estado"] == "Agotado" and st.session_state['filtros_lista']['agotados']:
                pass
            elif d["estado"] == "Crítico" and st.session_state['filtros_lista']['criticos']:
                pass
            elif d["estado"] == "Bajo" and st.session_state['filtros_lista']['bajos']:
                pass
            elif d["estado"] == "Saludable" and st.session_state['filtros_lista']['saludables']:
                pass
            else:
                continue
            
            # Filtrar por búsqueda
            if busqueda and busqueda.strip():
                nombre_prod = d["producto"].get('nombre', '').lower()
                if busqueda.lower() not in nombre_prod:
                    continue
            
            datos_stock_filtrados.append(d)
        
        # Ordenar: Críticos primero
        estado_orden = {"Crítico": 0, "Agotado": 1, "Bajo": 2, "Saludable": 3}
        datos_stock_filtrados.sort(key=lambda x: (estado_orden.get(x["estado"], 3), x["producto"].get("nombre", "")))
        
        # Mostrar tabla de stock
        if datos_stock_filtrados:
            color_map = {
                "Agotado": "#6b7280",
                "Crítico": "#ef4444",
                "Bajo": "#f59e0b",
                "Saludable": "#10b981"
            }
            
            items_a_renderizar = min(20, len(datos_stock_filtrados))
            
            for i, d in enumerate(datos_stock_filtrados[:items_a_renderizar]):
                prod = d["producto"]
                stock = d["stock"]
                max_s = d["max_s"]
                estado = d["estado"]
                pct = d["pct"]
                color = color_map.get(estado, "#10b981")
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; background: rgba(30, 41, 59, 0.5); 
                            border-radius: 10px; padding: 10px 14px; margin-bottom: 6px;
                            border-left: 3px solid {color};">
                    <div style="width: 32px; height: 32px; background: rgba(255,255,255,0.1); border-radius: 6px; 
                                display: flex; align-items: center; justify-content: center; margin-right: 12px;">
                        <span style="font-size: 1rem;">📦</span>
                    </div>
                    <div style="flex: 2; min-width: 100px;">
                        <div style="font-size: 0.9rem; font-weight: 600; color: #f8fafc;">{prod.get('nombre', 'Producto')}</div>
                    </div>
                    <div style="flex: 0.8; text-align: center;">
                        <span style="font-size: 1.1rem; font-weight: 600; color: #ffffff;">{stock}</span>
                        <span style="color: #64748b; font-size: 0.8rem;">/</span>
                        <span style="font-size: 0.9rem; color: #64748b;">{max_s}</span>
                    </div>
                    <div style="flex: 1.2; padding: 0 12px;">
                        <div style="width: 100%; height: 6px; background: rgba(0, 0, 0, 0.4); border-radius: 3px; overflow: hidden;">
                            <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 3px;"></div>
                        </div>
                    </div>
                    <div style="flex: 0.5; text-align: center;">
                        <span style="font-size: 0.8rem; color: #94a3b8;">{pct:.0f}%</span>
                    </div>
                    <div style="flex: 0.7; text-align: right;">
                        <span style="padding: 3px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600;
                                    background: {color}25; color: {color}; border: 1px solid {color}50;">
                            {estado}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(datos_stock_filtrados) > items_a_renderizar:
                st.caption(f"Mostrando {items_a_renderizar} de {len(datos_stock_filtrados)} productos")
        else:
            st.info("ℹ️ No hay productos para mostrar con los filtros seleccionados")
    
    # ============================================
    # COLUMNA DERECHA: Gráfico + Alertas
    # ============================================
    with col_main_right:
        # Estado del Inventario (Gráfico)
        st.markdown("<h3>📊 Estado del Inventario</h3>", unsafe_allow_html=True)
        
        # Filtros solo para el GRÁFICO
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_grafico_agotados = st.checkbox("Agotados", value=True, key="graf_agotados")
            filtro_grafico_criticos = st.checkbox("Críticos", value=True, key="graf_criticos")
        with col_f2:
            filtro_grafico_bajos = st.checkbox("Bajos", value=True, key="graf_bajos")
            filtro_grafico_saludables = st.checkbox("Saludables", value=True, key="graf_saludables")
        
        datos = [
            {"Estado": "Agotados", "Cantidad": agotados, "Color": "#6b7280"},
            {"Estado": "Críticos", "Cantidad": criticos, "Color": "#ef4444"},
            {"Estado": "Bajos", "Cantidad": bajos, "Color": "#f59e0b"},
            {"Estado": "Saludables", "Cantidad": saludables, "Color": "#10b981"},
        ]
        
        datos_filtrados = [d for d in datos if (
            (d["Estado"] == "Agotados" and filtro_grafico_agotados) or
            (d["Estado"] == "Críticos" and filtro_grafico_criticos) or
            (d["Estado"] == "Bajos" and filtro_grafico_bajos) or
            (d["Estado"] == "Saludables" and filtro_grafico_saludables)
        )]
        
        if datos_filtrados:
            fig = go.Figure()
            
            fig.add_trace(go.Pie(
                labels=[d["Estado"] for d in datos_filtrados],
                values=[d["Cantidad"] for d in datos_filtrados],
                marker=dict(colors=[d["Color"] for d in datos_filtrados]),
                hole=0.6,
                textinfo='label+percent',
                textposition='outside',
                textfont=dict(size=14, color='white'),
                hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
            ))
            
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5, font=dict(color="white", size=10)),
                height=300,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                margin=dict(l=10, r=10, t=20, b=60),
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Centro de Notificaciones y Alertas
        st.markdown("<h4 style='color: #f59e0b; font-size: 0.9rem; margin-top: 20px;'>⚡ Centro de Notificaciones y Alertas</h4>", unsafe_allow_html=True)
        
        if criticos > 0:
            st.markdown(f"""
            <div style="padding: 10px 12px; background: rgba(239,68,68,0.15); border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(239,68,68,0.3);">
                <div style="color: #ef4444; font-weight: 600; font-size: 0.85rem;">🔴 ALERTA: {criticos} Críticos - Urgente</div>
                <div style="color: #94a3b8; font-size: 0.75rem;">Reposición urgente</div>
            </div>
            """, unsafe_allow_html=True)
        
        if bajos > 0:
            st.markdown(f"""
            <div style="padding: 10px 12px; background: rgba(245,158,11,0.15); border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(245,158,11,0.3);">
                <div style="color: #f59e0b; font-weight: 600; font-size: 0.85rem;">🟡 ALERTA: {bajos} Bajos - Revisión</div>
                <div style="color: #94a3b8; font-size: 0.75rem;">Revisar pronto</div>
            </div>
            """, unsafe_allow_html=True)
        
        if agotados > 0:
            st.markdown(f"""
            <div style="padding: 10px 12px; background: rgba(107,114,128,0.15); border-radius: 8px; margin-bottom: 6px; border: 1px solid rgba(107,114,128,0.3);">
                <div style="color: #94a3b8; font-weight: 600; font-size: 0.85rem;">⚫ AVISO: {agotados} Agotados - Sin existencias</div>
                <div style="color: #64748b; font-size: 0.75rem;">Sin existencias</div>
            </div>
            """, unsafe_allow_html=True)
        
        if criticos == 0 and bajos == 0 and agotados == 0:
            st.markdown("""
            <div style="padding: 10px 12px; background: rgba(16,185,129,0.15); border-radius: 8px; border: 1px solid rgba(16,185,129,0.3);">
                <div style="color: #10b981; font-weight: 600; font-size: 0.85rem;">✓ Todo en orden</div>
                <div style="color: #64748b; font-size: 0.75rem;">Inventario en óptimas condiciones</div>
            </div>
            """, unsafe_allow_html=True)
