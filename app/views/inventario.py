"""
Página de Inventario
"""
import streamlit as st
import pandas as pd
from app.utils.api import api_get, api_post
from app.utils.helpers import to_excel
from app.logic.inventario import (
    calcular_estado_stock, 
    preparar_datos_inventario,
    filtrar_por_estado,
    ordenar_inventario
)
from app.components.stock_badge import render_stock_badge


def render():
    """Renderiza la página de inventario."""
    st.markdown("<h2>📊 Control de Inventario</h2>", unsafe_allow_html=True)
    
    # Obtener datos
    inventarios = api_get("/api/v1/inventario")
    productos = api_get("/api/v1/productos")
    
    # === ACTUALIZAR STOCK ===
    st.markdown("<h3>✏️ Actualizar stock</h3>", unsafe_allow_html=True)
    with st.form("actualizar_stock"):
        col1, col2, col3 = st.columns([1, 1, 2])
        with col1:
            prod_id = st.number_input("ID del producto", min_value=1, key="prod_id")
        with col2:
            nueva_cantidad = st.number_input("Nueva cantidad", min_value=0, key="nueva_cant")
        with col3:
            ubicacion = st.text_input("Ubicación")
        
        if st.form_submit_button("🔄 Actualizar"):
            result = api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nueva_cantidad, "ubicacion": ubicacion})
            if result:
                st.success("✅ Stock actualizado")
                st.rerun()
            else:
                st.error("❌ Error al actualizar")
    
    st.markdown("---")
    
    # === FILTROS ===
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        filtro_estado_inv = st.selectbox("Filtrar por estado", ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"], key="filtro_inv_estado")
    with col_f2:
        ordenar_inv = st.selectbox("Ordenar por", ["Producto (A-Z)", "Stock (mayor)", "Stock (menor)"], key="ordenar_inv")
    
    # Preparar y filtrar datos
    datos_inv = preparar_datos_inventario(inventarios, productos)
    
    # Aplicar filtros
    if filtro_estado_inv != "Todos":
        datos_inv = [d for d in datos_inv if d["estado"] == filtro_estado_inv]
    
    # Ordenar
    datos_inv = ordenar_inventario(datos_inv, ordenar_inv)
    
    # Contador
    st.markdown(f"""
    <div style="padding: 10px 15px; background: rgba(16,185,129,0.1); border-radius: 10px; margin-bottom: 15px;">
        <span style="color: #10b981; font-weight: 600;">{len(datos_inv)}</span>
        <span style="color: #94a3b8;"> productos</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Exportar Excel
    if datos_inv:
        df_inv = pd.DataFrame([{
            "Producto": d["producto"].get("nombre"),
            "SKU": d["producto"].get("sku"),
            "Stock": d["stock"],
            "Stock Mín": d["min_s"],
            "Stock Máx": d["max_s"],
            "Ubicación": d["ubicacion"],
            "Estado": d["estado"]
        } for d in datos_inv])
        
        excel_inv = to_excel(df_inv)
        col_exp, _ = st.columns([1, 3])
        with col_exp:
            st.download_button(
                "📥 Exportar Excel",
                data=excel_inv,
                file_name="inventario.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    # Lista de inventario
    if datos_inv:
        for d in datos_inv:
            prod = d["producto"]
            stock = d["stock"]
            estado = d["estado"]
            prod_id = prod.get("id")
            
            col_card, col_btns = st.columns([4, 1])
            
            with col_card:
                estado_class = estado.lower().replace("á", "a").replace("é", "e")
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(26,35,50,0.8) 0%, rgba(26,35,50,0.6) 100%); border: 1px solid rgba(0,240,255,0.15); border-radius: 16px; padding: 18px; margin-bottom: 12px; border-left: 4px solid {get_estado_color(estado)};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="font-size: 1.1rem; font-weight: 600; color: #f1f5f9;">{prod.get("nombre", "Producto")}</div>
                        <span style="padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; background: {get_estado_bg(estado)}; color: {get_estado_color(estado)};">{estado}</span>
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
                        api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": d["ubicacion"]})
                        st.rerun()
                with c2:
                    if st.button("+", key=f"mas_{prod_id}", help="Aumentar 1"):
                        nuevo = stock + 1
                        api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": d["ubicacion"]})
                        st.rerun()
    else:
        st.info("No hay productos en el inventario")


def get_estado_color(estado: str) -> str:
    """Obtiene el color de borde para un estado."""
    colores = {
        "Agotado": "#6b7280",
        "Crítico": "#ef4444",
        "Bajo": "#f59e0b",
        "Saludable": "#10b981"
    }
    return colores.get(estado, "#10b981")


def get_estado_bg(estado: str) -> str:
    """Obtiene el color de fondo para un estado."""
    bgs = {
        "Agotado": "rgba(107,114,128,0.2)",
        "Crítico": "rgba(239,68,68,0.2)",
        "Bajo": "rgba(245,158,11,0.2)",
        "Saludable": "rgba(16,185,129,0.2)"
    }
    return bgs.get(estado, "rgba(16,185,129,0.2)")
