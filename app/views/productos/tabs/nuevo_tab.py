"""Nuevo producto tab"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data
from app.views.productos.utils.helpers import (
    UNIDADES,
    STOCK_MAX_POR_DEFECTO,
    TIEMPO_REPOSICION_POR_DEFECTO,
    PRECIO_MINIMO,
    LONGITUD_NOMBRE_MAX,
    LONGITUD_SKU_MIN,
    LONGITUD_SKU_MAX,
    DIR_IMAGENES,
    SIN_PROVEEDOR,
    SIN_NOMBRE_PROVEEDOR,
    NUEVO_PROVEEDOR,
    PROVEEDOR_NUEVO,
    SIN_CATEGORIA,
    CATEGORIA_ID_POR_DEFECTO,
)
from app.logic.producto import get_descripcion_default, preparar_producto_data
from app.db import DatabaseAccess
from app.components.success_modal import show_success_modal
from src.core.logging import log_success, log_error

STOCK_MIN_POR_DEFECTO = 0
CANTIDAD_INICIAL_POR_DEFECTO = 10
DIV_CLOSE = "</div>"


def _valores_existentes(productos):
    """Recopila nombre, sku y código de barras ya registrados (en minúsculas)."""
    return {
        "nombres": [p.get("nombre", "").lower() for p in productos],
        "skus": [p.get("sku", "").lower() for p in productos],
        "barras": [p.get("codigo_barras", "").lower() for p in productos if p.get("codigo_barras")],
    }


def _seccion_identificacion(form_version):
    """SKU, nombre, precio de venta y precio de coste."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sku = st.text_input("SKU *", placeholder="PROD-001", key=f"new_sku_{form_version}")
    with c2:
        nombre = st.text_input("Nombre *", placeholder="Leche Entera", key=f"new_nombre_{form_version}")
    with c3:
        precio = st.number_input("Precio Venta € *", min_value=0.0, value=0.0, step=0.01, key=f"new_precio_{form_version}")
    with c4:
        precio_coste = st.number_input("Precio Coste €", min_value=0.0, value=0.0, key=f"new_precio_coste_{form_version}")
    return sku, nombre, precio, precio_coste


def _selector_categoria(form_version, categorias):
    """Muestra el selector de categoria. Devuelve su id."""
    cat_options = {c.get("nombre"): c.get("id") for c in categorias}
    if not cat_options:
        st.selectbox("Categoría *", [SIN_CATEGORIA], key=f"new_cat_{form_version}")
        return CATEGORIA_ID_POR_DEFECTO

    categoria_nombre = st.selectbox("Categoría *", list(cat_options.keys()), key=f"new_cat_{form_version}")
    return cat_options.get(categoria_nombre, CATEGORIA_ID_POR_DEFECTO)


def _crear_proveedor(form_version, nombre, email, telefono):
    """Crea un proveedor nuevo. Devuelve True si se creó."""
    if not nombre or not email:
        st.warning("⚠️ Nombre y email son obligatorios")
        return False

    db = DatabaseAccess()
    try:
        resultado = db.crear_proveedor({
            "nombre": nombre,
            "email": email,
            "telefono": telefono or None,
            "contacto": None,
        })
        if not resultado:
            st.error("❌ Error al crear proveedor")
            return False
        st.success(f"✅ Proveedor '{nombre}' creado")
        return True
    finally:
        db.close()


def _render_formulario_nuevo_proveedor(form_version):
    """Muestra el formulario inline para dar de alta un proveedor."""
    st.markdown("<div style='background:rgba(0,240,255,0.1);padding:10px;border-radius:8px;margin-top:5px;'>", unsafe_allow_html=True)
    st.markdown("<span style='color:#3b82f6;font-size:12px;'>Nuevo proveedor</span>", unsafe_allow_html=True)
    nombre = st.text_input("Nombre *", key=f"new_prov_nombre_{form_version}", label_visibility="collapsed", placeholder="Nombre del proveedor")
    email = st.text_input("Email *", key=f"new_prov_email_{form_version}", label_visibility="collapsed", placeholder="email@ejemplo.com")
    telefono = st.text_input("Teléfono", key=f"new_prov_telefono_{form_version}", label_visibility="collapsed", placeholder="600 000 000")

    if st.button("💾 Guardar proveedor", key=f"btnGuardarProv_{form_version}", width="stretch", type="secondary"):
        if _crear_proveedor(form_version, nombre, email, telefono):
            st.session_state['form_version'] = form_version + 1
            st.rerun()

    st.markdown(DIV_CLOSE, unsafe_allow_html=True)


def _seccion_clasificacion(form_version, categorias, proveedores):
    """Unidad, categoría, código de barras y días de reposición."""
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        unidad = st.selectbox("Unidad *", UNIDADES, key=f"new_unidad_{form_version}")
    with c6:
        categoria_id = _selector_categoria(form_version, categorias)
    with c7:
        codigo_barras = st.text_input("Código de barras", key=f"new_codigo_barras_{form_version}")
    with c8:
        tiempo_repo = st.number_input(
            "Días reposición",
            min_value=1,
            value=TIEMPO_REPOSICION_POR_DEFECTO,
            key=f"new_tiempo_{form_version}",
        )
    return unidad, categoria_id, codigo_barras, tiempo_repo


def _selector_proveedor(form_version, proveedores):
    """Muestra el selector de proveedor. Devuelve su id, o None si es uno nuevo."""
    prov_options = {p.get("nombre", SIN_NOMBRE_PROVEEDOR): p.get("id") for p in proveedores or []}
    prov_options[SIN_PROVEEDOR] = None
    prov_options[NUEVO_PROVEEDOR] = PROVEEDOR_NUEVO

    proveedor_nombre = st.selectbox("Proveedor", list(prov_options.keys()), key=f"new_proveedor_{form_version}")
    proveedor_id = prov_options.get(proveedor_nombre)

    if proveedor_id != PROVEEDOR_NUEVO:
        return proveedor_id

    _render_formulario_nuevo_proveedor(form_version)
    return None


def _seccion_stock(form_version, proveedores):
    """Proveedor, cantidad inicial, stock máximo y stock mínimo (fijo)."""
    c9, c10, c11, c12 = st.columns(4)
    with c9:
        proveedor_id = _selector_proveedor(form_version, proveedores)
    with c10:
        unidad_ingreso = st.number_input("Cantidad inicial *", min_value=0, value=CANTIDAD_INICIAL_POR_DEFECTO, key=f"new_unidad_ingreso_{form_version}")
    with c11:
        stock_max = st.number_input("Stock máximo *", min_value=1, value=STOCK_MAX_POR_DEFECTO, key=f"new_stock_max_{form_version}")
    with c12:
        st.number_input("Stock mínimo", min_value=0, value=STOCK_MIN_POR_DEFECTO, disabled=True, key=f"new_stock_min_{form_version}")
    return proveedor_id, unidad_ingreso, stock_max


def _seccion_descripcion_e_imagen(form_version):
    """Descripción y subida de foto."""
    c13, c14 = st.columns([2, 1])
    with c13:
        descripcion = st.text_area("Descripción", key=f"new_descripcion_{form_version}", height=80)
    with c14:
        st.markdown("<label style='color: #94a3b8; font-size: 12px;'>📷 Foto</label>", unsafe_allow_html=True)
        imagen_subida = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key=f"new_imagen_{form_version}", label_visibility="collapsed")
        if imagen_subida:
            st.image(imagen_subida, width=100)
    return descripcion, imagen_subida


def _validar_alta(campos, existentes):
    """Valida el formulario de alta. Devuelve una lista de (campo, mensaje)."""
    errores = []

    sku = campos["sku"]
    if not sku:
        errores.append(("SKU", "SKU obligatorio"))
    elif len(sku) < LONGITUD_SKU_MIN:
        errores.append(("SKU", f"SKU mínimo {LONGITUD_SKU_MIN} caracteres"))
    elif len(sku) > LONGITUD_SKU_MAX:
        errores.append(("SKU", f"SKU máximo {LONGITUD_SKU_MAX} caracteres"))
    elif sku.lower() in existentes["skus"]:
        errores.append(("SKU", "SKU duplicado"))

    nombre = campos["nombre"]
    if not nombre:
        errores.append(("Nombre", "Nombre obligatorio"))
    elif len(nombre) > LONGITUD_NOMBRE_MAX:
        errores.append(("Nombre", f"Nombre máximo {LONGITUD_NOMBRE_MAX} caracteres"))
    elif nombre.lower() in existentes["nombres"]:
        errores.append(("Nombre", "Nombre duplicado"))

    precio = campos["precio"]
    precio_coste = campos["precio_coste"]
    if precio < PRECIO_MINIMO:
        errores.append(("Precio", "Precio inválido"))
    if precio_coste > 0 and precio_coste >= precio:
        errores.append(("Coste", "Coste debe ser menor que venta"))

    if not campos["categoria_id"]:
        errores.append(("Categoría", SIN_CATEGORIA))

    stock_max = campos["stock_max"]
    if stock_max <= 0:
        errores.append(("Stock", "Stock máx inválido"))
    if campos["cantidad_inicial"] > stock_max:
        errores.append(("Stock", "Cant. > stock máx"))

    barras = campos["codigo_barras"]
    if barras and barras.lower() in existentes["barras"]:
        errores.append(("Barras", "Barras duplicado"))

    return errores


def _guardar_imagen(imagen_subida, sku, form_version):
    """Guarda la imagen subida y devuelve su ruta, o None si no se subió ninguna."""
    if not imagen_subida:
        return None

    os.makedirs(DIR_IMAGENES, exist_ok=True)
    extension = imagen_subida.name.split('.')[-1]
    nombre_imagen = f"{sku.replace(' ', '_').replace('/', '_')}_{form_version}.{extension}"
    ruta_imagen = f"{DIR_IMAGENES}/{nombre_imagen}"
    with open(ruta_imagen, "wb") as f:
        f.write(imagen_subida.getbuffer())
    return ruta_imagen


def _crear_producto(campos):
    """Persiste el nuevo producto. Devuelve True si se creó."""
    data = preparar_producto_data(
        sku=campos["sku"],
        nombre=campos["nombre"],
        precio_venta=campos["precio"],
        unidad=campos["unidad"],
        stock_maximo=campos["stock_max"],
        categoria_id=campos["categoria_id"],
        codigo_barras=campos["codigo_barras"],
        precio_coste=campos["precio_coste"],
        proveedor_id=campos["proveedor_id"],
        descripcion=campos["descripcion"] or get_descripcion_default(campos["nombre"]),
        imagen_url=campos["imagen_url"],
        cantidad_inicial=campos["cantidad_inicial"],
        unidad_ingreso=campos["cantidad_inicial"],
        tiempo_reposicion=campos["tiempo_reposicion"],
        stock_minimo=STOCK_MIN_POR_DEFECTO,
    )

    db = DatabaseAccess()
    try:
        if not db.crear_producto(data):
            st.error("❌ Error al crear el producto")
            log_error("productos", f"Error al crear producto {campos['sku']}")
            return False

        get_productos_data.clear()
        show_success_modal("¡Producto creado!", f"{campos['nombre']} registrado en catálogo", duracion=3)
        log_success(f"Producto creado: {campos['nombre']} (SKU: {campos['sku']})")
        return True
    finally:
        db.close()


def _guardar_alta(campos, form_version, imagen_subida, existentes):
    """Valida de nuevo y crea el producto."""
    errores = _validar_alta(campos, existentes)
    if errores:
        st.error(f"❌ Corrige: {', '.join(campo for campo, _ in errores)}")
        st.stop()

    campos["imagen_url"] = _guardar_imagen(imagen_subida, campos["sku"], form_version)

    if _crear_producto(campos):
        st.session_state['form_version'] = form_version + 1
        st.rerun()


def _render_botones(campos, form_version, imagen_subida, existentes, errores):
    """Renderiza el botón de crear y el resumen de errores."""
    col_btn, col_info = st.columns([3, 1])

    with col_btn:
        if st.button("💾 Crear producto", type="primary", width="stretch", disabled=bool(errores), key=f"btn_crear_{form_version}"):
            _guardar_alta(campos, form_version, imagen_subida, existentes)

    with col_info:
        if errores:
            st.caption(f"⚠️ {len(errores)} error(es): {', '.join(mensaje for _, mensaje in errores[:2])}")
        else:
            st.caption("✅ Listo para crear")


def render():
    """Renderiza el formulario de nuevo producto."""
    form_version = st.session_state.get('form_version', 0)

    st.markdown("<h4 style='color: #3b82f6;'>➕ Nuevo Producto</h4>", unsafe_allow_html=True)

    productos, _, categorias, proveedores = get_productos_data()
    existentes = _valores_existentes(productos)

    sku, nombre, precio, precio_coste = _seccion_identificacion(form_version)
    unidad, categoria_id, codigo_barras, tiempo_repo = _seccion_clasificacion(form_version, categorias, proveedores)
    proveedor_id, unidad_ingreso, stock_max = _seccion_stock(form_version, proveedores)
    descripcion, imagen_subida = _seccion_descripcion_e_imagen(form_version)

    campos = {
        "sku": sku,
        "nombre": nombre,
        "precio": precio,
        "precio_coste": precio_coste,
        "unidad": unidad,
        "categoria_id": categoria_id,
        "codigo_barras": codigo_barras,
        "tiempo_reposicion": tiempo_repo,
        "proveedor_id": proveedor_id,
        "cantidad_inicial": unidad_ingreso,
        "stock_max": stock_max,
        "descripcion": descripcion,
        "imagen_url": None,
    }

    errores = _validar_alta(campos, existentes)

    _render_botones(campos, form_version, imagen_subida, existentes, errores)