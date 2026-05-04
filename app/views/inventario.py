"""
Página de Inventario - Vista Tabla Estilo Excel
"""
import streamlit as st
import pandas as pd
from app.utils.api import api_get, api_post, api_put
from app.utils.helpers import to_excel
from app.logic.inventario import (
    preparar_datos_inventario,
    ordenar_inventario
)


@st.cache_data(ttl=5, show_spinner=False)
def _get_inventario_data():
    inventarios = api_get("/api/v1/inventario", use_cache=False)
    productos = api_get("/api/v1/productos", use_cache=False)
    proveedores = api_get("/api/v1/proveedores", use_cache=False)
    return inventarios, productos, proveedores


def render():
    """Renderiza la vista de inventario como tabla Excel."""
    st.markdown("<h2>📦 Inventario</h2>", unsafe_allow_html=True)
    
    inventarios, productos, proveedores = _get_inventario_data()
    datos_inv = preparar_datos_inventario(inventarios, productos)
    
    prov_options_by_name = {p.get("nombre"): p.get("id") for p in proveedores}
    
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
    
    # Buscar edición activa
    editable_id = st.session_state.get('editando_producto_id', None)
    prod_a_editar = None
    if editable_id:
        prod_a_editar = next((d for d in datos_inv if d["producto"].get("id") == editable_id), None)
    
    # Header con contador y exportar
    col_contador, col_export = st.columns([4, 1])
    with col_contador:
        st.markdown(f"<span style='color: #00f0ff; font-weight: 600;'>{len(datos_inv)}</span> <span style='color: #94a3b8;'> productos</span>", unsafe_allow_html=True)
    with col_export:
        formato_export = st.selectbox("📤 Exportar", ["Exportar...", "Excel (.xlsx)", "JSON (.json)"], label_visibility="collapsed", key="formato_export")
        if formato_export and formato_export != "Exportar..." and "Excel" in formato_export:
            # Exportar TODOS los datos a Excel
            df_exp = pd.DataFrame([{
                "ID": d["producto"].get("id"),
                "Nombre": d["producto"].get("nombre"),
                "SKU": d["producto"].get("sku"),
                "Descripcion": d["producto"].get("descripcion", ""),
                "Unidad": d["producto"].get("unidad", "ud"),
                "Categoria": d["producto"].get("categoria", {}).get("nombre", "-"),
                "Proveedor": d["producto"].get("proveedor", {}).get("nombre", "-") if d["producto"].get("proveedor") else "-",
                "Proveedor_ID": d["producto"].get("proveedor_id"),
                "Stock_Actual": d["stock"],
                "Stock_Maximo": d["max_s"],
                "Stock_Minimo": d["producto"].get("stock_minimo", 0),
                "Ubicacion": d["ubicacion"],
                "Estado": d["estado"],
                "Precio_Coste": d["producto"].get("precio_coste") or 0,
                "Precio_Venta": d["producto"].get("precio_venta") or 0,
                "Ganancia": (d["producto"].get("precio_venta") or 0) - (d["producto"].get("precio_coste") or 0),
                "Margen_%": round(((d["producto"].get("precio_venta") or 0) - (d["producto"].get("precio_coste") or 0)) / (d["producto"].get("precio_venta") or 1) * 100, 2) if d["producto"].get("precio_venta") else 0,
                "Codigo_Barras": d["producto"].get("codigo_barras", "-"),
                "Dias_Reposicion": d["producto"].get("tiempo_reposicion", 3),
                "Activo": "Si" if d["producto"].get("activo", True) else "No",
                "Fecha_Creacion": str(d["producto"].get("fecha_creacion", "-"))
            } for d in datos_inv])
            excel_data = to_excel(df_exp)
            st.download_button("⬇️ Descargar Excel", data=excel_data, file_name="inventario.xlsx", 
                              mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, key="btn_exp_excel")
        elif formato_export and formato_export != "Exportar..." and "JSON" in formato_export:
            import json
            # Exportar TODOS los datos a JSON
            json_data = json.dumps([{
                "id": d["producto"].get("id"),
                "nombre": d["producto"].get("nombre"),
                "sku": d["producto"].get("sku"),
                "descripcion": d["producto"].get("descripcion", ""),
                "unidad": d["producto"].get("unidad", "ud"),
                "categoria": d["producto"].get("categoria", {}).get("nombre", "-"),
                "proveedor": {
                    "id": d["producto"].get("proveedor_id"),
                    "nombre": d["producto"].get("proveedor", {}).get("nombre", "-"),
                    "email": d["producto"].get("proveedor", {}).get("email", "-"),
                    "telefono": d["producto"].get("proveedor", {}).get("telefono", "-")
                } if d["producto"].get("proveedor") else None,
                "inventario": {
                    "stock_actual": d["stock"],
                    "stock_maximo": d["max_s"],
                    "stock_minimo": d["producto"].get("stock_minimo", 0),
                    "ubicacion": d["ubicacion"],
                    "estado": d["estado"]
                },
                "precios": {
                    "coste": d["producto"].get("precio_coste") or 0,
                    "venta": d["producto"].get("precio_venta") or 0,
                    "ganancia": (d["producto"].get("precio_venta") or 0) - (d["producto"].get("precio_coste") or 0),
                    "margen_porcentaje": round(((d["producto"].get("precio_venta") or 0) - (d["producto"].get("precio_coste") or 0)) / (d["producto"].get("precio_venta") or 1) * 100, 2) if d["producto"].get("precio_venta") else 0
                },
                "codigo_barras": d["producto"].get("codigo_barras"),
                "tiempo_reposicion": d["producto"].get("tiempo_reposicion", 3),
                "activo": d["producto"].get("activo", True),
                "fecha_creacion": str(d["producto"].get("fecha_creacion", "-"))
            } for d in datos_inv], indent=2, ensure_ascii=False)
            st.download_button("⬇️ Descargar JSON", data=json_data, file_name="inventario.json", 
                              mime="application/json", use_container_width=True, key="btn_exp_json")
    
    st.markdown("---")
    
    # Formulario de edición
    if prod_a_editar:
        productos_skus = [p.get("sku", "").lower() for p in productos if p.get("id") != editable_id]
        sku_actual = prod_a_editar["producto"].get("sku", "")
        
        st.markdown(f"<div style='background: linear-gradient(135deg, rgba(0, 240, 255, 0.15), rgba(0, 200, 255, 0.05)); border: 1px solid #00f0ff; border-radius: 12px; padding: 20px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='color: #00f0ff; margin: 0 0 15px 0;'>✏️ Editando: {prod_a_editar['producto'].get('nombre', '')}</h4>", unsafe_allow_html=True)
        
        col_e1, col_e2 = st.columns([1, 1])
        with col_e1:
            nuevo_sku = st.text_input("SKU", value=sku_actual, key="edit_sku_inv")
        with col_e2:
            prov_actual_id = prod_a_editar["producto"].get("proveedor_id")
            prov_actual_nombre = next((p.get("nombre") for p in proveedores if p.get("id") == prov_actual_id), "Sin proveedor")
            all_prov_nombres = ["Sin proveedor"] + [p.get("nombre") for p in proveedores] + ["➕ Nuevo proveedor"]
            prov_index = all_prov_nombres.index(prov_actual_nombre) if prov_actual_nombre in all_prov_nombres else 0
            nuevo_proveedor = st.selectbox("Proveedor", all_prov_nombres, index=prov_index, key="edit_prov_inv")
            
            if nuevo_proveedor == "➕ Nuevo proveedor":
                st.markdown("<div style='background:rgba(0,240,255,0.1);padding:10px;border-radius:8px;margin-top:5px;'>", unsafe_allow_html=True)
                nuevo_prov_nombre = st.text_input("Nombre nuevo *", key="new_prov_nom_inv", placeholder="Nombre del proveedor")
                nuevo_prov_email = st.text_input("Email nuevo *", key="new_prov_email_inv", placeholder="email@ejemplo.com")
                nuevo_prov_telefono = st.text_input("Teléfono", key="new_prov_tel_inv", placeholder="600 000 000")
                
                emails_existentes = [p.get("email", "").lower() for p in proveedores]
                if nuevo_prov_email and nuevo_prov_email.lower() in emails_existentes:
                    st.caption("⚠️ Email ya existe")
                    btn_crear_disabled = True
                else:
                    btn_crear_disabled = False
                
                if st.button("💾 Crear y usar", key="btn_new_prov_inv", use_container_width=True, type="secondary", disabled=btn_crear_disabled):
                    if nuevo_prov_nombre and nuevo_prov_email:
                        prov_data = {"nombre": nuevo_prov_nombre, "email": nuevo_prov_email, "telefono": nuevo_prov_telefono or None}
                        result = api_post("/api/v1/proveedores", prov_data)
                        if result:
                            _get_inventario_data.clear()
                            nuevo_prov_id = result.get("id")
                            data_prov = {"proveedor_id": nuevo_prov_id}
                            api_put(f"/api/v1/productos/{editable_id}", data_prov)
                            st.success("✅ Proveedor creado y asignado")
                            del st.session_state['editando_producto_id']
                            st.rerun()
                        else:
                            st.error("❌ Error al crear proveedor")
                st.markdown("</div>", unsafe_allow_html=True)
                nuevo_proveedor = prov_actual_nombre
        
        # Validaciones
        errores_edit = []
        if nuevo_sku != sku_actual:
            if not nuevo_sku:
                errores_edit.append("SKU obligatorio")
            elif len(nuevo_sku) < 4:
                errores_edit.append("Mín. 4 caracteres")
            elif len(nuevo_sku) > 20:
                errores_edit.append("Máx. 20 caracteres")
            elif nuevo_sku.lower() in productos_skus:
                errores_edit.append("SKU duplicado")
        
        col_btn_guardar, col_btn_cancel = st.columns([1, 4])
        with col_btn_guardar:
            btn_guardar = st.button("💾 Guardar", type="primary", use_container_width=True, 
                                disabled=len(errores_edit) > 0, key="btn_save_edit_inv")
            if errores_edit:
                st.caption(f"⚠️ {', '.join(errores_edit)}")
        with col_btn_cancel:
            if st.button("❌ Cancelar", use_container_width=True, key="btn_cancel_edit_inv"):
                del st.session_state['editando_producto_id']
                st.rerun()
        
        if btn_guardar:
            nuevo_prov_id = prov_options_by_name.get(nuevo_proveedor) if nuevo_proveedor != "Sin proveedor" else None
            
            data_sku = {"sku": nuevo_sku}
            api_put(f"/api/v1/productos/{editable_id}", data_sku)
            
            data_prov = {"proveedor_id": nuevo_prov_id}
            api_put(f"/api/v1/productos/{editable_id}", data_prov)
            
            _get_inventario_data.clear()
            st.success("✅ Actualizado")
            del st.session_state['editando_producto_id']
            st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")
    
    # Paginación
    productos_por_pagina = 8
    total_paginas = max(1, (len(datos_inv) + productos_por_pagina - 1) // productos_por_pagina)
    
    if 'pagina_inv' not in st.session_state:
        st.session_state['pagina_inv'] = 1
    
    pagina_actual = min(st.session_state['pagina_inv'], total_paginas)
    inicio = (pagina_actual - 1) * productos_por_pagina
    fin = min(inicio + productos_por_pagina, len(datos_inv))
    datos_inv_pagina = datos_inv[inicio:fin]
    
    # Dashboard de Tarjetas
    num_cols = 4
    for i in range(0, len(datos_inv_pagina), num_cols):
        row_items = datos_inv_pagina[i:i+num_cols]
        cols = st.columns(num_cols)
        
        for idx, d in enumerate(row_items):
            prod = d["producto"]
            pid = prod.get("id")
            prov_nombre = prod.get("proveedor", {}).get("nombre") if prod.get("proveedor") else "Sin proveedor"
            estado = d["estado"]
            stock = d["stock"]
            max_s = d["max_s"]
            
            pct = min(100, int((stock / max_s) * 100)) if max_s > 0 else 0
            color_barra = "#ef4444" if pct <= 20 else "#f59e0b" if pct <= 50 else "#10b981"
            color_estado = {"Agotado": "#6b7280", "Crítico": "#ef4444", "Bajo": "#f59e0b", "Saludable": "#10b981"}.get(estado, "#10b981")
            is_editing = (pid == editable_id)
            ganancia = (prod.get('precio_venta') or 0) - (prod.get('precio_coste') or 0)
            ganancia_color = "#10b981" if ganancia > 0 else "#ef4444"
            
            with cols[idx]:
                # Tarjeta completa en HTML
                border_color = "#00f0ff" if is_editing else "rgba(255,255,255,0.1)"
                shadow = "0 0 20px rgba(0,240,255,0.3)" if is_editing else "none"
                
                card_html = f"""<div style="background: linear-gradient(145deg, rgba(30,41,59,0.95), rgba(15,23,42,0.98)); border: 1px solid {border_color}; border-radius: 12px; padding: 16px; margin-bottom: 8px; box-shadow: {shadow};">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                        <div>
                            <div style="font-size: 20px; font-weight: 700; color: #f8fafc; margin-bottom: 2px;">{prod.get('nombre')}</div>
                            <div style="font-size: 15px; color: #64748b;">{prod.get('sku')} | {prod.get('unidad', 'ud')}</div>
                        </div>
                        <div style="background: {color_estado}; padding: 3px 8px; border-radius: 12px; font-size: 15px; font-weight: 700; color: white;">{estado}</div>
                    </div>
                    <div style="height: 1px; background: rgba(255,255,255,0.1); margin: 10px 0;"></div>
                    <div style="font-size: 15px; color: #f8fafc; margin-bottom: 6px;">🏢 {prov_nombre}</div>
                    <div style="margin-bottom: 12px;">
                        <div style="display: flex; justify-content: space-between; font-size: 15px; margin-bottom: 4px;">
                            <span style="color: #64748b;">Stock</span>
                            <span style="color: #e2e8f0; font-weight: 600;">{stock} / {max_s}</span>
                        </div>
                        <div style="width: 100%; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
                            <div style="width: {pct}%; height: 100%; background: {color_barra}; border-radius: 2px;"></div>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 10px; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #f8fafc; margin-bottom: 2px;">COSTE</div>
                            <div style="font-size: 15px; color: #f59e0b; font-weight: 700;">€{prod.get('precio_coste') or 0:.2f}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #f8fafc; margin-bottom: 2px;">VENTA</div>
                            <div style="font-size: 15px; color: #00f0ff; font-weight: 700;">€{prod.get('precio_venta') or 0:.2f}</div>
                        </div>
                        <div style="text-align: center;">
                            <div style="font-size: 12px; color: #f8fafc; margin-bottom: 2px;">GANANCIA</div>
                            <div style="font-size: 15px; color: {ganancia_color}; font-weight: 700;">€{ganancia:.2f}</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 15px; color: #64748b;">
                        <span>📍 {d['ubicacion']}</span>
                        <span>#{prod.get('codigo_barras', '-') or '-'}</span>
                    </div>
                </div>"""
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Botón editar debajo de la tarjeta
                if st.button("✏️ Editar", key=f"btn_edit_{pid}", use_container_width=True, 
                            type="primary" if is_editing else "secondary"):
                    st.session_state['editando_producto_id'] = pid
                    st.rerun()
    
    # Controles de paginación
    if total_paginas > 1:
        st.markdown("---")
        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
        with col_pag1:
            if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, use_container_width=True):
                st.session_state['pagina_inv'] = pagina_actual - 1
                st.rerun()
        with col_pag2:
            st.markdown(f"<p style='text-align: center; color: #94a3b8; margin: 0;'>Página {pagina_actual} de {total_paginas} | Mostrando {inicio+1}-{fin} de {len(datos_inv)}</p>", unsafe_allow_html=True)
        with col_pag3:
            if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, use_container_width=True):
                st.session_state['pagina_inv'] = pagina_actual + 1
                st.rerun()
    
