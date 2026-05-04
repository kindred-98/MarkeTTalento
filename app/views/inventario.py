"""
Página de Inventario - Vista Tabla Estilo Excel
"""
import streamlit as st
import pandas as pd
from app.utils.api import api_get, api_post
from app.utils.helpers import to_excel
from app.logic.inventario import (
    preparar_datos_inventario,
    ordenar_inventario
)


@st.cache_data(ttl=5, show_spinner=False)
def _get_inventario_data():
    inventarios = api_get("/api/v1/inventario", use_cache=False)
    productos = api_get("/api/v1/productos", use_cache=False)
    return inventarios, productos


def render():
    """Renderiza la vista de inventario como tabla Excel."""
    st.markdown("<h2>📦 Inventario</h2>", unsafe_allow_html=True)
    
    inventarios, productos = _get_inventario_data()
    datos_inv = preparar_datos_inventario(inventarios, productos)
    
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    with col_f1:
        busqueda = st.text_input("🔍 Buscar", placeholder="Producto o SKU...", key="busq")
    with col_f2:
        filtro_estado = st.selectbox("Estado", ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"], key="filtro")
    with col_f3:
        ordenar = st.selectbox("Ordenar", ["Producto (A-Z)", "Stock (mayor)", "Stock (menor)"], key="ordenar")
    
    if busqueda:
        busq_lower = busqueda.lower()
        datos_inv = [d for d in datos_inv 
                    if busq_lower in d["producto"].get("nombre", "").lower() 
                    or busq_lower in d["producto"].get("sku", "").lower()]
    
    if filtro_estado != "Todos":
        datos_inv = [d for d in datos_inv if d["estado"] == filtro_estado]
    
    datos_inv = ordenar_inventario(datos_inv, ordenar)
    
    st.markdown(f"<span style='color: #00f0ff; font-weight: 600;'>{len(datos_inv)}</span> <span style='color: #94a3b8;'> productos</span>", unsafe_allow_html=True)
    st.markdown("---")
    
    df = pd.DataFrame([{
        "Producto": prod.get("nombre"),
        "SKU": prod.get("sku"),
        "Unidad": prod.get("unidad", "ud"),
        "Proveedor": prod.get("proveedor", {}).get("nombre", "-") if prod.get("proveedor") else "-",
        "Stock": d["stock"],
        "Máx": d["max_s"],
        "Ubicación": d["ubicacion"],
        "Estado": d["estado"],
        "Coste": (prod.get('precio_coste') or 0),
        "Venta": (prod.get('precio_venta') or 0),
        "Ganancia": (prod.get('precio_venta') or 0) - (prod.get('precio_coste') or 0)
    } for prod, d in [(d["producto"], d) for d in datos_inv]])

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Producto": st.column_config.TextColumn("Producto", width="medium"),
            "SKU": st.column_config.TextColumn("SKU", width="small"),
            "Unidad": st.column_config.TextColumn("Unidad", width="small"),
            "Proveedor": st.column_config.TextColumn("Proveedor", width="medium"),
            "Stock": st.column_config.NumberColumn("Stock", format="%d"),
            "Máx": st.column_config.NumberColumn("Máx", format="%d"),
            "Ubicación": st.column_config.TextColumn("Ubicación", width="large"),
            "Estado": st.column_config.TextColumn("Estado", width="small"),
            "Coste": st.column_config.NumberColumn("Coste", format="€%.2f"),
            "Venta": st.column_config.NumberColumn("Venta", format="€%.2f"),
            "Ganancia": st.column_config.NumberColumn("Ganancia", format="€%.2f"),
        }
    )
    
    with st.expander("✏️ Editar stock por ID"):
        col_e1, col_e2, col_e3 = st.columns([1, 1, 1])
        with col_e1:
            prod_id_edit = st.number_input("ID producto", min_value=1, key="edit_id_inv")
        with col_e2:
            nuevaCant = st.number_input("Nueva cantidad", min_value=0, key="edit_cant_inv")
        with col_e3:
            nuevaUbic = st.text_input("Ubicación", key="edit_ubic_inv")
        
        if st.button("🔄 Actualizar", key="btn_actualizar_inv"):
            result = api_post(f"/api/v1/inventario/{prod_id_edit}", {"cantidad": nuevaCant, "ubicacion": nuevaUbic})
            if result:
                _get_inventario_data.clear()
                st.success("✅ Stock actualizado")
                st.rerun()
            else:
                st.error("❌ Error al actualizar")
    
    st.markdown("---")
    col_exp, _ = st.columns([1, 3])
    with col_exp:
        df = pd.DataFrame([{
            "Producto": d["producto"].get("nombre"),
            "SKU": d["producto"].get("sku"),
            "Unidad": d["producto"].get("unidad", "ud"),
            "Proveedor": d["producto"].get("proveedor", {}).get("nombre", "-") if d["producto"].get("proveedor") else "-",
            "Stock": d["stock"],
            "Máx": d["max_s"],
            "Ubicación": d["ubicacion"],
            "Estado": d["estado"],
            "Coste": d["producto"].get("precio_coste") or 0,
            "Venta": d["producto"].get("precio_venta") or 0,
            "Ganancia": (d["producto"].get("precio_venta") or 0) - (d["producto"].get("precio_coste") or 0)
        } for d in datos_inv])
        excel_data = to_excel(df)
        st.download_button(
            "📥 Exportar Excel",
            data=excel_data,
            file_name="inventario.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )