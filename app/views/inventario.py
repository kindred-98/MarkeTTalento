"""
Página de Inventario - Optimizada
"""
import streamlit as st
import pandas as pd
import hashlib
import json
from app.utils.api import api_get, api_post
from app.utils.helpers import to_excel
from app.logic.inventario import (
    calcular_estado_stock, 
    preparar_datos_inventario,
    filtrar_por_estado,
    ordenar_inventario
)
from app.components.stock_badge import render_stock_badge


@st.cache_data(ttl=120, show_spinner=False)
def _get_inventario_data():
    """Cachea datos de inventario y productos."""
    inventarios = api_get("/api/v1/inventario", use_cache=False)
    productos = api_get("/api/v1/productos", use_cache=False)
    return inventarios, productos


@st.cache_data(ttl=60, show_spinner=False)
def _procesar_inventario(inventarios_json: str, productos_json: str, filtro_estado: str, orden: str):
    """Cachea el procesamiento de datos de inventario."""
    inventarios = json.loads(inventarios_json)
    productos = json.loads(productos_json)
    
    datos_inv = preparar_datos_inventario(inventarios, productos)
    
    if filtro_estado != "Todos":
        datos_inv = [d for d in datos_inv if d["estado"] == filtro_estado]
    
    datos_inv = ordenar_inventario(datos_inv, orden)
    
    return datos_inv


def _generar_hash_datos(inventarios, productos) -> str:
    """Genera un hash simple de los datos."""
    datos_simples = []
    for inv in inventarios:
        datos_simples.append(f"{inv.get('producto_id')}:{inv.get('cantidad')}")
    return hashlib.md5(str(len(datos_simples)).encode()).hexdigest()


def render():
    """Renderiza la página de inventario optimizada."""
    st.markdown("<h2>📊 Control de Inventario</h2>", unsafe_allow_html=True)
    
    # Placeholder para carga
    loading = st.empty()
    with loading:
        st.spinner("Cargando inventario...")
    
    # Obtener datos con cache
    inventarios, productos = _get_inventario_data()
    
    # Limpiar loading
    loading.empty()
    
    # === ACTUALIZAR STOCK ===
    with st.expander("✏️ Actualizar stock", expanded=False):
        with st.form("actualizar_stock"):
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                prod_id = st.number_input("ID del producto", min_value=1, key="prod_id_form")
            with col2:
                nueva_cantidad = st.number_input("Nueva cantidad", min_value=0, key="nueva_cant_form")
            with col3:
                ubicacion = st.text_input("Ubicación", key="ubicacion_form")
            
            submitted = st.form_submit_button("🔄 Actualizar")
            if submitted:
                result = api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nueva_cantidad, "ubicacion": ubicacion})
                if result:
                    # Limpiar cache
                    _get_inventario_data.clear()
                    _procesar_inventario.clear()
                    st.success("✅ Stock actualizado")
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar")
    
    st.markdown("---")
    
    # === FILTROS ===
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_estado_inv = st.selectbox(
            "Filtrar por estado", 
            ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"], 
            key="filtro_inv_estado"
        )
    with col_f2:
        ordenar_inv = st.selectbox(
            "Ordenar por", 
            ["Producto (A-Z)", "Stock (mayor)", "Stock (menor)"], 
            key="ordenar_inv"
        )
    
    # Procesar datos con cache
    inv_json = json.dumps(inventarios)
    prod_json = json.dumps(productos)
    datos_inv = _procesar_inventario(inv_json, prod_json, filtro_estado_inv, ordenar_inv)
    
    # Contador
    st.markdown(f"""
    <div style="padding: 10px 15px; background: rgba(16,185,129,0.1); border-radius: 10px; margin-bottom: 15px;">
        <span style="color: #10b981; font-weight: 600;">{len(datos_inv)}</span>
        <span style="color: #94a3b8;"> productos</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Exportar Excel
    if datos_inv:
        # Preparar DataFrame con cache
        df_key = f"df_inv_{len(datos_inv)}_{filtro_estado_inv}"
        if df_key not in st.session_state:
            df_inv = pd.DataFrame([{
                "Producto": d["producto"].get("nombre"),
                "SKU": d["producto"].get("sku"),
                "Stock": d["stock"],
                "Stock Mín": d["min_s"],
                "Stock Máx": d["max_s"],
                "Ubicación": d["ubicacion"],
                "Estado": d["estado"]
            } for d in datos_inv])
            st.session_state[df_key] = df_inv
        else:
            df_inv = st.session_state[df_key]
        
        excel_inv = to_excel(df_inv)
        col_exp, _ = st.columns([1, 3])
        with col_exp:
            st.download_button(
                "📥 Exportar Excel",
                data=excel_inv,
                file_name="inventario.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_excel_inv"
            )
    
    # Lista de inventario con paginación lazy
    if datos_inv:
        # Colores pre-calculados
        colores = {
            "Agotado": "#6b7280",
            "Crítico": "#ef4444",
            "Bajo": "#f59e0b",
            "Saludable": "#10b981"
        }
        fondos = {
            "Agotado": "rgba(107,114,128,0.2)",
            "Crítico": "rgba(239,68,68,0.2)",
            "Bajo": "rgba(245,158,11,0.2)",
            "Saludable": "rgba(16,185,129,0.2)"
        }
        
        # Paginación
        items_por_pagina = 12
        if 'inv_pagina' not in st.session_state:
            st.session_state['inv_pagina'] = 1
        
        total_paginas = max(1, (len(datos_inv) + items_por_pagina - 1) // items_por_pagina)
        pagina_actual = min(st.session_state['inv_pagina'], total_paginas)
        
        inicio = (pagina_actual - 1) * items_por_pagina
        fin = min(inicio + items_por_pagina, len(datos_inv))
        
        datos_pagina = datos_inv[inicio:fin]
        
        # Renderizar items
        for d in datos_pagina:
            prod = d["producto"]
            stock = d["stock"]
            estado = d["estado"]
            prod_id = prod.get("id")
            color = colores.get(estado, "#10b981")
            bg = fondos.get(estado, "rgba(16,185,129,0.2)")
            
            col_card, col_btns = st.columns([4, 1])
            
            with col_card:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8) 0%, rgba(26,35,50,0.6) 100%); border: 1px solid rgba(0,240,255,0.15); border-radius: 16px; padding: 18px; margin-bottom: 12px; border-left: 4px solid {color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-size: 1.1rem; font-weight: 600; color: #f1f5f9;">{prod.get("nombre", "Producto")}</div>
                        <span style="padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; background: {bg}; color: {color};">{estado}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;">
                        <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Stock actual</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #f1f5f9; margin-top: 4px;">{stock}</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Mínimo</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #f1f5f9; margin-top: 4px;">{d['min_s']}</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Máximo</div>
                            <div style="font-size: 1.1rem; font-weight: 600; color: #f1f5f9; margin-top: 4px;">{d['max_s']}</div>
                        </div>
                        <div style="background: rgba(0,0,0,0.3); padding: 8px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">Ubicación</div>
                            <div style="font-size: 0.95rem; color: #f1f5f9; margin-top: 4px;">{d['ubicacion']}</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_btns:
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("−", key=f"menos_{prod_id}", help="Reducir 1"):
                        nuevo = max(0, stock - 1)
                        result = api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": d["ubicacion"]})
                        if result:
                            _get_inventario_data.clear()
                            _procesar_inventario.clear()
                        st.rerun()
                with c2:
                    if st.button("+", key=f"mas_{prod_id}", help="Aumentar 1"):
                        nuevo = stock + 1
                        result = api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": d["ubicacion"]})
                        if result:
                            _get_inventario_data.clear()
                            _procesar_inventario.clear()
                        st.rerun()
        
        # Controles de paginación
        if total_paginas > 1:
            col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
            with col_pag1:
                if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, key="btn_inv_pag_ant"):
                    st.session_state['inv_pagina'] = pagina_actual - 1
                    st.rerun()
            with col_pag2:
                st.markdown(f"<p style='text-align: center;'>Página {pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
            with col_pag3:
                if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, key="btn_inv_pag_sig"):
                    st.session_state['inv_pagina'] = pagina_actual + 1
                    st.rerun()
    else:
        st.info("No hay productos en el inventario")
