"""Edición de producto tab"""
import streamlit as st
import os
from app.views.productos.data.getters import get_productos_data
from app.views.productos.utils.helpers import (
    UNIDADES,
    UNIDAD_POR_DEFECTO,
    STOCK_MAX_POR_DEFECTO,
    TIEMPO_REPOSICION_POR_DEFECTO,
    PRECIO_MINIMO,
    LONGITUD_NOMBRE_MAX,
    DIR_IMAGENES,
    SIN_PROVEEDOR,
    SIN_NOMBRE_PROVEEDOR,
    SIN_CATEGORIA,
    CATEGORIA_ID_POR_DEFECTO,
)
from app.db import DatabaseAccess
from app.utils.state import clear_editar_producto
from src.core.logging import log_success, log_error


def _mostrar_aviso_actualizacion():
    """Muestra y consume el aviso de producto actualizado."""
    if st.session_state.get('producto_actualizado'):
        st.success("✅ Producto actualizado con éxito")
        del st.session_state['producto_actualizado']


def _obtener_stock_actual(inventarios, prod_id):
    """Devuelve el stock actual del producto (0 si no hay inventario)."""
    inv = next((i for i in inventarios or [] if i.get('producto_id') == prod_id), None)
    if not inv or inv.get('cantidad') is None:
        return 0
    return inv.get('cantidad', 0)


def _cargar_producto(prod_id):
    """Carga los datos y devuelve (producto, stock_actual). None si no se puede editar."""
    try:
        productos, inventarios, categorias, proveedores = get_productos_data()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return None

    if not productos:
        st.error("No hay productos disponibles")
        return None

    producto = next((p for p in productos if p.get('id') == prod_id), None)
    if not producto:
        st.error("Producto no encontrado")
        return None

    return producto, _obtener_stock_actual(inventarios, prod_id), categorias, proveedores


def _selector_unidad(producto):
    """Muestra el selector de unidad con la unidad actual preseleccionada."""
    unidad_actual = producto.get('unidad', UNIDAD_POR_DEFECTO)
    index = UNIDADES.index(unidad_actual) if unidad_actual in UNIDADES else 0
    return st.selectbox("Unidad *", UNIDADES, index=index, key="edit_unidad")


def _selector_categoria(producto, categorias):
    """Muestra el selector de categoria. Devuelve el id de categoria elegido."""
    if not categorias:
        st.selectbox("Categoría *", [SIN_CATEGORIA], key="edit_cat")
        return CATEGORIA_ID_POR_DEFECTO

    cat_nombres = [c.get('nombre') for c in categorias]
    cat_actual = producto.get('categoria_id')
    cat_index = next((i for i, c in enumerate(categorias) if c.get('id') == cat_actual), 0)
    edit_cat = st.selectbox("Categoría *", cat_nombres, index=cat_index, key="edit_cat")
    return next((c.get('id') for c in categorias if c.get('nombre') == edit_cat), CATEGORIA_ID_POR_DEFECTO)


def _opciones_proveedor(proveedores):
    """Devuelve el mapeo nombre -> id de proveedor, incluyendo la opción sin proveedor."""
    prov_options = {p.get("nombre", SIN_NOMBRE_PROVEEDOR): p.get("id") for p in proveedores or []}
    prov_options[SIN_PROVEEDOR] = None
    return prov_options


def _selector_proveedor(producto, proveedores):
    """Muestra el selector de proveedor. Devuelve el id de proveedor elegido (o None)."""
    prov_options = _opciones_proveedor(proveedores)
    prov_nombres = list(prov_options.keys())

    prov_actual_id = producto.get('proveedor_id')
    prov_actual_nombre = next(
        (p.get('nombre') for p in proveedores or [] if p.get('id') == prov_actual_id),
        SIN_PROVEEDOR,
    )
    prov_index = prov_nombres.index(prov_actual_nombre) if prov_actual_nombre in prov_nombres else 0
    edit_proveedor = st.selectbox("Proveedor", prov_nombres, index=prov_index, key="edit_proveedor")
    return prov_options.get(edit_proveedor)


def _seccion_datos_basicos(producto):
    """Nombre, precios y unidad."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        edit_nombre = st.text_input("Nombre *", value=producto.get('nombre', ''), key="edit_nombre")
    with c2:
        edit_precio = st.number_input("P. Venta € *", min_value=0.0, value=float(producto.get('precio_venta', 0)), step=0.01, key="edit_precio")
    with c3:
        edit_coste = st.number_input("P. Coste €", min_value=0.0, value=float(producto.get('precio_coste') or 0), key="edit_coste")
    with c4:
        edit_unidad = _selector_unidad(producto)
    return edit_nombre, edit_precio, edit_coste, edit_unidad


def _seccion_clasificacion(producto, categorias, proveedores):
    """Categoría, código de barras, días de reposición y proveedor."""
    c5, c6, c7, c8 = st.columns(4)
    with c5:
        edit_cat_id = _selector_categoria(producto, categorias)
    with c6:
        edit_codigo_barras = st.text_input("Cód. barras", value=producto.get('codigo_barras') or '', key="edit_codigo_barras")
    with c7:
        edit_tiempo = st.number_input(
            "Días repo",
            min_value=1,
            value=int(producto.get('tiempo_reposicion', TIEMPO_REPOSICION_POR_DEFECTO) or TIEMPO_REPOSICION_POR_DEFECTO),
            key="edit_tiempo",
        )
    with c8:
        edit_proveedor_id = _selector_proveedor(producto, proveedores)
    return edit_cat_id, edit_codigo_barras, edit_tiempo, edit_proveedor_id


def _seccion_stock(producto, stock_actual):
    """Stock actual, ingreso, stock máximo y descripción."""
    c9, c10, c11, c12 = st.columns(4)
    with c9:
        edit_stock_actual = st.number_input("Stock actual", min_value=0, value=int(stock_actual), key="edit_stock_actual")
    with c10:
        edit_ingreso = st.number_input("Ingreso", min_value=0, value=0, key="edit_ingreso")
    with c11:
        edit_stock_max = st.number_input("Stock máximo *", min_value=1, value=int(producto.get('stock_maximo', STOCK_MAX_POR_DEFECTO)), key="edit_stock_max")
    with c12:
        edit_descripcion = st.text_area("Descripción", value=producto.get('descripcion') or '', key="edit_descripcion", height=80)
    return edit_stock_actual, edit_ingreso, edit_stock_max, edit_descripcion


def _seccion_imagen(producto):
    """Muestra el uploader de imagen y la imagen actual."""
    c13, c14 = st.columns([2, 1])
    with c13:
        st.markdown("<label style='color: #94a3b8; font-size: 12px;'>📷 Cambiar foto</label>", unsafe_allow_html=True)
        return st.file_uploader("", type=['png', 'jpg', 'jpeg'], key="edit_imagen", label_visibility="collapsed")
    with c14:
        img_actual = producto.get('imagen_url')
        if img_actual and os.path.exists(img_actual):
            st.image(img_actual, width=100, caption="Actual")


def _validar_edicion(campos):
    """Valida el formulario. Devuelve una lista de (campo, mensaje)."""
    errores = []

    nombre = campos["nombre"]
    if not nombre:
        errores.append(("Nombre", "Nombre obligatorio"))
    elif len(nombre) > LONGITUD_NOMBRE_MAX:
        errores.append(("Nombre", f"Nombre máximo {LONGITUD_NOMBRE_MAX} caracteres"))

    precio_venta = campos["precio_venta"]
    precio_coste = campos["precio_coste"]
    if precio_venta < PRECIO_MINIMO:
        errores.append(("Precio", "Precio inválido"))
    if precio_coste > 0 and precio_coste >= precio_venta:
        errores.append(("Coste", "Coste debe ser menor que venta"))

    if not campos["categoria_id"]:
        errores.append(("Categoría", SIN_CATEGORIA))

    stock_max = campos["stock_maximo"]
    stock_actual = campos["stock_actual"]
    ingreso = campos["ingreso"]
    resultante = stock_actual + ingreso

    if stock_max <= 0:
        errores.append(("Stock máx", "Stock máx inválido"))
    if stock_actual > stock_max:
        errores.append(("Stock actual > máx", "Stock actual > stock máx"))
    if ingreso > stock_max:
        errores.append(("Ingreso > máx", "Ingreso > stock máx"))
    if resultante > stock_max:
        errores.append((
            "Stock resultante > máx",
            f"Stock resultante ({resultante}) > stock máx ({stock_max})",
        ))

    return errores


def _guardar_imagen(edit_imagen, producto):
    """Guarda la imagen subida y devuelve su ruta, o None si no se subió ninguna."""
    if not edit_imagen:
        return None

    os.makedirs(DIR_IMAGENES, exist_ok=True)
    extension = edit_imagen.name.split('.')[-1]
    nombre_imagen = f"{producto.get('sku', 'prod').replace(' ', '_').replace('/', '_')}_edit.{extension}"
    ruta_imagen = f"{DIR_IMAGENES}/{nombre_imagen}"
    with open(ruta_imagen, "wb") as f:
        f.write(edit_imagen.getbuffer())
    return ruta_imagen


def _actualizar_stock(db, prod_id, nuevo_stock):
    """Actualiza la cantidad en inventario del producto."""
    from src.dominio.entidades.entidades import Inventario
    inv = db.session.query(Inventario).filter_by(producto_id=prod_id).first()
    if inv:
        inv.cantidad = nuevo_stock
        db.session.commit()


def _persistir_edicion(prod_id, producto, data_edit, nuevo_stock):
    """Guarda el producto y su stock. Devuelve True si se actualizó."""
    db = DatabaseAccess()
    try:
        if not db.actualizar_producto(prod_id, data_edit):
            st.error("❌ Error al actualizar")
            log_error("productos", f"Error al actualizar producto {prod_id}")
            return False

        _actualizar_stock(db, prod_id, nuevo_stock)
        get_productos_data.clear()
        st.session_state['producto_actualizado'] = True
        log_success(f"Producto actualizado: {data_edit['nombre']}")
        return True
    finally:
        db.close()


def _construir_datos_edicion(producto, campos, nueva_imagen_url):
    """Construye el diccionario de actualización del producto."""
    return {
        "sku": producto.get('sku'),
        "nombre": campos["nombre"],
        "codigo_barras": campos["codigo_barras"] or None,
        "precio_venta": campos["precio_venta"],
        "precio_coste": campos["precio_coste"] if campos["precio_coste"] > 0 else None,
        "unidad": campos["unidad"],
        "stock_minimo": 0,
        "stock_maximo": campos["stock_maximo"],
        "tiempo_reposicion": campos["tiempo_reposicion"],
        "categoria_id": campos["categoria_id"],
        "proveedor_id": campos["proveedor_id"],
        "descripcion": campos["descripcion"],
        "imagen_url": nueva_imagen_url,
    }


def _render_botones(errores, on_guardar):
    """Renderiza guardar/cancelar y el resumen de errores."""
    col_btn1, col_btn2, col_info = st.columns([2, 1, 1])

    with col_btn1:
        if st.button("💾 Guardar cambios", type="primary", width="stretch", disabled=bool(errores), key="btnGuardarEdit"):
            on_guardar()

    with col_btn2:
        if st.button("❌ Cancelar", width="stretch", key="btnCancelarEdit"):
            clear_editar_producto()
            st.rerun()

    with col_info:
        if errores:
            st.caption(f"⚠️ {len(errores)} error(es)")
        else:
            st.caption("✅ Listo para guardar")


def _guardar_edicion(prod_id, producto, campos, edit_imagen):
    """Valida de nuevo, guarda la imagen y persiste la edicion."""
    errores = _validar_edicion(campos)
    if errores:
        st.error(f"❌ Corrige: {', '.join(campo for campo, _ in errores)}")
        st.stop()

    nueva_imagen_url = _guardar_imagen(edit_imagen, producto) or producto.get('imagen_url')
    data_edit = _construir_datos_edicion(producto, campos, nueva_imagen_url)
    nuevo_stock = campos["stock_actual"] + campos["ingreso"]

    if _persistir_edicion(prod_id, producto, data_edit, nuevo_stock):
        clear_editar_producto()
        st.rerun()


def render():
    """Renderiza el formulario de edición."""
    _mostrar_aviso_actualizacion()

    if not st.session_state.get('editar_producto'):
        st.info("👆 Selecciona un producto del catálogo para editarlo")
        return

    prod_id = st.session_state['editar_producto']
    datos = _cargar_producto(prod_id)
    if datos is None:
        return

    producto, stock_actual, categorias, proveedores = datos

    st.markdown(f"<h4 style='color: #3b82f6;'>✏️ Editando: {producto.get('nombre', '')}</h4>", unsafe_allow_html=True)
    st.markdown(f"<div style='background:rgba(30,41,59,0.6);padding:8px 12px;border-radius:8px;margin-bottom:10px;display:inline-block;'><span style='color:#64748b;font-size:12px;'>SKU:</span> <span style='color:#3b82f6;font-weight:600;'>{producto.get('sku', 'N/A')}</span></div>", unsafe_allow_html=True)

    edit_nombre, edit_precio, edit_coste, edit_unidad = _seccion_datos_basicos(producto)
    edit_cat_id, edit_codigo_barras, edit_tiempo, edit_proveedor_id = _seccion_clasificacion(producto, categorias, proveedores)
    edit_stock_actual, edit_ingreso, edit_stock_max, edit_descripcion = _seccion_stock(producto, stock_actual)
    edit_imagen = _seccion_imagen(producto)

    campos = {
        "nombre": edit_nombre,
        "precio_venta": edit_precio,
        "precio_coste": edit_coste,
        "unidad": edit_unidad,
        "categoria_id": edit_cat_id,
        "codigo_barras": edit_codigo_barras,
        "tiempo_reposicion": edit_tiempo,
        "proveedor_id": edit_proveedor_id,
        "stock_actual": edit_stock_actual,
        "ingreso": edit_ingreso,
        "stock_maximo": edit_stock_max,
        "descripcion": edit_descripcion,
    }

    errores = _validar_edicion(campos)

    _render_botones(errores, lambda: _guardar_edicion(prod_id, producto, campos, edit_imagen))