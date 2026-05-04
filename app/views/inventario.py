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


def _ver_detalles_modal(prod_id, productos, inventarios):
    """Abre un diálogo con los detalles del producto."""
    producto = next((p for p in productos if p.get("id") == prod_id), None)
    if not producto:
        st.error("Producto no encontrado")
        return
    
    inv = next((i for i in inventarios if i.get("producto_id") == prod_id), None)
    stock = inv.get("cantidad", 0) if inv else 0
    
    max_s = producto.get("stock_maximo", 100) or 100
    estado = "Agotado" if stock == 0 else "Crítico" if stock <= max_s * 0.25 else "Bajo" if stock <= max_s * 0.5 else "Saludable"
    color = {"Agotado": "#6b7280", "Crítico": "#ef4444", "Bajo": "#f59e0b", "Saludable": "#10b981"}.get(estado, "#10b981")
    ubicacion = inv.get("ubicacion", "-") if inv else "-"
    
    with st.container():
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(30,41,59,0.9), rgba(51,65,85,0.7)); 
                    border: 2px solid {color}; border-radius: 12px; padding: 20px; margin: 10px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="color: #fff; margin: 0;">{producto.get('nombre', '')}</h3>
                    <p style="color: #94a3b8; margin: 5px 0;">SKU: {producto.get('sku', '-')} | {producto.get('unidad', 'ud')}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 2rem; font-weight: 700; color: #00f0ff;">{stock}</div>
                    <span style="padding: 4px 12px; border-radius: 12px; background: {color}30; color: {color}; font-weight: 600;">{estado}</span>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 15px;">
                <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #64748b; font-size: 11px; margin: 0;">MÍNIMO</p>
                    <p style="color: #fff; font-weight: 600;">{producto.get('stock_minimo', 0)}</p>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #64748b; font-size: 11px; margin: 0;">MÁXIMO</p>
                    <p style="color: #fff; font-weight: 600;">{producto.get('stock_maximo', 100)}</p>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #64748b; font-size: 11px; margin: 0;">PRECIO</p>
                    <p style="color: #fff; font-weight: 600;">€{producto.get('precio_venta', 0):.2f}</p>
                </div>
                <div style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 8px; text-align: center;">
                    <p style="color: #64748b; font-size: 11px; margin: 0;">UBICACIÓN</p>
                    <p style="color: #fff; font-weight: 600;">{ubicacion}</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("− 1", key=f"menos_{prod_id}", use_container_width=True):
                nuevo = max(0, stock - 1)
                api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": ubicacion})
                _get_inventario_data.clear()
                st.rerun()
        with col2:
            if st.button("+ 1", key=f"mas_{prod_id}", use_container_width=True):
                nuevo = stock + 1
                api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": ubicacion})
                _get_inventario_data.clear()
                st.rerun()
        with col3:
            nuevo_val = st.number_input("Nueva cantidad", min_value=0, value=stock, key=f"nuevo_{prod_id}", label_visibility="collapsed")
            if st.button("💾 Guardar", key=f"guardar_{prod_id}", use_container_width=True):
                api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo_val, "ubicacion": ubicacion})
                _get_inventario_data.clear()
                st.rerun()
        with col4:
            if st.button("✕ Cerrar", key=f"cerrar_{prod_id}", use_container_width=True):
                st.rerun()


def render():
    """Renderiza la vista de inventario tipo tabla Excel."""
    st.markdown("<h2>📦 Inventario</h2>", unsafe_allow_html=True)
    
    inventarios, productos = _get_inventario_data()
    datos_inv = preparar_datos_inventario(inventarios, productos)
    
    if 'inv_view' not in st.session_state:
        st.session_state['inv_view'] = "Grid"
    if 'inv_page' not in st.session_state:
        st.session_state['inv_page'] = 1
    
    col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
    with col_f1:
        busqueda = st.text_input("🔍 Buscar", placeholder="Producto o SKU...", key="busq")
    with col_f2:
        filtro_estado = st.selectbox("Estado", ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"], key="filtro")
    with col_f3:
        ordenar = st.selectbox("Ordenar", ["Producto (A-Z)", "Stock (mayor)", "Stock (menor)"], key="ordenar")
    with col_f4:
        ver_opcion = st.selectbox("Ver", ["Grid", "Tabla"], key="ver", on_change=lambda: st.session_state.update(inv_view=st.session_state.ver, inv_page=1))
    
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
    
    colores_estado = {"Agotado": "#6b7280", "Crítico": "#ef4444", "Bajo": "#f59e0b", "Saludable": "#10b981"}
    
    ver = st.session_state.get('inv_view', 'Grid')
    
    if ver == "Grid":
        items_por_pagina = 12
        total_paginas = max(1, (len(datos_inv) + items_por_pagina - 1) // items_por_pagina)
        pagina_actual = min(st.session_state.get('inv_page', 1), total_paginas)
        
        inicio = (pagina_actual - 1) * items_por_pagina
        fin = min(inicio + items_por_pagina, len(datos_inv))
        datos_pagina = datos_inv[inicio:fin]
        
        cols = st.columns(4)
        for idx, d in enumerate(datos_pagina):
            prod = d["producto"]
            estado = d["estado"]
            color = colores_estado.get(estado, "#10b981")
            prod_id = prod.get("id")
            
            with cols[idx % 4]:
                st.markdown(f"""
                <div style="background: rgba(30,41,59,0.7); border: 1px solid {color}40; border-radius: 10px; padding: 12px; margin-bottom: 8px; border-left: 3px solid {color};">
                    <div style="font-weight: 600; font-size: 13px; color: #fff;">{prod.get("nombre", "Producto")[:20]}</div>
                    <div style="color: #94a3b8; font-size: 11px;">{prod.get("sku", "-")}</div>
                    <div style="display: flex; justify-content: space-between; margin-top: 8px;">
                        <span style="font-size: 18px; font-weight: 700; color: #00f0ff;">{d['stock']}</span>
                        <span style="padding: 2px 8px; border-radius: 10px; font-size: 10px; background: {color}30; color: {color};">{estado}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("−", key=f"menos_{prod_id}_{pagina_actual}", use_container_width=True):
                        nuevo = max(0, d['stock'] - 1)
                        api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": d["ubicacion"]})
                        _get_inventario_data.clear()
                        st.rerun()
                with c2:
                    if st.button("+", key=f"mas_{prod_id}_{pagina_actual}", use_container_width=True):
                        nuevo = d['stock'] + 1
                        api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo, "ubicacion": d["ubicacion"]})
                        _get_inventario_data.clear()
                        st.rerun()
                
                if st.button("📋 Detalles", key=f"detalles_{prod_id}_{pagina_actual}", use_container_width=True):
                    _ver_detalles_modal(prod_id, productos, inventarios)
        
        if total_paginas > 1:
            col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
            with col_pag1:
                if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, key="btn_inv_ant"):
                    st.session_state['inv_page'] = pagina_actual - 1
                    st.rerun()
            with col_pag2:
                st.markdown(f"<p style='text-align: center;'>Página {pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
            with col_pag3:
                if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, key="btn_inv_sig"):
                    st.session_state['inv_page'] = pagina_actual + 1
                    st.rerun()
    
    else:
        df = pd.DataFrame([{
            "Producto": prod.get("nombre"),
            "SKU": prod.get("sku"),
            "Stock": d["stock"],
            "Mín": d["min_s"],
            "Máx": d["max_s"],
            "Ubicación": d["ubicacion"],
            "Estado": d["estado"],
            "Precio": f"€{prod.get('precio_venta', 0):.2f}"
        } for prod, d in [(d["producto"], d) for d in datos_inv]])
        
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Producto": st.column_config.TextColumn("Producto", width="medium"),
                "SKU": st.column_config.TextColumn("SKU", width="small"),
                "Stock": st.column_config.NumberColumn("Stock", format="%d"),
                "Mín": st.column_config.NumberColumn("Mín", format="%d"),
                "Máx": st.column_config.NumberColumn("Máx", format="%d"),
                "Ubicación": st.column_config.TextColumn("Ubicación", width="medium"),
                "Estado": st.column_config.TextColumn("Estado", width="small"),
                "Precio": st.column_config.TextColumn("Precio", width="small"),
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
            "Stock": d["stock"],
            "Mín": d["min_s"],
            "Máx": d["max_s"],
            "Ubicación": d["ubicacion"],
            "Estado": d["estado"]
        } for d in datos_inv])
        excel_data = to_excel(df)
        st.download_button(
            "📥 Exportar Excel",
            data=excel_data,
            file_name="inventario.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )