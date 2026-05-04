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
    
    st.markdown(f"<span style='color: #00f0ff; font-weight: 600;'>{len(datos_inv)}</span> <span style='color: #94a3b8;'> productos</span>", unsafe_allow_html=True)
    st.markdown("---")
    
    # Formulario de edición SKU
    if prod_a_editar:
        productos_skus = [p.get("sku", "").lower() for p in productos if p.get("id") != editable_id]
        sku_actual = prod_a_editar["producto"].get("sku", "")
        
        st.markdown(f"<h4 style='color: #00f0ff;'>✏️ Editando: {prod_a_editar['producto'].get('nombre', '')}</h4>", unsafe_allow_html=True)
        
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
                            st.success(f"✅ Proveedor '{nuevo_prov_nombre}' creado")
                            # Asignar el nuevo proveedor al producto
                            nuevo_prov_id = result.get("id")
                            data_prov = {"proveedor_id": nuevo_prov_id}
                            api_put(f"/api/v1/productos/{editable_id}", data_prov)
                            _get_inventario_data.clear()
                            st.success("✅ Proveedor asignado")
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
                errores_edit.append("SKU mínimo 4 caracteres")
            elif len(nuevo_sku) > 20:
                errores_edit.append("SKU máximo 20 caracteres")
            elif nuevo_sku.lower() in productos_skus:
                errores_edit.append("SKU duplicado")
        
        col_btn_guardar, col_btn_cancel = st.columns(2)
        with col_btn_guardar:
            btn_guardar = st.button("💾 Guardar cambios", type="primary", use_container_width=True, 
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
            result_sku = api_put(f"/api/v1/productos/{editable_id}", data_sku)
            
            data_prov = {"proveedor_id": nuevo_prov_id}
            api_put(f"/api/v1/productos/{editable_id}", data_prov)
            
            if result_sku or nuevo_proveedor != prov_actual_nombre:
                _get_inventario_data.clear()
                st.success("✅ Actualizado")
                del st.session_state['editando_producto_id']
                st.rerun()
            else:
                st.error("❌ Error al actualizar")
        
        st.markdown("---")
    
    st.markdown("""
    <style>
    .edit-btn-mini {
        padding: 2px 8px !important;
        font-size: 12px !important;
        min-width: 40px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    cols_tabla = st.columns([3, 1.5, 1.5, 1.5, 1, 1, 1.5, 1, 1, 1, 1, 0.8])
    headers = ["Producto", "SKU", "Unidad", "Proveedor", "Stock", "Máx", "Ubicación", "Estado", "Coste", "Venta", "Ganancia", "✏️"]
    for i, col in enumerate(cols_tabla):
        col.markdown(f"<b>{headers[i]}</b>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    for idx, d in enumerate(datos_inv):
        prod = d["producto"]
        pid = prod.get("id")
        prov_nombre = prod.get("proveedor", {}).get("nombre") if prod.get("proveedor") else "-"
        editando_esta = (editable_id == pid)
        
        if editando_esta:
            st.markdown("<div style='background: rgba(0, 240, 255, 0.1); border: 1px solid #00f0ff; border-radius: 8px; padding: 10px; margin-bottom: 5px;'>", unsafe_allow_html=True)
        
        cols = st.columns([3, 1.5, 1.5, 1.5, 1, 1, 1.5, 1, 1, 1, 1, 0.8])
        
        with cols[0]:
            st.markdown(f"<span style='color: #f8fafc;'>{prod.get('nombre', '-')}</span>", unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f"<span style='color: #00f0ff;'>{prod.get('sku', '-')}</span>", unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f"<span style='color: #94a3b8;'>{prod.get('unidad', 'ud')}</span>", unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f"<span style='color: #cbd5e1;'>{prov_nombre}</span>", unsafe_allow_html=True)
        with cols[4]:
            st.markdown(f"<span style='color: #f8fafc;'>{d['stock']}</span>", unsafe_allow_html=True)
        with cols[5]:
            st.markdown(f"<span style='color: #94a3b8;'>{d['max_s']}</span>", unsafe_allow_html=True)
        with cols[6]:
            st.markdown(f"<span style='color: #94a3b8; font-size: 12px;'>{d['ubicacion']}</span>", unsafe_allow_html=True)
        with cols[7]:
            color_estado = {"Agotado": "#6b7280", "Crítico": "#ef4444", "Bajo": "#f59e0b", "Saludable": "#10b981"}.get(d['estado'], "#10b981")
            st.markdown(f"<span style='color: {color_estado}; font-weight: 600;'>{d['estado']}</span>", unsafe_allow_html=True)
        with cols[8]:
            st.markdown(f"<span>€{prod.get('precio_coste') or 0:.2f}</span>", unsafe_allow_html=True)
        with cols[9]:
            st.markdown(f"<span>€{prod.get('precio_venta') or 0:.2f}</span>", unsafe_allow_html=True)
        with cols[10]:
            ganancia = (prod.get('precio_venta') or 0) - (prod.get('precio_coste') or 0)
            color_gan = "#10b981" if ganancia > 0 else "#ef4444"
            st.markdown(f"<span style='color: {color_gan};'>€{ganancia:.2f}</span>", unsafe_allow_html=True)
        with cols[11]:
            if st.button("✏️", key=f"btn_edit_{pid}", use_container_width=True):
                st.session_state['editando_producto_id'] = pid
                st.rerun()
        
        if editando_esta:
            st.markdown("</div>", unsafe_allow_html=True)
    
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