"""
Página del Dashboard - Diseño Limpio
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
    """Renderiza el dashboard limpio."""
    # Placeholder para carga inicial
    if '_dashboard_loaded' not in st.session_state:
        st.session_state['_dashboard_loaded'] = False
    
    if not st.session_state['_dashboard_loaded']:
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            st.spinner("Cargando dashboard...")
    
    # Título pequeño en esquina superior izquierda
    st.markdown("""
    <div style="margin-bottom: 30px;">
        <span style="font-size: 3rem; font-weight: 600; color: #00f0ff;">MarkeTTalento</span>
    </div>
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
    
    # Métricas compactas
    metrics_cols = st.columns(4)
    
    with metrics_cols[0]:
        # Generar puntos para sparkline (valores entre 10 y 20 para que quepan bien)
        sp1 = [random.randint(12, 20) for _ in range(8)]
        points1 = " ".join([f"{i*6},{22-v}" for i, v in enumerate(sp1)])
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; display: flex; align-items: center; gap: 10px;">
            <div style="width: 36px; height: 36px; background: rgba(0,240,255,0.15); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">📦</div>
            <div style="flex: 1;">
                <div style="color: white; font-size: 0.9rem; text-transform: uppercase;">Productos en Catálogo</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #00f0ff;">{resumen.get('total_productos', 0)}</div>
                <div style="color: white;; font-size: 0.9rem;">en catálogo</div>
            </div>
            <div style="width: 50px; height: 25px;">
                <svg width="50" height="25" viewBox="0 0 50 25" style="overflow: visible;">
                    <polyline fill="none" stroke="#00f0ff" stroke-width="2" points="{points1}"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[1]:
        sp2 = [random.randint(12, 20) for _ in range(8)]
        points2 = " ".join([f"{i*6},{22-v}" for i, v in enumerate(sp2)])
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; display: flex; align-items: center; gap: 10px;">
            <div style="width: 36px; height: 36px; background: rgba(139,92,246,0.15); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">📊</div>
            <div style="flex: 1;">
                <div style="color: white;; font-size: 0.9rem; text-transform: uppercase;">Stock Total Unidades</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #8b5cf6;">{resumen.get('total_unidades', 0)}</div>
                <div style="color: white;; font-size: 0.9rem;">unidades</div>
            </div>
            <div style="width: 50px; height: 25px;">
                <svg width="50" height="25" viewBox="0 0 50 25" style="overflow: visible;">
                    <polyline fill="none" stroke="#8b5cf6" stroke-width="2" points="{points2}"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[2]:
        color_crit = "#ef4444" if criticos > 0 else "#10b981"
        sp3 = [random.randint(12, 20) for _ in range(8)]
        points3 = " ".join([f"{i*6},{22-v}" for i, v in enumerate(sp3)])
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; display: flex; align-items: center; gap: 10px;">
            <div style="width: 36px; height: 36px; background: rgba({color_crit.replace('#', '')},0.15); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">⚠️</div>
            <div style="flex: 1;">
                <div style="color: white; font-size: 0.9rem; text-transform: uppercase;">Índice Críticos</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: {color_crit};">{criticos}</div>
                <div style="color: white; font-size: 0.9rem;">requieren atención</div>
            </div>
            <div style="width: 50px; height: 25px;">
                <svg width="50" height="25" viewBox="0 0 50 25" style="overflow: visible;">
                    <polyline fill="none" stroke="{color_crit}" stroke-width="2" points="{points3}"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with metrics_cols[3]:
        valor = resumen.get("valor_total", 0)
        sp4 = [random.randint(12, 20) for _ in range(8)]
        points4 = " ".join([f"{i*6},{22-v}" for i, v in enumerate(sp4)])
        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255,255,255,0.1); border-radius: 10px; padding: 12px; display: flex; align-items: center; gap: 10px;">
            <div style="width: 36px; height: 36px; background: rgba(16,185,129,0.15); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">💰</div>
            <div style="flex: 1;">
                <div style="color: white; font-size: 0.9rem; text-transform: uppercase;">Valor Total Inventario</div>
                <div style="font-size: 1.4rem; font-weight: 700; color: #10b981;">€{valor:.0f}</div>
                <div style="color: white; font-size: 0.9rem;">en inventario</div>
            </div>
            <div style="width: 50px; height: 25px;">
                <svg width="50" height="25" viewBox="0 0 50 25" style="overflow: visible;">
                    <polyline fill="none" stroke="#10b981" stroke-width="2" points="{points4}"/>
                </svg>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # LAYOUT PRINCIPAL: Dos columnas
    col_main_left, col_main_right = st.columns([1, 1])
    
    # ============================================
    # COLUMNA IZQUIERDA: Stock por Producto
    # ============================================
    with col_main_left:
        # Header PRIMERO (arriba)
        col_header, col_search = st.columns([2, 1])
        with col_header:
            st.markdown("<h3 style='color: #00f0ff; font-size: 1.5rem; margin: 0;'>📦 Stock por Producto</h3>", unsafe_allow_html=True)
        
        with col_search:
            busqueda = st.text_input("Buscar producto", placeholder="🔍 Buscar...", label_visibility="collapsed", key="search_productos")
        
        # Filtros DESPUÉS (debajo del título)
        if 'filtros_lista' not in st.session_state:
            st.session_state['filtros_lista'] = {
                'agotados': True,
                'criticos': True,
                'bajos': True,
                'saludables': True
            }
        
        st.markdown("<p style='color: #64748b; font-size: 0.75rem; margin-bottom: 10px;'>💡 Haz clic para filtrar:</p>", unsafe_allow_html=True)
        
        # CSS para botones opacos y pequeños
        st.markdown("""
        <style>
        .filter-btn-container {
            display: flex;
            gap: 8px;
            margin-bottom: 15px;
        }
        .filter-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            border: 1px solid;
            background: rgba(30, 41, 59, 0.6);
        }
        .filter-btn:hover {
            transform: translateY(-1px);
        }
        .filter-btn.agotados { color: #9ca3af; border-color: rgba(156, 163, 175, 0.3); }
        .filter-btn.agotados:hover { background: rgba(156, 163, 175, 0.15); }
        .filter-btn.agotados.active { background: rgba(107, 114, 128, 0.25); border-color: rgba(107, 114, 128, 0.5); }
        
        .filter-btn.criticos { color: #f87171; border-color: rgba(248, 113, 113, 0.3); }
        .filter-btn.criticos:hover { background: rgba(248, 113, 113, 0.15); }
        .filter-btn.criticos.active { background: rgba(239, 68, 68, 0.25); border-color: rgba(239, 68, 68, 0.5); }
        
        .filter-btn.bajos { color: #fbbf24; border-color: rgba(251, 191, 36, 0.3); }
        .filter-btn.bajos:hover { background: rgba(251, 191, 36, 0.15); }
        .filter-btn.bajos.active { background: rgba(245, 158, 11, 0.25); border-color: rgba(245, 158, 11, 0.5); }
        
        .filter-btn.saludables { color: #34d399; border-color: rgba(52, 211, 153, 0.3); }
        .filter-btn.saludables:hover { background: rgba(52, 211, 153, 0.15); }
        .filter-btn.saludables.active { background: rgba(16, 185, 129, 0.25); border-color: rgba(16, 185, 129, 0.5); }
        </style>
        """, unsafe_allow_html=True)
        
        filtros_config = [
            ("⚫ Agotados", 'agotados', "agotados"),
            ("🔴 Críticos", 'criticos', "criticos"),
            ("🟡 Bajos", 'bajos', "bajos"),
            ("🟢 Saludables", 'saludables', "saludables"),
        ]
        
        filtros_cols = st.columns(4)
        col_idx = 0
        for label, filtro_nombre, btn_class in filtros_config:
            with filtros_cols[col_idx]:
                is_active = st.session_state['filtros_lista'][filtro_nombre]
                active_class = "active" if is_active else ""
                icon = "✓" if is_active else "○"
                
                st.markdown(f"""
                <div class="filter-btn {btn_class} {active_class}">
                    <span>{icon}</span>
                    <span>{label}</span>
                </div>
                """, unsafe_allow_html=True)
                
                # Botón invisible para detectar clicks
                if st.button(" ", key=f"btn_lista_{filtro_nombre}", label_visibility="collapsed"):
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
            
            items_a_renderizar = min(15, len(datos_stock_filtrados))
            
            for i, d in enumerate(datos_stock_filtrados[:items_a_renderizar]):
                prod = d["producto"]
                stock = d["stock"]
                max_s = d["max_s"]
                estado = d["estado"]
                pct = d["pct"]
                color = color_map.get(estado, "#10b981")
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; background: rgba(30, 41, 59, 0.5); border-radius: 8px; padding: 8px 12px; margin-bottom: 5px; border-left: 3px solid {color};">
                    <div style="display: flex; align-items: center; gap: 12px; flex: 1;">
                        <span style="font-size: 0.9rem; font-weight: 600; color: #f8fafc; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 150px;">{prod.get('nombre', 'Producto')}</span>
                        <span style="font-size: 0.9rem; font-weight: 600; color: #ffffff;">{stock}</span><span style="color: #64748b; font-size: 0.75rem;">/</span><span style="font-size: 0.85rem; color: #10b981; font-weight: 600;">{max_s}</span>
                        <div style="width: 50px;">
                            <div style="width: 100%; height: 5px; background: rgba(0, 0, 0, 0.3); border-radius: 3px; overflow: hidden;">
                                <div style="width: {pct}%; height: 100%; background: {color}; border-radius: 3px;"></div>
                            </div>
                        </div>
                        <span style="font-size: 0.7rem; color: #94a3b8; width: 35px;">{pct:.0f}%</span>
                    </div>
                    <span style="padding: 2px 8px; border-radius: 8px; font-size: 0.65rem; font-weight: 600; background: {color}20; color: {color}; border: 1px solid {color}50; margin-left: 8px;">{estado}</span>
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
        st.markdown("<h3 style='color: #00f0ff; font-size: 1.5rem; margin: 0;'>📊 Estado del Inventario</h3>", unsafe_allow_html=True)
        
        # Leyenda clickeable ARRIBA del gráfico (estilo visual tipo etiqueta, no botón)
        if 'filtros_grafico' not in st.session_state:
            st.session_state['filtros_grafico'] = {
                'agotados': True,
                'criticos': True,
                'bajos': True,
                'saludables': True
            }
        
        # Leyendas clickeables (estilo etiqueta, NO botón)
        st.markdown("<p style='color: #64748b; font-size: 0.75rem; margin: 8px 0; text-align: center;'>Haz clic en una leyenda para mostrar/ocultar:</p>", unsafe_allow_html=True)
        
        # Crear botones que parecen etiquetas de leyenda
        leyenda_cols = st.columns(4)
        
        # Agotados
        with leyenda_cols[0]:
            is_active = st.session_state['filtros_grafico']['agotados']
            label = f"⚫ Agotados" if is_active else "○ Agotados"
            if st.button(label, key="leyenda_agotados", use_container_width=True):
                st.session_state['filtros_grafico']['agotados'] = not is_active
                st.rerun()
        
        # Críticos
        with leyenda_cols[1]:
            is_active = st.session_state['filtros_grafico']['criticos']
            label = f"🔴 Críticos" if is_active else "○ Críticos"
            if st.button(label, key="leyenda_criticos", use_container_width=True):
                st.session_state['filtros_grafico']['criticos'] = not is_active
                st.rerun()
        
        # Bajos
        with leyenda_cols[2]:
            is_active = st.session_state['filtros_grafico']['bajos']
            label = f"🟡 Bajos" if is_active else "○ Bajos"
            if st.button(label, key="leyenda_bajos", use_container_width=True):
                st.session_state['filtros_grafico']['bajos'] = not is_active
                st.rerun()
        
        # Saludables
        with leyenda_cols[3]:
            is_active = st.session_state['filtros_grafico']['saludables']
            label = f"🟢 Saludables" if is_active else "○ Saludables"
            if st.button(label, key="leyenda_saludables", use_container_width=True):
                st.session_state['filtros_grafico']['saludables'] = not is_active
                st.rerun()
        
        datos = [
            {"Estado": "Agotados", "Cantidad": agotados, "Color": "#6b7280"},
            {"Estado": "Críticos", "Cantidad": criticos, "Color": "#ef4444"},
            {"Estado": "Bajos", "Cantidad": bajos, "Color": "#f59e0b"},
            {"Estado": "Saludables", "Cantidad": saludables, "Color": "#10b981"},
        ]
        
        datos_filtrados = [d for d in datos if (
            (d["Estado"] == "Agotados" and st.session_state['filtros_grafico']['agotados']) or
            (d["Estado"] == "Críticos" and st.session_state['filtros_grafico']['criticos']) or
            (d["Estado"] == "Bajos" and st.session_state['filtros_grafico']['bajos']) or
            (d["Estado"] == "Saludables" and st.session_state['filtros_grafico']['saludables'])
        ) and d["Cantidad"] > 0]
        
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
                showlegend=False,  # Usamos la leyenda HTML de arriba
                height=350,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"),
                margin=dict(l=20, r=20, t=20, b=60),  # Márgenes amplios para que el gráfico se vea completo
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Centro de Notificaciones
        st.markdown("<h4 style='color: #f59e0b; font-size: 0.9rem; margin-top: 15px;'>⚡ Centro de Notificaciones y Alertas</h4>", unsafe_allow_html=True)
        
        if criticos > 0:
            st.markdown(f"""
            <div style="padding: 8px 12px; background: rgba(239,68,68,0.12); border-radius: 6px; margin-bottom: 6px; border: 1px solid rgba(239,68,68,0.25);">
                <div style="color: #ef4444; font-weight: 600; font-size: 0.8rem;">🔴 ALERTA: {criticos} Críticos - Urgente</div>
                <div style="color: #64748b; font-size: 0.7rem;">Reposición urgente</div>
            </div>
            """, unsafe_allow_html=True)
        
        if bajos > 0:
            st.markdown(f"""
            <div style="padding: 8px 12px; background: rgba(245,158,11,0.12); border-radius: 6px; margin-bottom: 6px; border: 1px solid rgba(245,158,11,0.25);">
                <div style="color: #f59e0b; font-weight: 600; font-size: 0.8rem;">🟡 ALERTA: {bajos} Bajos - Revisión</div>
                <div style="color: #64748b; font-size: 0.7rem;">Revisar pronto</div>
            </div>
            """, unsafe_allow_html=True)
        
        if agotados > 0:
            st.markdown(f"""
            <div style="padding: 8px 12px; background: rgba(107,114,128,0.12); border-radius: 6px; margin-bottom: 6px; border: 1px solid rgba(107,114,128,0.25);">
                <div style="color: #94a3b8; font-weight: 600; font-size: 0.8rem;">⚫ AVISO: {agotados} Agotados - Sin existencias</div>
                <div style="color: #64748b; font-size: 0.7rem;">Sin existencias</div>
            </div>
            """, unsafe_allow_html=True)
        
        if criticos == 0 and bajos == 0 and agotados == 0:
            st.markdown("""
            <div style="padding: 8px 12px; background: rgba(16,185,129,0.12); border-radius: 6px; border: 1px solid rgba(16,185,129,0.25);">
                <div style="color: #10b981; font-weight: 600; font-size: 0.8rem;">✓ Todo en orden</div>
                <div style="color: #64748b; font-size: 0.7rem;">Inventario en óptimas condiciones</div>
            </div>
            """, unsafe_allow_html=True)
