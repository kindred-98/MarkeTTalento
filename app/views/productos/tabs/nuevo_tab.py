"""Nuevo producto tab"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data
from app.logic.producto import get_descripcion_default, preparar_producto_data
from app.utils.api import api_post
from app.components.success_modal import show_success_modal


def render():
    """Renderiza el formulario de nuevo producto."""
    form_version = st.session_state.get('form_version', 0)

    st.markdown("<h4 style='color: #3b82f6;'>➕ Nuevo Producto</h4>", unsafe_allow_html=True)

    productos, _, categorias, proveedores = get_productos_data()
    nombres_existentes = [p.get("nombre", "").lower() for p in productos]
    skus_existentes = [p.get("sku", "").lower() for p in productos]
    barras_existentes = [p.get("codigo_barras", "").lower() for p in productos if p.get("codigo_barras")]

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sku = st.text_input("SKU *", placeholder="PROD-001", key=f"new_sku_{form_version}")
    with c2:
        nombre = st.text_input("Nombre *", placeholder="Leche Entera", key=f"new_nombre_{form_version}")
    with c3:
        precio = st.number_input("Precio Venta € *", min_value=0.0, value=0.0, step=0.01, key=f"new_precio_{form_version}")
    with c4:
        precio_coste = st.number_input("Precio Coste €", min_value=0.0, value=0.0, key=f"new_precio_coste_{form_version}")

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        unidad = st.selectbox("Unidad *", ["unidad", "kg", "litro", "paquete", "caja", "botella"], key=f"new_unidad_{form_version}")
    with c6:
        cat_options = {c.get("nombre"): c.get("id") for c in categorias}
        categoria_nombre = st.selectbox("Categoría *", list(cat_options.keys()), key=f"new_cat_{form_version}")
        categoria_id = cat_options.get(categoria_nombre)
    with c7:
        codigo_barras = st.text_input("Código de barras", key=f"new_codigo_barras_{form_version}")
    with c8:
        tiempo_repo = st.number_input("Días reposición", min_value=1, value=3, key=f"new_tiempo_{form_version}")

    c9, c10, c11, c12 = st.columns(4)
    with c9:
        prov_options = {p.get("nombre", "Sin nombre"): p.get("id") for p in proveedores}
        prov_options["Sin proveedor"] = None
        prov_options["➕ Nuevo proveedor"] = "nuevo"
        proveedor_nombre = st.selectbox("Proveedor", list(prov_options.keys()), key=f"new_proveedor_{form_version}")
        proveedor_id = prov_options.get(proveedor_nombre)

        if proveedor_id == "nuevo":
            st.markdown("<div style='background:rgba(0,240,255,0.1);padding:10px;border-radius:8px;margin-top:5px;'>", unsafe_allow_html=True)
            st.markdown("<span style='color:#3b82f6;font-size:12px;'>Nuevo proveedor</span>", unsafe_allow_html=True)
            nuevo_prov_nombre = st.text_input("Nombre *", key=f"new_prov_nombre_{form_version}", label_visibility="collapsed", placeholder="Nombre del proveedor")
            nuevo_prov_email = st.text_input("Email *", key=f"new_prov_email_{form_version}", label_visibility="collapsed", placeholder="email@ejemplo.com")
            nuevo_prov_telefono = st.text_input("Teléfono", key=f"new_prov_telefono_{form_version}", label_visibility="collapsed", placeholder="600 000 000")

            if st.button("💾 Guardar proveedor", key=f"btnGuardarProv_{form_version}", width="stretch", type="secondary"):
                if nuevo_prov_nombre and nuevo_prov_email:
                    prov_data = {
                        "nombre": nuevo_prov_nombre,
                        "email": nuevo_prov_email,
                        "telefono": nuevo_prov_telefono or None,
                        "contacto": None
                    }
                    resultado = api_post("/api/v1/proveedores", prov_data, authenticated=False)
                    if resultado and not resultado.get("error"):
                        st.success(f"✅ Proveedor '{nuevo_prov_nombre}' creado")
                        st.session_state['form_version'] = form_version + 1
                        st.rerun()
                    else:
                        st.error("❌ Error al crear proveedor")
                else:
                    st.warning("⚠️ Nombre y email son obligatorios")
            st.markdown("</div>", unsafe_allow_html=True)
            proveedor_id = None
    with c10:
        unidad_ingreso = st.number_input("Cantidad inicial *", min_value=0, value=10, key=f"new_unidad_ingreso_{form_version}")
    with c11:
        stock_max = st.number_input("Stock máximo *", min_value=1, value=100, key=f"new_stock_max_{form_version}")
    with c12:
        st.number_input("Stock mínimo", min_value=0, value=0, disabled=True, key=f"new_stock_min_{form_version}")
        stock_min = 0

    c13, c14 = st.columns([2, 1])
    with c13:
        descripcion = st.text_area("Descripción", key=f"new_descripcion_{form_version}", height=80)
    with c14:
        st.markdown("<label style='color: #94a3b8; font-size: 12px;'>📷 Foto</label>", unsafe_allow_html=True)
        imagen_subida = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key=f"new_imagen_{form_version}", label_visibility="collapsed")
        if imagen_subida:
            st.image(imagen_subida, width=100)

    errores = []
    if not sku:
        errores.append("SKU obligatorio")
    elif len(sku) < 4:
        errores.append("SKU mínimo 4 caracteres")
    elif len(sku) > 20:
        errores.append("SKU máximo 20 caracteres")
    elif sku.lower() in skus_existentes:
        errores.append("SKU duplicado")

    if not nombre:
        errores.append("Nombre obligatorio")
    elif len(nombre) > 50:
        errores.append("Nombre máximo 50 caracteres")
    elif nombre.lower() in nombres_existentes:
        errores.append("Nombre duplicado")

    if precio < 0.01:
        errores.append("Precio inválido")

    if precio_coste > 0 and precio_coste >= precio:
        errores.append("Coste debe ser menor que venta")

    if not categoria_id:
        errores.append("Sin categoría")

    if stock_max <= 0:
        errores.append("Stock máx inválido")

    if unidad_ingreso > stock_max:
        errores.append("Cant. > stock máx")

    if codigo_barras and codigo_barras.lower() in barras_existentes:
        errores.append("Barras duplicado")

    campos_ok = len(errores) == 0

    col_btn, col_info = st.columns([3, 1])
    with col_btn:
        if st.button("💾 Crear producto", type="primary", width="stretch", disabled=not campos_ok, key=f"btn_crear_{form_version}"):
            errores_click = []
            if not sku or len(sku) < 4 or len(sku) > 20 or sku.lower() in skus_existentes:
                errores_click.append("SKU")
            if not nombre or len(nombre) > 50 or nombre.lower() in nombres_existentes:
                errores_click.append("Nombre")
            if precio < 0.01:
                errores_click.append("Precio")
            if not categoria_id:
                errores_click.append("Categoría")
            if stock_max <= 0 or unidad_ingreso > stock_max:
                errores_click.append("Stock")
            if precio_coste > 0 and precio_coste >= precio:
                errores_click.append("Coste")
            if codigo_barras and codigo_barras.lower() in barras_existentes:
                errores_click.append("Barras")

            if errores_click:
                st.error(f"❌ Corrige: {', '.join(errores_click)}")
                st.stop()

            imagen_url = None
            if imagen_subida:
                os.makedirs("docs/img_productos", exist_ok=True)
                extension = imagen_subida.name.split('.')[-1]
                nombre_imagen = f"{sku.replace(' ', '_').replace('/', '_')}_{form_version}.{extension}"
                ruta_imagen = f"docs/img_productos/{nombre_imagen}"
                with open(ruta_imagen, "wb") as f:
                    f.write(imagen_subida.getbuffer())
                imagen_url = ruta_imagen

            data = preparar_producto_data(
                sku=sku, nombre=nombre, precio_venta=precio, unidad=unidad,
                stock_maximo=stock_max, categoria_id=categoria_id,
                codigo_barras=codigo_barras, precio_coste=precio_coste,
                proveedor_id=proveedor_id, descripcion=descripcion or get_descripcion_default(nombre),
                imagen_url=imagen_url, cantidad_inicial=unidad_ingreso,
                unidad_ingreso=unidad_ingreso, tiempo_reposicion=tiempo_repo,
                stock_minimo=stock_min
            )

            resultado = api_post("/api/v1/productos", data, authenticated=False)
            if resultado and not resultado.get("error"):
                get_productos_data.clear()
                show_success_modal("¡Producto creado!", f"{nombre} registrado en catálogo", duracion=3)
                st.session_state['form_version'] = form_version + 1
                st.rerun()
            else:
                st.error("❌ Error al crear el producto")

    with col_info:
        if errores:
            st.caption(f"⚠️ {len(errores)} error(es): {', '.join(errores[:2])}")
        else:
            st.caption("✅ Listo para crear")