"""
Página del Dashboard - Ultra Compacto con Fondo Tech
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
    """Renderiza el dashboard ultra compacto."""
    # Placeholder para carga inicial
    if '_dashboard_loaded' not in st.session_state:
        st.session_state['_dashboard_loaded'] = False
    
    if not st.session_state['_dashboard_loaded']:
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            st.spinner("Cargando dashboard...")
    
    # CSS para fondo tech con grid
    st.markdown("""
    <style>
    /* Fondo tecnológico con grid */
    .stApp {
        background: linear-gradient(135deg, #0a0e17 0%, #0f172a 50%, #1e1b4b 100%);
    }
    
    .stApp::before {
        content: '';
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-image: 
            linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
        background-size: 50px 50px;
        pointer-events: none;
        z-index: 0;
    }
    
    /* Hero Section Compacto */
    .hero-mini {
        background: linear-gradient(135deg, rgba(0,240,255,0.08) 0%, rgba(139,92,246,0.08) 50%, rgba(236,72,153,0.08) 100%);
        padding: 20px 30px;
        border-radius: 16px;
        border: 1px solid rgba(0,240,255,0.2);
        margin-bottom: 15px;
        text-align: center;
        position: relative;
    }
    
    .hero-mini::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, transparent, #00f0ff, transparent);
    }
    
    .hero-icon {
        font-size: 2.5rem;
        margin-bottom: 8px;
    }
    
    .hero-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0 0 5px 0;
        background: linear-gradient(90deg, #00f0ff, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        letter-spacing: 2px;
    }
    
    .hero-subtitle {
        color: #64748b;
        font-size: 0.9rem;
        margin: 0 0 12px 0;
    }
    
    .hero-subtitle span {
        color: #00f0ff;
    }
    
    .hero-tags {
        display: flex;
        justify-content: center;
        gap: 10px;
    }
    
    .hero-tag {
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    .hero-tag.cyan {
        background: rgba(0,240,255,0.15);
        border: 1px solid rgba(0,240,255,0.4);
        color: #00f0ff;
    }
    
    .hero-tag.purple {
        background: rgba(139,92,246,0.15);
        border: 1px solid rgba(139,92,246,0.4);
        color: #8b5cf6;
    }
    
    .hero-tag.green {
        background: rgba(16,185,129,0.15);
        border: 1px solid rgba(16,185,129,0.4);
        color: #10b981;
    }
    
    /* Tarjetas de métricas compactas */
    .metric-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 12px;
        padding: 12px 15px;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .metric-icon {
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .metric-icon.cyan {
        background: rgba(0,240,255,0.15);
    }
    
    .metric-icon.purple {
        background: rgba(139,92,246,0.15);
    }
    
    .metric-icon.red {
        background: rgba(239,68,68,0.15);
    }
    
    .metric-icon.green {
        background: rgba(16,185,129,0.15);
    }
    
    .metric-content {
        flex: 1;
    }
    
    .metric-label {
        color: #64748b;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 2px;
    }
    
    .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        margin-bottom: 2px;
    }
    
    .metric-sublabel {
        color: #475569;
        font-size: 0.7rem;
    }
    
    .metric-sparkline {
        width: 60px;
        height: 30px;
    }
    
    /* Secciones */
    .section-title {
        color: #00f0ff;
        font-size: 0.95rem;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .section-subtitle {
        color: #64748b;
        font-size: 0.75rem;
        margin-bottom: 12px;
    }
    </style>
    
    <!-- Hero Section -->
    <div class="hero-mini">
        <div class="hero-icon">📦</div>
        <h1 class="hero-title">MarkeTTalento</h1>
        <p class="hero-subtitle">Sistema de Inventario Inteligente con <span>Visión Artificial</span></p>
        <div class="hero-tags">
            <span class="hero-tag cyan">🤖 ML & IA</span>
            <span class="hero-tag purple">📊 Analytics</span>
            <span class="hero-tag green">🔮 Predicciones</span>
        </div>
    </div>
    
    <p style="color: #475569; font-size: 0.8rem; margin-bottom: 15px;">Dashboard</p>
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
    
    # Métricas compactas con sparklines
    metrics_cols = st.columns(4)
    
    with metrics_cols[0]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon cyan">📦</div>
            <div class="metric-content">
                <div class="metric-label">Productos en Catálogo</div>
                <div class="metric-value" style="color: #00f0ff;">{resumen.get('total_productos', 0)}</div>
                <div class="metric-sublabel">en catálogo</div>
            </div>
            <svg class="metric-sparkline" viewBox="0 0 60 30">
                <polyline fill="none" stroke="#00f0ff" stroke-width="2" points="0,{30-spark_productos[0]*0.5} 6,{30-spark_productos[1]*0.5} 12,{30-spark_productos[2]*0.5} 18,{30-spark_productos[3]*0.5} 24,{30-spark_productos[4]*0.5} 30,{30-spark_productos[5]*0.5} 36,{30-spark_productos[6]*0.5} 42,{30-spark_productos[7]*0.5} 48,{30-spark_productos[8]*0.5} 54,{30-spark_productos[9]*0.5}"/>
                <polygon fill="rgba(0,240,255,0.1)" stroke="none" points="0,30 0,{30-spark_productos[0]*0.5} 6,{30-spark_productos[1]*0.5} 12,{30-spark_productos[2]*0.5} 18,{30-spark_productos[3]*0.5} 24,{30-spark_productos[4]*0.5} 30,{30-spark_productos[5]*0.5} 36,{30-spark_productos[6]*0.5} 42,{30-spark_productos[7]*0.5} 48,{30-spark_productos[8]*0.5} 54,{30-spark_productos[9]*0.5} 54,30"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[1]:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon purple">📊</div>
            <div class="metric-content">
                <div class="metric-label">Stock Total Unidades</div>
                <div class="metric-value" style="color: #8b5cf6;">{resumen.get('total_unidades', 0)}</div>
                <div class="metric-sublabel">unidades</div>
            </div>
            <svg class="metric-sparkline" viewBox="0 0 60 30">
                <polyline fill="none" stroke="#8b5cf6" stroke-width="2" points="0,{30-spark_stock[0]*0.5} 6,{30-spark_stock[1]*0.5} 12,{30-spark_stock[2]*0.5} 18,{30-spark_stock[3]*0.5} 24,{30-spark_stock[4]*0.5} 30,{30-spark_stock[5]*0.5} 36,{30-spark_stock[6]*0.5} 42,{30-spark_stock[7]*0.5} 48,{30-spark_stock[8]*0.5} 54,{30-spark_stock[9]*0.5}"/>
                <polygon fill="rgba(139,92,246,0.1)" stroke="none" points="0,30 0,{30-spark_stock[0]*0.5} 6,{30-spark_stock[1]*0.5} 12,{30-spark_stock[2]*0.5} 18,{30-spark_stock[3]*0.5} 24,{30-spark_stock[4]*0.5} 30,{30-spark_stock[5]*0.5} 36,{30-spark_stock[6]*0.5} 42,{30-spark_stock[7]*0.5} 48,{30-spark_stock[8]*0.5} 54,{30-spark_stock[9]*0.5} 54,30"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[2]:
        color_crit = "#ef4444" if criticos > 0 else "#10b981"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon red">⚠️</div>
            <div class="metric-content">
                <div class="metric-label">Índice Críticos</div>
                <div class="metric-value" style="color: {color_crit};">{criticos}</div>
                <div class="metric-sublabel">requieren atención</div>
            </div>
            <svg class="metric-sparkline" viewBox="0 0 60 30">
                <polyline fill="none" stroke="{color_crit}" stroke-width="2" points="0,{30-spark_criticos[0]*0.5} 6,{30-spark_criticos[1]*0.5} 12,{30-spark_criticos[2]*0.5} 18,{30-spark_criticos[3]*0.5} 24,{30-spark_criticos[4]*0.5} 30,{30-spark_criticos[5]*0.5} 36,{30-spark_criticos[6]*0.5} 42,{30-spark_criticos[7]*0.5} 48,{30-spark_criticos[8]*0.5} 54,{30-spark_criticos[9]*0.5}"/>
                <polygon fill="rgba(239,68,68,0.1)" stroke="none" points="0,30 0,{30-spark_criticos[0]*0.5} 6,{30-spark_criticos[1]*0.5} 12,{30-spark_criticos[2]*0.5} 18,{30-spark_criticos[3]*0.5} 24,{30-spark_criticos[4]*0.5} 30,{30-spark_criticos[5]*0.5} 36,{30-spark_criticos[6]*0.5} 42,{30-spark_criticos[7]*0.5} 48,{30-spark_criticos[8]*0.5} 54,{30-spark_criticos[9]*0.5} 54,30"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[3]:
        valor = resumen.get("valor_total", 0)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon green">💰</div>
            <div class="metric-content">
                <div class="metric-label">Valor Total Inventario</div>
                <div class="metric-value" style="color: #10b981;">€{valor:.0f}</div>
                <div class="metric-sublabel">en inventario</div>
            </div>
            <svg class="metric-sparkline" viewBox="0 0 60 30">
                <polyline fill="none" stroke="#10b981" stroke-width="2" points="0,{30-spark_valor[0]*0.5} 6,{30-spark_valor[1]*0.5} 12,{30-spark_valor[2]*0.5} 18,{30-spark_valor[3]*0.5} 24,{30-spark_valor[4]*0.5} 30,{30-spark_valor[5]*0.5} 36,{30-spark_valor[6]*0.5} 42,{30-spark_valor[7]*0.5} 48,{30-spark_valor[8]*0.5} 54,{30-spark_valor[9]*0.5}"/>
                <polygon fill="rgba(16,185,129,0.1)" stroke="none" points="0,30 0,{30-spark_valor[0]*0.5} 6,{30-spark_valor[1]*0.5} 12,{30-spark_valor[2]*0.5} 18,{30-spark_valor[3]*0.5} 24,{30-spark_valor[4]*0.5} 30,{30-spark_valor[5]*0.5} 36,{30-spark_valor[6]*0.5} 42,{30-spark_valor[7]*0.5} 48,{30-spark_valor[8]*0.5} 54,{30-spark_valor[9]*0.5} 54,30"/>
            </svg>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # LAYOUT PRINCIPAL: Dos columnas (izquierda 2/3, derecha 1/3)
    col_main_left, col_main_right = st.columns([2, 1])
    
    # ============================================
    # COLUMNA IZQUIERDA: Stock por Producto
    # ============================================
    with col_main_left:
        # Header compacto
        col_header, col_search = st.columns([2, 1])
        with col_header:
            st.markdown('<div class="section-title">📦 Stock por Producto</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-subtitle">Visualización en tiempo real del inventario</div>', unsafe_allow_html=True)
        
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
        
        st.markdown('<div class="section-subtitle">💡 Haz clic para filtrar:</div>', unsafe_allow_html=True)
        
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
        
        # Mostrar tabla
        if datos_stock_filtrados:
            color_map = {
                "Agotado": "#6b7280",
                "Crítico": "#ef4444",
                "Bajo": "#f59e0b",
                "Saludable": "#10b981"
            }
            
            items_a_renderizar = min(15, len(datos_stock_filtrados))
            
            for i, d in enumerate(datos_stock_filtrados[:items_a_renderizar]):
                prod = d["producto"]
                stock = d["stock"]
                max_s = d["max_s"]
                estado = d["estado"]
                pct = d["pct"]
                color = color_map.get(estado, "#10b981")
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; background: rgba(30, 41, 59, 0.4); 
                            border-radius: 8px; padding: 8px 12px; margin-bottom: 5px;
                            border-left: 3px solid {color};">
                    <div style="width: 28px; height: 28px; background: rgba(255,255,255,0.08); border-radius: 5px; 
                                display: flex; align-items: center; justify-content: center; margin-right: 10px;">
                        <span style="font-size: 0.9rem;">📦</span>
                    </div>
                    <div style="flex: 2; min-width: 80px;">
                        <div style="font-size: 0.85rem; font-weight: 600; color: #f8fafc;">{prod.get('nombre', 'Producto')}</div>
                    </div>
                    <div style="flex: 0.7; text-align: center;">
                        <span style="font-size: 1rem; font-weight: 600; color: #ffffff;">{stock}</span>
                        <span style="color: #64748b; font-size: 0.7rem;">/</span>
                        <span style="font-size: 0.8rem; color: #64748b;">{max_s}</span>
                    </div>
                    <div style="flex: 1; padding: 0 10px;">
                        <div style="width: 100%; height: 5px; background: rgba(0, 0, 0, 0.3); border-radius: 3px; overflow: hidden;">
                            <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 3px;"></div>
                        </div>
                    </div>
                    <div style="flex: 0.4; text-align: center;">
                        <span style="font-size: 0.75rem; color: #94a3b8;">{pct:.0f}%</span>
                    </div>
                    <div style="flex: 0.6; text-align: right;">
                        <span style="padding: 2px 6px; border-radius: 8px; font-size: 0.65rem; font-weight: 600;
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
        st.markdown('<div class="section-title">📊 Estado del Inventario</div>', unsafe_allow_html=True)
        
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
                textfont=dict(size=12, color='white'),
                hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
            ))
            
            fig.update_layout(
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5, font=dict(color="white", size=9)),
                height=220,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                margin=dict(l=5, r=5, t=15, b=40),
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Centro de Notificaciones
        st.markdown('<div class="section-title" style="margin-top: 10px;">⚡ Centro de Notificaciones y Alertas</div>', unsafe_allow_html=True)
        
        if criticos > 0:
            st.markdown(f"""
            <div style="padding: 8px 10px; background: rgba(239,68,68,0.12); border-radius: 6px; margin-bottom: 5px; border: 1px solid rgba(239,68,68,0.25);">
                <div style="color: #ef4444; font-weight: 600; font-size: 0.75rem;">🔴 ALERTA: {criticos} Críticos - Urgente</div>
                <div style="color: #64748b; font-size: 0.65rem;">Reposición urgente</div>
            </div>
            """, unsafe_allow_html=True)
        
        if bajos > 0:
            st.markdown(f"""
            <div style="padding: 8px 10px; background: rgba(245,158,11,0.12); border-radius: 6px; margin-bottom: 5px; border: 1px solid rgba(245,158,11,0.25);">
                <div style="color: #f59e0b; font-weight: 600; font-size: 0.75rem;">🟡 ALERTA: {bajos} Bajos - Revisión</div>
                <div style="color: #64748b; font-size: 0.65rem;">Revisar pronto</div>
            </div>
            """, unsafe_allow_html=True)
        
        if agotados > 0:
            st.markdown(f"""
            <div style="padding: 8px 10px; background: rgba(107,114,128,0.12); border-radius: 6px; margin-bottom: 5px; border: 1px solid rgba(107,114,128,0.25);">
                <div style="color: #94a3b8; font-weight: 600; font-size: 0.75rem;">⚫ AVISO: {agotados} Agotados - Sin existencias</div>
                <div style="color: #64748b; font-size: 0.65rem;">Sin existencias</div>
            </div>
            """, unsafe_allow_html=True)
        
        if criticos == 0 and bajos == 0 and agotados == 0:
            st.markdown("""
            <div style="padding: 8px 10px; background: rgba(16,185,129,0.12); border-radius: 6px; border: 1px solid rgba(16,185,129,0.25);">
                <div style="color: #10b981; font-weight: 600; font-size: 0.75rem;">✓ Todo en orden</div>
                <div style="color: #64748b; font-size: 0.65rem;">Inventario en óptimas condiciones</div>
            </div>
            """, unsafe_allow_html=True)
