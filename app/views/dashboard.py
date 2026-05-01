"""
Página del Dashboard - Fondo Futurista
"""
import streamlit as st
import plotly.graph_objects as go
import hashlib
import json
import random
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
    datos_simples = []
    for inv in inventarios:
        datos_simples.append(f"{inv.get('producto_id')}:{inv.get('cantidad')}")
    datos_str = "|".join(sorted(datos_simples))
    return hashlib.md5(datos_str.encode()).hexdigest()


def _generar_sparkline_data(trend="up"):
    """Genera datos para sparkline de ejemplo."""
    if trend == "up":
        return [random.randint(40, 60) + i*2 for i in range(10)]
    elif trend == "down":
        return [random.randint(60, 80) - i*2 for i in range(10)]
    else:
        return [random.randint(45, 55) for i in range(10)]


def render():
    """Renderiza el dashboard con fondo futurista."""
    # Placeholder para carga inicial
    if '_dashboard_loaded' not in st.session_state:
        st.session_state['_dashboard_loaded'] = False
    
    if not st.session_state['_dashboard_loaded']:
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            st.spinner("Cargando dashboard...")
    
    # FONDO FUTURISTA CON GRID Y PARTICULAS
    st.markdown("""
    <style>
    /* Fondo base oscuro futurista */
    .stApp {
        background: linear-gradient(135deg, #050810 0%, #0a0f1e 30%, #0d1321 70%, #0a0e1a 100%);
    }
    
    /* Grid tecnológico */
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            linear-gradient(rgba(0, 240, 255, 0.04) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.04) 1px, transparent 1px);
        background-size: 40px 40px;
        pointer-events: none;
        z-index: 0;
    }
    
    /* Efecto de vignette */
    .stApp::after {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: radial-gradient(ellipse at center, transparent 0%, rgba(5,8,16,0.4) 100%);
        pointer-events: none;
        z-index: 0;
    }
    
    /* Líneas de conexión decorativas */
    .tech-lines {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: none;
        z-index: 0;
        background: 
            linear-gradient(45deg, transparent 48%, rgba(0,240,255,0.02) 49%, rgba(0,240,255,0.02) 51%, transparent 52%),
            linear-gradient(-45deg, transparent 48%, rgba(139,92,246,0.02) 49%, rgba(139,92,246,0.02) 51%, transparent 52%);
        background-size: 100px 100px;
    }
    
    /* Header esquina */
    .header-corner {
        position: fixed;
        top: 10px;
        right: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        z-index: 100;
        padding: 8px 15px;
        background: rgba(10, 15, 30, 0.8);
        border: 1px solid rgba(0, 240, 255, 0.2);
        border-radius: 20px;
        backdrop-filter: blur(10px);
    }
    
    .header-corner-icon {
        font-size: 1.2rem;
    }
    
    .header-corner-text {
        font-size: 0.9rem;
        font-weight: 600;
        background: linear-gradient(90deg, #00f0ff, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    /* Tarjetas de métricas ultra compactas */
    .metric-micro {
        background: rgba(20, 25, 40, 0.6);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        padding: 10px 12px;
        display: flex;
        align-items: center;
        gap: 10px;
        backdrop-filter: blur(10px);
    }
    
    .metric-micro-icon {
        width: 32px;
        height: 32px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
    }
    
    .metric-micro-content {
        flex: 1;
    }
    
    .metric-micro-label {
        color: #64748b;
        font-size: 0.6rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 1px;
    }
    
    .metric-micro-value {
        font-size: 1.2rem;
        font-weight: 700;
        line-height: 1;
    }
    
    .metric-micro-sublabel {
        color: #475569;
        font-size: 0.6rem;
    }
    
    .metric-micro-spark {
        width: 45px;
        height: 22px;
    }
    
    /* Titulos de sección */
    .section-micro {
        color: #00f0ff;
        font-size: 0.85rem;
        font-weight: 600;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    
    .section-micro-sub {
        color: #64748b;
        font-size: 0.7rem;
        margin-bottom: 10px;
    }
    
    /* Botones de filtro compactos */
    .filter-pill {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.7rem;
        font-weight: 500;
        border: 1px solid;
        cursor: pointer;
        transition: all 0.2s;
    }
    
    /* Productos lista */
    .product-row {
        display: flex;
        align-items: center;
        background: rgba(20, 25, 40, 0.4);
        border-radius: 6px;
        padding: 6px 10px;
        margin-bottom: 4px;
        border-left: 2px solid;
        font-size: 0.8rem;
    }
    
    .product-icon {
        width: 24px;
        height: 24px;
        background: rgba(255,255,255,0.06);
        border-radius: 4px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 8px;
        font-size: 0.8rem;
    }
    
    /* Alertas compactas */
    .alert-micro {
        padding: 6px 8px;
        border-radius: 5px;
        margin-bottom: 4px;
        border: 1px solid;
        font-size: 0.7rem;
    }
    </style>
    
    <!-- Líneas decorativas de fondo -->
    <div class="tech-lines"></div>
    
    <!-- Header en esquina -->
    <div class="header-corner">
        <span class="header-corner-icon">📦</span>
        <span class="header-corner-text">MarkeTTalento</span>
    </div>
    
    <div style="margin-top: 40px;"></div>
    """, unsafe_allow_html=True)
    
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
    
    # Generar datos de sparkline
    spark_productos = _generar_sparkline_data("up")
    spark_stock = _generar_sparkline_data("up")
    spark_criticos = _generar_sparkline_data("down")
    spark_valor = _generar_sparkline_data("up")
    
    # Métricas ultra compactas
    metrics_cols = st.columns(4)
    
    with metrics_cols[0]:
        st.markdown(f"""
        <div class="metric-micro">
            <div class="metric-micro-icon" style="background: rgba(0,240,255,0.12);">📦</div>
            <div class="metric-micro-content">
                <div class="metric-micro-label">Productos en Catálogo</div>
                <div class="metric-micro-value" style="color: #00f0ff;">{resumen.get('total_productos', 0)}</div>
                <div class="metric-micro-sublabel">en catálogo</div>
            </div>
            <svg class="metric-micro-spark" viewBox="0 0 45 22">
                <polyline fill="none" stroke="#00f0ff" stroke-width="1.5" points="0,{22-spark_productos[0]*0.4} 5,{22-spark_productos[1]*0.4} 10,{22-spark_productos[2]*0.4} 15,{22-spark_productos[3]*0.4} 20,{22-spark_productos[4]*0.4} 25,{22-spark_productos[5]*0.4} 30,{22-spark_productos[6]*0.4} 35,{22-spark_productos[7]*0.4} 40,{22-spark_productos[8]*0.4} 45,{22-spark_productos[9]*0.4}"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[1]:
        st.markdown(f"""
        <div class="metric-micro">
            <div class="metric-micro-icon" style="background: rgba(139,92,246,0.12);">📊</div>
            <div class="metric-micro-content">
                <div class="metric-micro-label">Stock Total Unidades</div>
                <div class="metric-micro-value" style="color: #8b5cf6;">{resumen.get('total_unidades', 0)}</div>
                <div class="metric-micro-sublabel">unidades</div>
            </div>
            <svg class="metric-micro-spark" viewBox="0 0 45 22">
                <polyline fill="none" stroke="#8b5cf6" stroke-width="1.5" points="0,{22-spark_stock[0]*0.4} 5,{22-spark_stock[1]*0.4} 10,{22-spark_stock[2]*0.4} 15,{22-spark_stock[3]*0.4} 20,{22-spark_stock[4]*0.4} 25,{22-spark_stock[5]*0.4} 30,{22-spark_stock[6]*0.4} 35,{22-spark_stock[7]*0.4} 40,{22-spark_stock[8]*0.4} 45,{22-spark_stock[9]*0.4}"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[2]:
        color_crit = "#ef4444" if criticos > 0 else "#10b981"
        st.markdown(f"""
        <div class="metric-micro">
            <div class="metric-micro-icon" style="background: rgba({color_crit.replace('#', '')},0.12);">⚠️</div>
            <div class="metric-micro-content">
                <div class="metric-micro-label">Índice Críticos</div>
                <div class="metric-micro-value" style="color: {color_crit};">{criticos}</div>
                <div class="metric-micro-sublabel">requieren atención</div>
            </div>
            <svg class="metric-micro-spark" viewBox="0 0 45 22">
                <polyline fill="none" stroke="{color_crit}" stroke-width="1.5" points="0,{22-spark_criticos[0]*0.4} 5,{22-spark_criticos[1]*0.4} 10,{22-spark_criticos[2]*0.4} 15,{22-spark_criticos[3]*0.4} 20,{22-spark_criticos[4]*0.4} 25,{22-spark_criticos[5]*0.4} 30,{22-spark_criticos[6]*0.4} 35,{22-spark_criticos[7]*0.4} 40,{22-spark_criticos[8]*0.4} 45,{22-spark_criticos[9]*0.4}"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[3]:
        valor = resumen.get("valor_total", 0)
        st.markdown(f"""
        <div class="metric-micro">
            <div class="metric-micro-icon" style="background: rgba(16,185,129,0.12);">💰</div>
            <div class="metric-micro-content">
                <div class="metric-micro-label">Valor Total Inventario</div>
                <div class="metric-micro-value" style="color: #10b981;">€{valor:.0f}</div>
                <div class="metric-micro-sublabel">en inventario</div>
            </div>
            <svg class="metric-micro-spark" viewBox="0 0 45 22">
                <polyline fill="none" stroke="#10b981" stroke-width="1.5" points="0,{22-spark_valor[0]*0.4} 5,{22-spark_valor[1]*0.4} 10,{22-spark_valor[2]*0.4} 15,{22-spark_valor[3]*0.4} 20,{22-spark_valor[4]*0.4} 25,{22-spark_valor[5]*0.4} 30,{22-spark_valor[6]*0.4} 35,{22-spark_valor[7]*0.4} 40,{22-spark_valor[8]*0.4} 45,{22-spark_valor[9]*0.4}"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin: 12px 0; border-top: 1px solid rgba(255,255,255,0.06);'></div>", unsafe_allow_html=True)
    
    # LAYOUT PRINCIPAL: Dos columnas
    col_main_left, col_main_right = st.columns([2, 1])
    
    # ============================================
    # COLUMNA IZQUIERDA: Stock por Producto
    # ============================================
    with col_main_left:
        # Header compacto
        col_header, col_search = st.columns([2, 1])
        with col_header:
            st.markdown('<div class="section-micro">📦 Stock por Producto</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-micro-sub">Visualización en tiempo real del inventario</div>', unsafe_allow_html=True)
        
        with col_search:
            busqueda = st.text_input("", placeholder="🔍 Buscar...", label_visibility="collapsed", key="search_productos")
        
        # Filtros para la lista
        if 'filtros_lista' not in st.session_state:
            st.session_state['filtros_lista'] = {
                'agotados': True,
                'criticos': True,
                'bajos': True,
                'saludables': True
            }
        
        st.markdown('<div class="section-micro-sub">💡 Haz clic para filtrar:</div>', unsafe_allow_html=True)
        
        # Filtros clickeables
        filtros_config = [
            ("⚫ Agotados", 'agotados', "#6b7280"),
            ("🔴 Críticos", 'criticos', "#ef4444"),
            ("🟡 Bajos", 'bajos', "#f59e0b"),
            ("🟢 Saludables", 'saludables', "#10b981"),
        ]
        
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
        
        # Filtrar datos
        datos_stock_filtrados = []
        for d in datos_stock:
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
            
            if busqueda and busqueda.strip():
                nombre_prod = d["producto"].get('nombre', '').lower()
                if busqueda.lower() not in nombre_prod:
                    continue
            
            datos_stock_filtrados.append(d)
        
        # Ordenar
        estado_orden = {"Crítico": 0, "Agotado": 1, "Bajo": 2, "Saludable": 3}
        datos_stock_filtrados.sort(key=lambda x: (estado_orden.get(x["estado"], 3), x["producto"].get("nombre", "")))
        
        # Mostrar lista
        if datos_stock_filtrados:
            color_map = {
                "Agotado": "#6b7280",
                "Crítico": "#ef4444",
                "Bajo": "#f59e0b",
                "Saludable": "#10b981"
            }
            
            items_a_renderizar = min(12, len(datos_stock_filtrados))
            
            for i, d in enumerate(datos_stock_filtrados[:items_a_renderizar]):
                prod = d["producto"]
                stock = d["stock"]
                max_s = d["max_s"]
                estado = d["estado"]
                pct = d["pct"]
                color = color_map.get(estado, "#10b981")
                
                st.markdown(f"""
                <div class="product-row" style="border-left-color: {color};">
                    <div class="product-icon">📦</div>
                    <div style="flex: 2; min-width: 80px;">
                        <span style="font-weight: 600; color: #f8fafc;">{prod.get('nombre', 'Producto')}</span>
                    </div>
                    <div style="flex: 0.7; text-align: center;">
                        <span style="font-weight: 600; color: #ffffff;">{stock}</span>
                        <span style="color: #64748b; font-size: 0.7rem;">/</span>
                        <span style="font-size: 0.75rem; color: #64748b;">{max_s}</span>
                    </div>
                    <div style="flex: 1; padding: 0 10px;">
                        <div style="width: 100%; height: 4px; background: rgba(0, 0, 0, 0.3); border-radius: 2px; overflow: hidden;">
                            <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="flex: 0.4; text-align: center;">
                        <span style="font-size: 0.7rem; color: #94a3b8;">{pct:.0f}%</span>
                    </div>
                    <div style="flex: 0.6; text-align: right;">
                        <span style="padding: 2px 6px; border-radius: 6px; font-size: 0.6rem; font-weight: 600;
                                    background: {color}20; color: {color}; border: 1px solid {color}40;">
                            {estado}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            if len(datos_stock_filtrados) > items_a_renderizar:
                st.caption(f"Mostrando {items_a_renderizar} de {len(datos_stock_filtrados)} productos")
        else:
            st.info("No hay productos para mostrar")
    
    # ============================================
    # COLUMNA DERECHA: Gráfico + Alertas
    # ============================================
    with col_main_right:
        # Estado del Inventario
        st.markdown('<div class="section-micro">📊 Estado del Inventario</div>', unsafe_allow_html=True)
        
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
                textfont=dict(size=11, color='white'),
                hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
            ))
            
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color="white", size=9)),
                height=200,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                margin=dict(l=5, r=5, t=10, b=35),
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Centro de Notificaciones
        st.markdown('<div class="section-micro" style="margin-top: 8px;">⚡ Centro de Notificaciones y Alertas</div>', unsafe_allow_html=True)
        
        if criticos > 0:
            st.markdown(f"""
            <div class="alert-micro" style="background: rgba(239,68,68,0.1); border-color: rgba(239,68,68,0.3);">
                <div style="color: #ef4444; font-weight: 600;">🔴 ALERTA: {criticos} Críticos - Urgente</div>
                <div style="color: #64748b; font-size: 0.65rem;">Reposición urgente</div>
            </div>
            """, unsafe_allow_html=True)
        
        if bajos > 0:
            st.markdown(f"""
            <div class="alert-micro" style="background: rgba(245,158,11,0.1); border-color: rgba(245,158,11,0.3);">
                <div style="color: #f59e0b; font-weight: 600;">🟡 ALERTA: {bajos} Bajos - Revisión</div>
                <div style="color: #64748b; font-size: 0.65rem;">Revisar pronto</div>
            </div>
            """, unsafe_allow_html=True)
        
        if agotados > 0:
            st.markdown(f"""
            <div class="alert-micro" style="background: rgba(107,114,128,0.1); border-color: rgba(107,114,128,0.3);">
                <div style="color: #94a3b8; font-weight: 600;">⚫ AVISO: {agotados} Agotados</div>
                <div style="color: #64748b; font-size: 0.65rem;">Sin existencias</div>
            </div>
            """, unsafe_allow_html=True)
        
        if criticos == 0 and bajos == 0 and agotados == 0:
            st.markdown("""
            <div class="alert-micro" style="background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3);">
                <div style="color: #10b981; font-weight: 600;">✓ Todo en orden</div>
                <div style="color: #64748b; font-size: 0.65rem;">Inventario óptimo</div>
            </div>
            """, unsafe_allow_html=True)
