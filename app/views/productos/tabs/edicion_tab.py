"""Edición de producto tab"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data
from app.utils.api import api_put, api_post
from app.components.success_modal import show_success_modal
from app.utils.state import set_editar_producto, clear_editar_producto


def render():
    """Renderiza el formulario de edición."""
    if 'producto_actualizado' in st.session_state and st.session_state['producto_actualizado']:
        st.success("✅ Producto actualizado con éxito")
        del st.session_state['producto_actualizado']

    if 'editar_producto' not in st.session_state or not st.session_state['editar_producto']:
        st.info("👆 Selecciona un producto del catálogo para editarlo")
        return

    prod_id = st.session_state['editar_producto']

    productos, inventarios, categorias, proveedores = get_productos_data()
    producto = next((p for p in productos if p.get('id') == prod_id), None)

    if not producto:
        st.error("Producto no encontrado")
        return

    inv = next((i for i in inventarios if i.get('producto_id') == prod_id), None)
    stock_actual = inv.get('cantidad', 0) if inv else 0

    st.markdown(f"<h4 style='color: #3b82f6;'>✏️ Editando: {producto.get('nombre', '')}</h4>", unsafe_allow_html=True)

    st.markdown(f"<div style='background:rgba(30,41,59,0.6);padding:8px 12px;border-radius:8px;margin-bottom:10px;display:inline-block;'><span style='color:#64748b;font-size:12px;'>SKU:</span> <span style='color:#3b82f6;font-weight:600;'>{producto.get('sku', 'N/A')}</span></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        edit_nombre = st.text_input("Nombre *", value=producto.get('nombre', ''), key="edit_nombre")
    with c2:
        edit_precio = st.number_input("P. Venta € *", min_value=0.0, value=float(producto.get('precio_venta', 0)), step=0.01, key="edit_precio")
    with c3:
        edit_coste = st.number_input("P. Coste €", min_value=0.0, value=float(producto.get('precio_coste') or 0), key="edit_coste")
    with c4:
        unidades = ["unidad", "kg", "litro", "paquete", "caja", "botella"]
        unidad_actual = producto.get('unidad', 'unidad')
        edit_unidad = st.selectbox("Unidad *", unidades, index=unidades.index(unidad_actual) if unidad_actual in unidades else 0, key="edit_unidad")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        cat_nombres = [c.get('nombre') for c in categorias]
        cat_actual = producto.get('categoria_id')
        cat_index = next((i for i, c in enumerate(categorias) if c.get('id') == cat_actual), 0)
        edit_cat = st.selectbox("Categoría *", cat_nombres, index=cat_index, key="edit_cat")
        edit_cat_id = next((c.get('id') for c in categorias if c.get('nombre') == edit_cat), 1)
    with c6:
        edit_codigo_barras = st.text_input("Cód. barras", value=producto.get('codigo_barras') or '', key="edit_codigo_barras")
    with c7:
        edit_tiempo = st.number_input("Días repo", min_value=1, value=int(producto.get('tiempo_reposicion', 3)), key="edit_tiempo")
    with c8:
        prov_options = {p.get("nombre", "Sin nombre"): p.get("id") for p in proveedores}
        prov_options["Sin proveedor"] = None
        prov_actual_id = producto.get('proveedor_id')
        prov_actual_nombre = next((p.get('nombre') for p in proveedores if p.get('id') == prov_actual_id), "Sin proveedor")
        prov_nombres_select = list(prov_options.keys())
        prov_index = prov_nombres_select.index(prov_actual_nombre) if prov_actual_nombre in prov_nombres_select else 0
        edit_proveedor_nombre = st.selectbox("Proveedor", prov_nombres_select, index=prov_index, key="edit_proveedor")
        edit_proveedor_id = prov_options.get(edit_proveedor_nombre)

    c9, c10, c11, c12 = st.columns(4)
    with c9:
        edit_stock_actual = st.number_input("Stock actual", min_value=0, value=int(stock_actual), key="edit_stock_actual")
    with c10:
        edit_ingreso = st.number_input("Ingreso", min_value=0, value=0, key="edit_ingreso")
    with c11:
        edit_stock_max = st.number_input("Stock máximo *", min_value=1, value=int(producto.get('stock_maximo', 100)), key="edit_stock_max")
    with c12:
        edit_descripcion = st.text_area("Descripción", value=producto.get('descripcion') or '', key="edit_descripcion", height=80)

    c13, c14 = st.columns([2, 1])
    with c13:
        st.markdown("<label style='color: #94a3b8; font-size: 12px;'>📷 Cambiar foto</label>", unsafe_allow_html=True)
        edit_imagen = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="edit_imagen", label_visibility="collapsed")
    with c14:
        img_actual = producto.get('imagen_url')
        if img_actual and os.path.exists(img_actual):
            st.image(img_actual, width=100, caption="Actual")

    errores = []
    if not edit_nombre:
        errores.append("Nombre obligatorio")
    elif len(edit_nombre) > 50:
        errores.append("Nombre máximo 50 caracteres")

    if edit_precio < 0.01:
        errores.append("Precio inválido")

    if edit_coste > 0 and edit_coste >= edit_precio:
        errores.append("Coste debe ser menor que venta")

    if not edit_cat_id:
        errores.append("Sin categoría")

    if edit_stock_max <= 0:
        errores.append("Stock máx inválido")

    if edit_stock_actual > edit_stock_max:
        errores.append("Stock actual > stock máx")

    if edit_ingreso > edit_stock_max:
        errores.append("Ingreso > stock máx")

    stock_resultante = edit_stock_actual + edit_ingreso
    if stock_resultante > edit_stock_max:
        errores.append(f"Stock resultante ({stock_resultante}) > stock máx ({edit_stock_max})")

    campos_ok = len(errores) == 0

    col_btn1, col_btn2, col_info = st.columns([2, 1, 1])
    with col_btn1:
        if st.button("💾 Guardar cambios", type="primary", width="stretch", disabled=not campos_ok, key="btnGuardarEdit"):
            errores_click = []
            if not edit_nombre or len(edit_nombre) > 50:
                errores_click.append("Nombre")
            if edit_precio < 0.01:
                errores_click.append("Precio")
            if edit_coste > 0 and edit_coste >= edit_precio:
                errores_click.append("Coste")
            if not edit_cat_id:
                errores_click.append("Categoría")
            if edit_stock_max <= 0:
                errores_click.append("Stock máx")
            if edit_stock_actual > edit_stock_max:
                errores_click.append("Stock actual > máx")
            if edit_ingreso > edit_stock_max:
                errores_click.append("Ingreso > máx")
            if edit_stock_actual + edit_ingreso > edit_stock_max:
                errores_click.append("Stock resultante > máx")

            if errores_click:
                st.error(f"❌ Corrige: {', '.join(errores_click)}")
                st.stop()

            nueva_imagen_url = producto.get('imagen_url')
            if edit_imagen:
                os.makedirs("docs/img_productos", exist_ok=True)
                extension = edit_imagen.name.split('.')[-1]
                nombre_imagen = f"{producto.get('sku', 'prod').replace(' ', '_').replace('/', '_')}_edit.{extension}"
                ruta_imagen = f"docs/img_productos/{nombre_imagen}"
                with open(ruta_imagen, "wb") as f:
                    f.write(edit_imagen.getbuffer())
                nueva_imagen_url = ruta_imagen

            data_edit = {
                "sku": producto.get('sku'),
                "nombre": edit_nombre,
                "codigo_barras": edit_codigo_barras if edit_codigo_barras else None,
                "precio_venta": edit_precio,
                "precio_coste": edit_coste if edit_coste > 0 else None,
                "unidad": edit_unidad,
                "stock_minimo": 0,
                "stock_maximo": edit_stock_max,
                "tiempo_reposicion": edit_tiempo,
                "categoria_id": edit_cat_id,
                "proveedor_id": edit_proveedor_id,
                "descripcion": edit_descripcion,
                "imagen_url": nueva_imagen_url
            }

            resultado = api_put(f"/api/v1/productos/{prod_id}", data_edit, authenticated=False)
            if resultado and not resultado.get("error"):
                nuevo_stock = edit_stock_actual + edit_ingreso
                api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo_stock}, authenticated=False)
                get_productos_data.clear()
                st.session_state['producto_actualizado'] = True
                clear_editar_producto()
                st.rerun()
            else:
                st.error("❌ Error al actualizar")

    with col_btn2:
        if st.button("❌ Cancelar", width="stretch", key="btnCancelarEdit"):
            clear_editar_producto()
            st.rerun()

    with col_info:
        if errores:
            st.caption(f"⚠️ {len(errores)} error(es)")
        else:
            st.caption("✅ Listo para guardar")