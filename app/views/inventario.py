"""
Página de Inventario - Vista Dashboard con Tarjetas
Refactorizado: Funciones pequeñas y reutilizables
"""
import streamlit as st
import pandas as pd
from app.utils.api import api_get, api_post, api_put
from app.utils.helpers import to_excel
from app.utils.validators import validar_sku, validar_email_proveedor
from app.logic.inventario import (
    preparar_datos_inventario,
    ordenar_inventario
)


@st.cache_data(ttl=5, show_spinner=False)
def _get_inventario_data():
    """Obtiene datos de inventario, productos y proveedores."""
    inventarios = api_get("/api/v1/inventario", use_cache=False)
    productos = api_get("/api/v1/productos", use_cache=False)
    proveedores = api_get("/api/v1/proveedores", use_cache=False)
    return inventarios, productos, proveedores


def _aplicar_filtros(datos_inv, busqueda, filtro_estado):
    """Aplica filtros de búsqueda y estado."""
    if busqueda:
        busq_lower = busqueda.lower()
        datos_inv = [d for d in datos_inv 
                    if busq_lower in d["producto"].get("nombre", "").lower() 
                    or busq_lower in d["producto"].get("sku", "").lower()]
    
    if filtro_estado != "Todos":
        datos_inv = [d for d in datos_inv if d["estado"] == filtro_estado]
    
    return datos_inv


def _render_filtros(productos):
    """Renderiza filtros y controles de búsqueda."""
    col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
    
    with col_f1:
        busqueda = st.text_input("🔍 Buscar", placeholder="Producto o SKU...", key="busq")
    with col_f2:
        filtro_estado = st.selectbox("Estado", ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"], key="filtro")
    with col_f3:
        ordenar = st.selectbox("Ordenar", ["Producto (A-Z)", "Stock (mayor)", "Stock (menor)"], key="ordenar")
    
    return busqueda, filtro_estado, ordenar


def _render_exportar(datos_inv):
    """Renderiza controles de exportación."""
    formato_export = st.selectbox(
        "📤 Exportar", 
        ["Exportar...", "Excel (.xlsx)", "JSON (.json)"], 
        label_visibility="collapsed", 
        key="formato_export"
    )
    
    if formato_export and formato_export != "Exportar...":
        if "Excel" in formato_export:
            _exportar_excel(datos_inv)
        elif "JSON" in formato_export:
            _exportar_json(datos_inv)


def _extraer_datos_producto(d):
    """Extrae datos normalizados de un producto para exportación.
    
    Args:
        d: Diccionario con producto e inventario
    
    Returns:
        Diccionario con datos normalizados
    """
    prod = d["producto"]
    precio_venta = prod.get("precio_venta") or 0
    precio_coste = prod.get("precio_coste") or 0
    ganancia = precio_venta - precio_coste
    margen = round((ganancia / precio_coste) * 100, 2) if precio_coste > 0 else 0
    
    return {
        "id": prod.get("id"),
        "nombre": prod.get("nombre"),
        "sku": prod.get("sku"),
        "descripcion": prod.get("descripcion", ""),
        "unidad": prod.get("unidad", "ud"),
        "categoria": prod.get("categoria", {}).get("nombre", "-"),
        "categoria_id": prod.get("categoria_id"),
        "proveedor_id": prod.get("proveedor_id"),
        "proveedor_nombre": prod.get("proveedor", {}).get("nombre", "-") if prod.get("proveedor") else "-",
        "proveedor_email": prod.get("proveedor", {}).get("email", "-") if prod.get("proveedor") else "-",
        "proveedor_telefono": prod.get("proveedor", {}).get("telefono", "-") if prod.get("proveedor") else "-",
        "stock_actual": d["stock"],
        "stock_maximo": d["max_s"],
        "stock_minimo": prod.get("stock_minimo", 0),
        "ubicacion": d["ubicacion"],
        "estado": d["estado"],
        "precio_coste": precio_coste,
        "precio_venta": precio_venta,
        "ganancia": ganancia,
        "margen_porcentaje": margen,
        "codigo_barras": prod.get("codigo_barras", "-"),
        "tiempo_reposicion": prod.get("tiempo_reposicion", 3),
        "activo": prod.get("activo", True),
        "fecha_creacion": str(prod.get("fecha_creacion", "-"))
    }


def _exportar_excel(datos_inv):
    """Exporta datos a Excel."""
    datos = [_extraer_datos_producto(d) for d in datos_inv]
    
    df_exp = pd.DataFrame([{
        "ID": d["id"],
        "Nombre": d["nombre"],
        "SKU": d["sku"],
        "Descripcion": d["descripcion"],
        "Unidad": d["unidad"],
        "Categoria": d["categoria"],
        "Proveedor": d["proveedor_nombre"],
        "Proveedor_ID": d["proveedor_id"],
        "Stock_Actual": d["stock_actual"],
        "Stock_Maximo": d["stock_maximo"],
        "Stock_Minimo": d["stock_minimo"],
        "Ubicacion": d["ubicacion"],
        "Estado": d["estado"],
        "Precio_Coste": d["precio_coste"],
        "Precio_Venta": d["precio_venta"],
        "Ganancia": d["ganancia"],
        "Margen_%": d["margen_porcentaje"],
        "Codigo_Barras": d["codigo_barras"],
        "Dias_Reposicion": d["tiempo_reposicion"],
        "Activo": "Si" if d["activo"] else "No",
        "Fecha_Creacion": d["fecha_creacion"]
    } for d in datos])
    
    excel_data = to_excel(df_exp)
    st.download_button(
        "⬇️ Descargar Excel", 
        data=excel_data, 
        file_name="inventario.xlsx", 
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        use_container_width=True, 
        key="btn_exp_excel"
    )


def _exportar_json(datos_inv):
    """Exporta datos a JSON."""
    import json
    
    datos = [_extraer_datos_producto(d) for d in datos_inv]
    
    json_data = json.dumps([{
        "id": d["id"],
        "nombre": d["nombre"],
        "sku": d["sku"],
        "descripcion": d["descripcion"],
        "unidad": d["unidad"],
        "categoria": {
            "id": d["categoria_id"],
            "nombre": d["categoria"]
        },
        "proveedor": {
            "id": d["proveedor_id"],
            "nombre": d["proveedor_nombre"],
            "email": d["proveedor_email"],
            "telefono": d["proveedor_telefono"]
        } if d["proveedor_id"] else None,
        "inventario": {
            "stock_actual": d["stock_actual"],
            "stock_maximo": d["stock_maximo"],
            "stock_minimo": d["stock_minimo"],
            "ubicacion": d["ubicacion"],
            "estado": d["estado"]
        },
        "precios": {
            "coste": d["precio_coste"],
            "venta": d["precio_venta"],
            "ganancia": d["ganancia"],
            "margen_porcentaje": d["margen_porcentaje"]
        },
        "codigo_barras": d["codigo_barras"],
        "tiempo_reposicion": d["tiempo_reposicion"],
        "activo": d["activo"],
        "fecha_creacion": d["fecha_creacion"]
    } for d in datos], indent=2, ensure_ascii=False)
    
    st.download_button(
        "⬇️ Descargar JSON", 
        data=json_data, 
        file_name="inventario.json", 
        mime="application/json", 
        use_container_width=True, 
        key="btn_exp_json"
    )


def _render_tarjeta_producto(d, is_editing, proveedores, editable_id, prov_options_by_name):
    """Renderiza una tarjeta de producto individual."""
    prod = d["producto"]
    pid = prod.get("id")
    prov_nombre = prod.get("proveedor", {}).get("nombre") if prod.get("proveedor") else "Sin proveedor"
    estado = d["estado"]
    stock = d["stock"]
    max_s = d["max_s"]
    
    pct = min(100, int((stock / max_s) * 100)) if max_s > 0 else 0
    color_barra = "#ef4444" if pct <= 20 else "#f59e0b" if pct <= 50 else "#10b981"
    color_estado = {"Agotado": "#6b7280", "Crítico": "#ef4444", "Bajo": "#f59e0b", "Saludable": "#10b981"}.get(estado, "#10b981")
    ganancia = (prod.get('precio_venta') or 0) - (prod.get('precio_coste') or 0)
    ganancia_color = "#10b981" if ganancia > 0 else "#ef4444"
    
    # 🔧 Estilos mejorados para tarjeta en edición
    if is_editing:
        # Badge de edición
        st.markdown('<div style="background: #00f0ff; color: #0f172a; padding: 2px 8px; border-radius: 4px; font-size: 9px; font-weight: 700; margin-bottom: 8px; display: inline-block;">✏️ EDITANDO</div>', unsafe_allow_html=True)
        border_color = "#00f0ff"
        bg_color = "rgba(0,240,255,0.08)"
        shadow = "0 0 30px rgba(0,240,255,0.4)"
    else:
        border_color = "rgba(255,255,255,0.1)"
        bg_color = "rgba(30,41,59,0.95)"
        shadow = "none"
    
    # Construir HTML de la tarjeta
    nombre = prod.get('nombre', '')
    sku = prod.get('sku', '')
    unidad = prod.get('unidad', 'ud')
    precio_coste = prod.get('precio_coste') or 0
    precio_venta = prod.get('precio_venta') or 0
    codigo_barras = prod.get('codigo_barras', '-') or '-'
    ubicacion = d['ubicacion']
    
    card_html = '<div style="background: linear-gradient(145deg, ' + bg_color + ', rgba(15,23,42,0.98)); border: 2px solid ' + border_color + '; border-radius: 12px; padding: 16px; margin-bottom: 8px; box-shadow: ' + shadow + ';">'
    card_html += '<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">'
    card_html += '<div><div style="font-size: 20px; font-weight: 700; color: #f8fafc; margin-bottom: 2px;">' + nombre + '</div>'
    card_html += '<div style="font-size: 15px; color: #64748b;">' + sku + ' | ' + unidad + '</div></div>'
    card_html += '<div style="background: ' + color_estado + '; padding: 3px 8px; border-radius: 12px; font-size: 15px; font-weight: 700; color: white;">' + estado + '</div></div>'
    card_html += '<div style="height: 1px; background: rgba(255,255,255,0.1); margin: 10px 0;"></div>'
    card_html += '<div style="font-size: 15px; color: #f8fafc; margin-bottom: 6px;">🏢 ' + prov_nombre + '</div>'
    card_html += '<div style="margin-bottom: 12px;">'
    card_html += '<div style="display: flex; justify-content: space-between; font-size: 15px; margin-bottom: 4px;">'
    card_html += '<span style="color: #64748b;">Stock</span>'
    card_html += '<span style="color: #e2e8f0; font-weight: 600;">' + str(stock) + ' / ' + str(max_s) + '</span></div>'
    card_html += '<div style="width: 100%; height: 10px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">'
    card_html += '<div style="width: ' + str(pct) + '%; height: 100%; background: ' + color_barra + '; border-radius: 2px;"></div></div></div>'
    card_html += '<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 10px; padding: 8px; background: rgba(0,0,0,0.2); border-radius: 6px;">'
    card_html += '<div style="text-align: center;"><div style="font-size: 12px; color: #f8fafc; margin-bottom: 2px;">COSTE</div>'
    card_html += '<div style="font-size: 20px; color: #f59e0b; font-weight: 700;">€' + f'{precio_coste:.2f}' + '</div></div>'
    card_html += '<div style="text-align: center;"><div style="font-size: 12px; color: #f8fafc; margin-bottom: 2px;">VENTA</div>'
    card_html += '<div style="font-size: 20px; color: #00f0ff; font-weight: 700;">€' + f'{precio_venta:.2f}' + '</div></div>'
    card_html += '<div style="text-align: center;"><div style="font-size: 12px; color: #f8fafc; margin-bottom: 2px;">GANANCIA</div>'
    card_html += '<div style="font-size: 20px; color: ' + ganancia_color + '; font-weight: 700;">€' + f'{ganancia:.2f}' + '</div></div></div>'
    card_html += '<div style="display: flex; justify-content: space-between; font-size: 15px; color: #f8fafc;">'
    card_html += '<span>📍 ' + ubicacion + '</span>'
    card_html += '<span>#' + codigo_barras + '</span></div></div>'
    
    st.markdown(card_html, unsafe_allow_html=True)
    
    # Botón editar
    if st.button("✏️ Editar", key=f"btn_edit_{pid}", use_container_width=True, 
                type="primary" if is_editing else "secondary"):
        st.session_state['editando_producto_id'] = pid
        st.rerun()


def _render_grid_productos(datos_inv_pagina, editable_id, proveedores, prov_options_by_name):
    """Renderiza el grid de tarjetas de productos."""
    num_cols = 4
    for i in range(0, len(datos_inv_pagina), num_cols):
        row_items = datos_inv_pagina[i:i+num_cols]
        cols = st.columns(num_cols)
        
        for idx, d in enumerate(row_items):
            with cols[idx]:
                is_editing = (d["producto"].get("id") == editable_id)
                _render_tarjeta_producto(d, is_editing, proveedores, editable_id, prov_options_by_name)


def _render_paginacion(total_paginas, pagina_actual, inicio, fin, total_items):
    """Renderiza controles de paginación."""
    if total_paginas > 1:
        st.markdown("---")
        col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
        with col_pag1:
            if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, use_container_width=True):
                st.session_state['pagina_inv'] = pagina_actual - 1
                st.rerun()
        with col_pag2:
            st.markdown(f"<p style='text-align: center; color: #94a3b8; margin: 0;'>Página {pagina_actual} de {total_paginas} | Mostrando {inicio+1}-{fin} de {total_items}</p>", unsafe_allow_html=True)
        with col_pag3:
            if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, use_container_width=True):
                st.session_state['pagina_inv'] = pagina_actual + 1
                st.rerun()


def _render_formulario_edicion(prod_a_editar, proveedores, productos, editable_id, prov_options_by_name):
    """Renderiza el formulario de edición de producto."""
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
            _render_formulario_nuevo_proveedor(editable_id, proveedores)
            nuevo_proveedor = prov_actual_nombre
    
    # Validaciones
    errores_edit = []
    if nuevo_sku != sku_actual:
        errores_edit = validar_sku(nuevo_sku, productos, editable_id)
    
    # 🔧 NUEVO: Checkbox de confirmación antes de guardar
    cambios_realizados = (nuevo_sku != sku_actual) or (nuevo_proveedor != prov_actual_nombre)
    
    if cambios_realizados and not errores_edit:
        st.markdown("<div style='background: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b; border-radius: 8px; padding: 12px; margin: 15px 0;'>", unsafe_allow_html=True)
        st.markdown("**⚠️ Cambios detectados:**")
        if nuevo_sku != sku_actual:
            st.markdown(f"- SKU: `{sku_actual}` → `{nuevo_sku}`")
        if nuevo_proveedor != prov_actual_nombre:
            st.markdown(f"- Proveedor: `{prov_actual_nombre}` → `{nuevo_proveedor}`")
        st.markdown("</div>", unsafe_allow_html=True)
        
        confirmar_cambios = st.checkbox("✅ He revisado y confirmo los cambios", key="confirmar_cambios_inv")
    else:
        confirmar_cambios = True
    
    col_btn_guardar, col_btn_cancel = st.columns([1, 4])
    with col_btn_guardar:
        btn_guardar = st.button("💾 Guardar cambios", type="primary", use_container_width=True, 
                            disabled=len(errores_edit) > 0 or (cambios_realizados and not confirmar_cambios), 
                            key="btn_save_edit_inv")
        if errores_edit:
            st.caption(f"⚠️ {', '.join(errores_edit)}")
        elif cambios_realizados and not confirmar_cambios:
            st.caption("⚠️ Confirma los cambios para guardar")
    with col_btn_cancel:
        if st.button("❌ Cancelar", use_container_width=True, key="btn_cancel_edit_inv"):
            del st.session_state['editando_producto_id']
            if 'confirmar_cambios_inv' in st.session_state:
                del st.session_state['confirmar_cambios_inv']
            st.rerun()
    
    if btn_guardar:
        # 🔧 FIX: Validar explícitamente que se confirmaron los cambios antes de guardar
        if cambios_realizados and not confirmar_cambios:
            st.error("❌ Por favor, marca la casilla 'He revisado y confirmo los cambios' antes de guardar")
            st.stop()
        else:
            _guardar_cambios_producto(editable_id, nuevo_sku, nuevo_proveedor, prov_options_by_name)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("---")


def _render_formulario_nuevo_proveedor(editable_id, proveedores):
    """Renderiza formulario para crear nuevo proveedor."""
    st.markdown("<div style='background:rgba(0,240,255,0.1);padding:10px;border-radius:8px;margin-top:5px;'>", unsafe_allow_html=True)
    nuevo_prov_nombre = st.text_input("Nombre nuevo *", key="new_prov_nom_inv", placeholder="Nombre del proveedor")
    nuevo_prov_email = st.text_input("Email nuevo *", key="new_prov_email_inv", placeholder="email@ejemplo.com")
    nuevo_prov_telefono = st.text_input("Teléfono", key="new_prov_tel_inv", placeholder="600 000 000")
    
    email_valido, email_error = validar_email_proveedor(nuevo_prov_email, proveedores)
    if not email_valido:
        st.caption(f"⚠️ {email_error}")
        btn_crear_disabled = True
    else:
        btn_crear_disabled = False
    
    if st.button("💾 Crear y usar", key="btn_new_prov_inv", use_container_width=True, type="secondary", disabled=btn_crear_disabled):
        if nuevo_prov_nombre and nuevo_prov_email:
            with st.spinner("⏳ Creando proveedor..."):
                try:
                    prov_data = {"nombre": nuevo_prov_nombre, "email": nuevo_prov_email, "telefono": nuevo_prov_telefono or None}
                    result = api_post("/api/v1/proveedores", prov_data)
                    
                    if result and isinstance(result, dict) and "id" in result:
                        nuevo_prov_id = result.get("id")
                        data_prov = {"proveedor_id": nuevo_prov_id}
                        resultado_asignacion = api_put(f"/api/v1/productos/{editable_id}", data_prov)
                        
                        if resultado_asignacion and "error" not in str(resultado_asignacion).lower():
                            _get_inventario_data.clear()
                            st.success(f"✅ Proveedor '{nuevo_prov_nombre}' creado y asignado")
                            del st.session_state['editando_producto_id']
                            st.rerun()
                        else:
                            error_msg = "Error al asignar proveedor al producto"
                            if isinstance(resultado_asignacion, dict) and "error" in resultado_asignacion:
                                error_msg = resultado_asignacion["error"]
                            st.error(f"❌ {error_msg}")
                            st.warning("⚠️ El proveedor se creó pero no se pudo asignar.")
                    else:
                        error_msg = "Error desconocido al crear proveedor"
                        if isinstance(result, dict) and "error" in result:
                            error_msg = result["error"]
                        st.error(f"❌ {error_msg}")
                except Exception as e:
                    st.error(f"❌ Error inesperado: {str(e)}")
                    st.info("💡 Verifica tu conexión o contacta soporte")
    st.markdown("</div>", unsafe_allow_html=True)


def _guardar_cambios_producto(editable_id, nuevo_sku, nuevo_proveedor, prov_options_by_name):
    """Guarda los cambios de un producto editado."""
    nuevo_prov_id = prov_options_by_name.get(nuevo_proveedor) if nuevo_proveedor != "Sin proveedor" else None
    
    datos_actualizar = {
        "sku": nuevo_sku,
        "proveedor_id": nuevo_prov_id
    }
    
    with st.spinner("💾 Guardando cambios..."):
        try:
            resultado = api_put(f"/api/v1/productos/{editable_id}", datos_actualizar)
            
            if resultado and "error" not in str(resultado).lower():
                _get_inventario_data.clear()
                st.success("✅ Cambios guardados correctamente")
                del st.session_state['editando_producto_id']
                if 'confirmar_cambios_inv' in st.session_state:
                    del st.session_state['confirmar_cambios_inv']
                st.rerun()
            else:
                error_msg = resultado.get("error", "Error desconocido del servidor") if isinstance(resultado, dict) else "Error al actualizar"
                st.error(f"❌ {error_msg}")
        except Exception as e:
            st.error(f"❌ Error inesperado: {str(e)}")
            st.info("💡 Por favor, intenta de nuevo o contacta soporte si el problema persiste")


def render():
    """Función principal - Renderiza la vista de inventario."""
    st.markdown("<h2>📦 Inventario</h2>", unsafe_allow_html=True)
    
    # Obtener datos
    inventarios, productos, proveedores = _get_inventario_data()
    datos_inv = preparar_datos_inventario(inventarios, productos)
    prov_options_by_name = {p.get("nombre"): p.get("id") for p in proveedores}
    
    # Filtros
    busqueda, filtro_estado, ordenar = _render_filtros(productos)
    datos_inv = _aplicar_filtros(datos_inv, busqueda, filtro_estado)
    datos_inv = ordenar_inventario(datos_inv, ordenar)
    
    # Header con contador y exportar
    col_contador, col_export = st.columns([4, 1])
    with col_contador:
        st.markdown(f"<span style='color: #00f0ff; font-weight: 600;'>{len(datos_inv)}</span> <span style='color: #94a3b8;'> productos</span>", unsafe_allow_html=True)
    with col_export:
        _render_exportar(datos_inv)
    
    st.markdown("---")
    
    # Verificar edición activa
    editable_id = st.session_state.get('editando_producto_id', None)
    prod_a_editar = None
    if editable_id:
        prod_a_editar = next((d for d in datos_inv if d["producto"].get("id") == editable_id), None)
    
    # 🔧 NUEVO: Auto-scroll al formulario de edición
    if prod_a_editar:
        st.markdown("<div id='formulario-edicion'></div>", unsafe_allow_html=True)
        st.markdown("""
        <script>
            // Scroll suave al formulario de edición
            setTimeout(function() {
                const formulario = document.getElementById('formulario-edicion');
                if (formulario) {
                    formulario.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 100);
        </script>
        """, unsafe_allow_html=True)
        
        _render_formulario_edicion(prod_a_editar, proveedores, productos, editable_id, prov_options_by_name)
    
    # Paginación
    productos_por_pagina = 8
    total_paginas = max(1, (len(datos_inv) + productos_por_pagina - 1) // productos_por_pagina)
    
    if 'pagina_inv' not in st.session_state:
        st.session_state['pagina_inv'] = 1
    
    pagina_actual = min(st.session_state['pagina_inv'], total_paginas)
    inicio = (pagina_actual - 1) * productos_por_pagina
    fin = min(inicio + productos_por_pagina, len(datos_inv))
    datos_inv_pagina = datos_inv[inicio:fin]
    
    # Grid de productos
    _render_grid_productos(datos_inv_pagina, editable_id, proveedores, prov_options_by_name)
    
    # Paginación
    _render_paginacion(total_paginas, pagina_actual, inicio, fin, len(datos_inv))
    
    # 🔧 NUEVO: Botón volver arriba
    if prod_a_editar:
        st.markdown("---")
        col_volver, _ = st.columns([1, 5])
        with col_volver:
            if st.button("⬆️ Volver al formulario", use_container_width=True, type="secondary"):
                st.markdown("""
                <script>
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                </script>
                """, unsafe_allow_html=True)
                st.rerun()
