"""
Página de Productos - Optimizada
"""
import streamlit as st
import os
import pandas as pd
import hashlib
from datetime import datetime
from app.utils.api import api_get, api_post, api_put
from app.utils.helpers import to_excel, calcular_porcentaje, truncate_text
from app.utils.state import set_editar_producto, clear_editar_producto
from app.logic.producto import get_categoria_emoji, get_descripcion_default, preparar_producto_data
from app.logic.inventario import calcular_estado_stock
from app.components.success_modal import show_success_modal
from app.config import PRODUCTOS_POR_PAGINA


@st.cache_data(ttl=5, show_spinner=False)
def _get_productos_data():
    """Cachea datos de productos, inventarios, categorías y proveedores."""
    productos = api_get("/api/v1/productos", use_cache=False)
    inventarios = api_get("/api/v1/inventario", use_cache=False)
    categorias = api_get("/api/v1/categorias", use_cache=False)
    proveedores = api_get("/api/v1/proveedores", use_cache=False)
    return productos, inventarios, categorias, proveedores


def _get_estado_producto(prod_id, inventarios, productos):
    """Obtiene el estado de stock de un producto de forma eficiente."""
    inv = next((i for i in inventarios if i.get("producto_id") == prod_id), None)
    prod = next((p for p in productos if p.get("id") == prod_id), None)
    if inv and prod:
        return calcular_estado_stock(inv.get("cantidad", 0), prod.get("stock_maximo", 100) or 100)
    return "Saludable"


def _build_search_index(productos, inventarios):
    """Construye índice de búsqueda para filtrado rápido."""
    index = {}
    for p in productos:
        pid = p.get("id")
        nombre_lower = p.get("nombre", "").lower()
        sku_lower = p.get("sku", "").lower()
        estado = _get_estado_producto(pid, inventarios, productos)
        index[pid] = {
            "nombre": nombre_lower,
            "sku": sku_lower,
            "estado": estado,
            "categoria_id": p.get("categoria_id")
        }
    return index


def render():
    """Renderiza la página de productos optimizada."""
    st.markdown("<h2>📦 Gestión de Productos</h2>", unsafe_allow_html=True)
    
    # Inicializar tab activo solo si no existe
    if 'producto_tab_activo' not in st.session_state:
        st.session_state['producto_tab_activo'] = 0
    
    # Tabs de navegación - optimizado para evitar re-renders innecesarios
    col_nav1, col_nav2, col_nav3 = st.columns(3)
    
    # Usar session_state para controlar cambios de tab
    tab_previo = st.session_state.get('_tab_previo_productos', 0)
    tab_actual = st.session_state['producto_tab_activo']
    
    with col_nav1:
        btn_catalogo = st.button(
            "📋 Catálogo", 
            use_container_width=True, 
            type="primary" if tab_actual == 0 else "secondary",
            key="btn_catalogo_main"
        )
        if btn_catalogo and tab_actual != 0:
            st.session_state['producto_tab_activo'] = 0
            st.rerun()
    
    with col_nav2:
        btn_nuevo = st.button(
            "➕ Nuevo", 
            use_container_width=True,
            type="primary" if tab_actual == 1 else "secondary",
            key="btn_nuevo_main"
        )
        if btn_nuevo and tab_actual != 1:
            st.session_state['producto_tab_activo'] = 1
            st.rerun()
    
    with col_nav3:
        btn_edicion = st.button(
            "✏️ Edición", 
            use_container_width=True,
            type="primary" if tab_actual == 2 else "secondary",
            key="btn_edicion_main"
        )
        if btn_edicion and tab_actual != 2:
            st.session_state['producto_tab_activo'] = 2
            st.rerun()
    
    # Guardar tab previo
    st.session_state['_tab_previo_productos'] = tab_actual
    
    st.markdown("---")
    
    # Mostrar contenido según tab usando st.empty() para transiciones suaves
    content_placeholder = st.empty()
    
    if tab_actual == 0:
        with content_placeholder.container():
            render_catalogo()
    elif tab_actual == 1:
        with content_placeholder.container():
            render_nuevo()
    else:
        with content_placeholder.container():
            render_edicion()


def render_catalogo():
    """Renderiza el catálogo de productos optimizado."""
    # Usar placeholder para carga
    loading = st.empty()
    with loading:
        st.spinner("Cargando catálogo...")
    
    # Obtener datos con cache
    productos, inventarios, categorias, proveedores = _get_productos_data()
    
    # Construir índice de búsqueda (una sola vez)
    if '_search_index' not in st.session_state or st.session_state.get('_catalogo_hash') != hashlib.md5(str(len(productos)).encode()).hexdigest():
        st.session_state['_search_index'] = _build_search_index(productos, inventarios)
        st.session_state['_catalogo_hash'] = hashlib.md5(str(len(productos)).encode()).hexdigest()
    
    search_index = st.session_state['_search_index']
    
    loading.empty()
    
    # Filtros
    col_busq1, col_busq2, col_busq3 = st.columns([2, 1, 1])
    
    with col_busq1:
        busqueda = st.text_input("🔍 Buscar", placeholder="Nombre o SKU...", key="cat_busqueda")
    
    with col_busq2:
        cat_options = ["Todas"] + [c.get("nombre", "Sin categoría") for c in categorias]
        cat_filtro = st.selectbox("Categoría", cat_options, key="cat_categoria")
    
    with col_busq3:
        estado_options = ["Todos", "Agotado", "Crítico", "Bajo", "Saludable"]
        estado_filtro = st.selectbox("Estado", estado_options, key="cat_estado")
    
    # Filtrar usando índice (más rápido)
    productos_filtrados = productos
    
    if busqueda:
        busq_lower = busqueda.lower()
        productos_filtrados = [p for p in productos_filtrados 
                              if busq_lower in search_index.get(p.get("id"), {}).get("nombre", "") 
                              or busq_lower in search_index.get(p.get("id"), {}).get("sku", "")]
    
    if cat_filtro != "Todas":
        cat_id = next((c.get("id") for c in categorias if c.get("nombre") == cat_filtro), None)
        productos_filtrados = [p for p in productos_filtrados if p.get("categoria_id") == cat_id]
    
    if estado_filtro != "Todos":
        productos_filtrados = [p for p in productos_filtrados 
                              if search_index.get(p.get("id"), {}).get("estado") == estado_filtro]
    
    # Contador
    st.markdown(f"""
    <div style="padding: 10px 15px; background: rgba(0,240,255,0.1); border-radius: 10px; margin-bottom: 15px;">
        <span style="color: #00f0ff; font-weight: 600;">{len(productos_filtrados)}</span>
        <span style="color: #94a3b8;"> productos</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Exportar (solo si hay productos)
    if productos:
        # Preparar DataFrame una sola vez
        df_key = f"df_export_{len(productos)}"
        if df_key not in st.session_state:
            df_export = pd.DataFrame([{
                "ID": p.get("id"),
                "Nombre": p.get("nombre"),
                "SKU": p.get("sku"),
                "Precio Venta": p.get("precio_venta"),
                "Categoría": next((c.get("nombre") for c in categorias if c.get("id") == p.get("categoria_id")), "")
            } for p in productos])
            st.session_state[df_key] = df_export
        else:
            df_export = st.session_state[df_key]
        
        excel_data = to_excel(df_export)
        col_exp_izq, _, col_exp_der = st.columns([1, 2, 1])
        with col_exp_izq:
            st.download_button("📊 Excel", data=excel_data, file_name="productos.xlsx", use_container_width=True, key="btn_excel_cat")
        with col_exp_der:
            json_data = df_export.to_json(orient='records', indent=2)
            st.download_button("📄 JSON", data=json_data, file_name="productos.json", use_container_width=True, key="btn_json_cat")
    
    # Grid de productos con paginación lazy
    if productos_filtrados:
        # Mapas de color pre-calculados
        color_map = {
            "Agotado": "#6b7280",
            "Crítico": "#ef4444",
            "Bajo": "#f59e0b",
            "Saludable": "#10b981"
        }
        
        # Limitar cantidad mostrada inicialmente para rendimiento
        items_por_pagina = 10
        if 'cat_pagina' not in st.session_state:
            st.session_state['cat_pagina'] = 1
        
        total_paginas = max(1, (len(productos_filtrados) + items_por_pagina - 1) // items_por_pagina)
        pagina_actual = min(st.session_state['cat_pagina'], total_paginas)
        
        inicio = (pagina_actual - 1) * items_por_pagina
        fin = min(inicio + items_por_pagina, len(productos_filtrados))
        
        productos_pagina = productos_filtrados[inicio:fin]
        
        # Renderizar productos
        for prod in productos_pagina:
            pid = prod.get("id")
            inv = next((i for i in inventarios if i.get("producto_id") == pid), None)
            stock = inv.get("cantidad", 0) if inv else 0
            max_s = prod.get("stock_maximo", 100) or 100
            
            estado = search_index.get(pid, {}).get("estado", "Saludable")
            estado_color = color_map.get(estado, "#10b981")
            pct = calcular_porcentaje(stock, max_s)
            
            cat_nombre = next((c.get("nombre") for c in categorias if c.get("id") == prod.get("categoria_id")), "General")
            emoji = get_categoria_emoji(cat_nombre)
            
            with st.container():
                col_img, col_info = st.columns([1, 3])
                
                with col_img:
                    img_url = prod.get("imagen_url")
                    if img_url and os.path.exists(img_url):
                        try:
                            st.image(img_url, width=150)
                        except:
                            st.markdown(f"<div style='font-size: 3rem;'>{emoji}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size: 3rem;'>{emoji}</div>", unsafe_allow_html=True)
                
                with col_info:
                    if st.button("✏️ Editar", key=f"edit_{pid}"):
                        set_editar_producto(pid)
                        st.rerun()
                    
                    st.markdown(f"<h4 style='color: #00f0ff;'>{prod.get('nombre', 'Producto')}</h4>", unsafe_allow_html=True)
                    st.markdown(f"<h3>€{prod.get('precio_venta', 0):.2f}</h3>", unsafe_allow_html=True)
                    st.caption(f"📦 SKU: {prod.get('sku', 'N/A')} | 🏷️ {cat_nombre}")
                    st.write(f"📊 **Stock:** {stock} {prod.get('unidad', 'uds')}")
                    
                    st.progress(pct / 100)
                    st.caption(f"{pct:.0f}% del máximo")
                    
                    st.markdown(f"""
                    <div style="padding: 8px 16px; border-radius: 8px; text-align: center; 
                        background: {estado_color}; color: white; font-weight: 600;">
                        {estado}
                    </div>
                    """, unsafe_allow_html=True)
                
                st.markdown("---")
        
        # Controles de paginación
        if total_paginas > 1:
            col_pag1, col_pag2, col_pag3 = st.columns([1, 2, 1])
            with col_pag1:
                if st.button("⬅️ Anterior", disabled=pagina_actual <= 1, key="btn_pag_ant"):
                    st.session_state['cat_pagina'] = pagina_actual - 1
                    st.rerun()
            with col_pag2:
                st.markdown(f"<p style='text-align: center;'>Página {pagina_actual} de {total_paginas}</p>", unsafe_allow_html=True)
            with col_pag3:
                if st.button("Siguiente ➡️", disabled=pagina_actual >= total_paginas, key="btn_pag_sig"):
                    st.session_state['cat_pagina'] = pagina_actual + 1
                    st.rerun()
    else:
        st.info("No hay productos en el catálogo")


def render_nuevo():
    """Renderiza el formulario de nuevo producto optimizado."""
    form_version = st.session_state.get('form_version', 0)
    
    st.markdown("<h4 style='color: #00f0ff;'>➕ Nuevo Producto</h4>", unsafe_allow_html=True)
    
    # Cargar datos solo si es necesario
    categorias = api_get("/api/v1/categorias", use_cache=True)
    proveedores = api_get("/api/v1/proveedores", use_cache=True)
    productos_existentes = api_get("/api/v1/productos", use_cache=True)
    nombres_existentes = [p.get("nombre", "").lower() for p in productos_existentes]
    
    # Formulario con st.form para mejor rendimiento
    with st.form(f"form_nuevo_producto_{form_version}"):
        col1, col2 = st.columns(2)
        
        with col1:
            sku = st.text_input("Código SKU *", placeholder="Ej: PROD-001", key=f"new_sku_{form_version}")
            nombre = st.text_input("Nombre *", placeholder="Ej: Leche Entera", key=f"new_nombre_{form_version}")
            codigo_barras = st.text_input("Código de barras", key=f"new_codigo_barras_{form_version}")
            precio = st.number_input("Precio de venta (€) *", min_value=0.0, value=0.0, step=0.01, key=f"new_precio_{form_version}")
        
        with col2:
            unidad = st.selectbox("Unidad *", ["unidad", "kg", "litro", "paquete", "caja", "botella"], key=f"new_unidad_{form_version}")
            precio_coste = st.number_input("Precio de coste (€)", min_value=0.0, value=0.0, key=f"new_precio_coste_{form_version}")
            tiempo_repo = st.number_input("Días de reposición", min_value=1, value=3, key=f"new_tiempo_{form_version}")
            
            prov_options = {p.get("nombre", "Sin nombre"): p.get("id") for p in proveedores}
            prov_options["Sin proveedor"] = None
            proveedor_nombre = st.selectbox("Proveedor", list(prov_options.keys()), key=f"new_proveedor_{form_version}")
            proveedor_id = prov_options.get(proveedor_nombre)
        
        st.markdown("---")
        st.markdown("<h5 style='color: #00f0ff;'>📦 Configuración de Stock</h5>", unsafe_allow_html=True)
        
        col_stock1, col_stock2 = st.columns(2)
        with col_stock1:
            unidad_ingreso = st.number_input("📥 Unidad de ingreso *", min_value=1, value=10, key=f"new_unidad_ingreso_{form_version}")
        
        with col_stock2:
            stock_max = st.number_input("📦 Stock máximo *", min_value=0, value=100, key=f"new_stock_max_{form_version}")
        
        col3, col4 = st.columns(2)
        with col3:
            cat_options = {c.get("nombre"): c.get("id") for c in categorias}
            categoria_nombre = st.selectbox("Categoría *", list(cat_options.keys()), key=f"new_cat_{form_version}")
            categoria_id = cat_options.get(categoria_nombre)
            
            descripcion = st.text_area("Descripción", key=f"new_descripcion_{form_version}", height=100)
        
        with col4:
            st.markdown("<label style='color: #94a3b8;'>📷 Foto del producto</label>", unsafe_allow_html=True)
            imagen_subida = st.file_uploader("", type=['png', 'jpg', 'jpeg'], key=f"new_imagen_{form_version}", label_visibility="collapsed")
            
            if imagen_subida:
                st.image(imagen_subida, width=150, caption="Vista previa")
        
        # Validar campos
        campos_ok = sku and nombre and precio >= 0.01 and categoria_id and stock_max > 0 and unidad_ingreso >= 1
        
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            submitted = st.form_submit_button("💾 Crear producto", type="primary", use_container_width=True, disabled=not campos_ok)
        
        if not campos_ok:
            with col_btn2:
                st.caption("⚠️ Completa los campos obligatorios (*)")
    
    # Procesar fuera del form
    if submitted:
        if nombre.lower() in nombres_existentes:
            st.error("❌ Ya existe un producto con ese nombre")
        else:
            # Guardar imagen
            imagen_url = None
            if imagen_subida:
                os.makedirs("docs/productos", exist_ok=True)
                extension = imagen_subida.name.split('.')[-1]
                nombre_imagen = f"{sku.replace(' ', '_').replace('/', '_')}_{form_version}.{extension}"
                ruta_imagen = f"docs/productos/{nombre_imagen}"
                with open(ruta_imagen, "wb") as f:
                    f.write(imagen_subida.getbuffer())
                imagen_url = ruta_imagen
            
            data = preparar_producto_data(
                sku=sku,
                nombre=nombre,
                precio_venta=precio,
                unidad=unidad,
                stock_maximo=stock_max,
                categoria_id=categoria_id,
                codigo_barras=codigo_barras,
                precio_coste=precio_coste,
                proveedor_id=proveedor_id,
                descripcion=descripcion or get_descripcion_default(nombre),
                imagen_url=imagen_url,
                cantidad_inicial=unidad_ingreso,
                unidad_ingreso=unidad_ingreso,
                tiempo_reposicion=tiempo_repo
            )
            
            result = api_post("/api/v1/productos", data)
            if result:
                # Limpiar cache de productos
                _get_productos_data.clear()
                show_success_modal(
                    "¡Producto añadido exitosamente!",
                    "El producto ha sido registrado en el catálogo",
                    duracion=3
                )
                st.session_state['form_version'] = form_version + 1
                st.rerun()
            else:
                st.error("❌ Error al crear el producto")


def render_edicion():
    """Renderiza el formulario de edición de productos optimizado."""
    if 'producto_actualizado' in st.session_state and st.session_state['producto_actualizado']:
        st.success("✅ Producto actualizado con éxito")
        del st.session_state['producto_actualizado']
    
    if 'editar_producto' not in st.session_state or not st.session_state['editar_producto']:
        st.info("👆 Selecciona un producto del catálogo para editarlo")
        return
    
    prod_id = st.session_state['editar_producto']
    
    # Cargar datos con cache
    productos, inventarios, categorias, proveedores = _get_productos_data()
    producto = next((p for p in productos if p.get('id') == prod_id), None)
    
    if not producto:
        st.error("Producto no encontrado")
        return
    
    # Obtener stock actual
    inv = next((i for i in inventarios if i.get('producto_id') == prod_id), None)
    stock_actual = inv.get('cantidad', 0) if inv else 0
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, rgba(0,240,255,0.15), rgba(139,92,246,0.15)); 
                padding: 25px; border-radius: 15px; border: 1px solid rgba(0,240,255,0.4);
                box-shadow: 0 0 30px rgba(0,240,255,0.2); margin-bottom: 25px; text-align: center;">
        <h2 style="margin: 0; color: #00f0ff; text-shadow: 0 0 15px rgba(0,240,255,0.6); font-size: 1.8rem;">
            ✏️ Editando: {producto.get('nombre', '')}
        </h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Formulario de edición
    with st.form("form_edicion_producto"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"<label style='color: #94a3b8;'>SKU (no editable)</label><div style='background: rgba(30,41,59,0.8); padding: 10px; border-radius: 8px; color: #64748b;'>{producto.get('sku', 'N/A')}</div>", unsafe_allow_html=True)
            edit_nombre = st.text_input("Nombre *", value=producto.get('nombre', ''), key="edit_nombre")
            edit_codigo_barras = st.text_input("Código de barras", value=producto.get('codigo_barras') or '', key="edit_codigo_barras")
            edit_precio = st.number_input("Precio de venta (€) *", min_value=0.0, value=float(producto.get('precio_venta', 0)), step=0.01, key="edit_precio")
        
        with col2:
            unidad_actual = producto.get('unidad', 'unidad')
            unidades = ["unidad", "kg", "litro", "paquete", "caja", "botella"]
            edit_unidad = st.selectbox("Unidad *", unidades, index=unidades.index(unidad_actual) if unidad_actual in unidades else 0, key="edit_unidad")
            edit_coste = st.number_input("Precio de coste (€)", value=float(producto.get('precio_coste') or 0), key="edit_coste")
            edit_tiempo = st.number_input("Días de reposición", value=int(producto.get('tiempo_reposicion', 3)), key="edit_tiempo")
        
        st.markdown("---")
        st.markdown("<h5 style='color: #00f0ff;'>📦 Configuración de Stock</h5>", unsafe_allow_html=True)
        
        col_stock1, col_stock2 = st.columns(2)
        with col_stock1:
            edit_stock_actual = st.number_input("Stock actual", min_value=0, value=int(stock_actual), key="edit_stock_actual")
        with col_stock2:
            edit_ingreso = st.number_input("Ingreso (entrada)", min_value=0, value=0, key="edit_ingreso", help="Cantidad que está entrando al almacén")
        
        col_stock3, col_stock4 = st.columns(2)
        with col_stock3:
            st.markdown("<label style='color: #94a3b8;'>🔒 Stock mínimo</label><div style='background: rgba(30,41,59,0.6); padding: 15px; border-radius: 10px;'><div style='font-size: 1.5rem; color: #64748b;'>0</div></div>", unsafe_allow_html=True)
        with col_stock4:
            edit_stock_max = st.number_input("Stock máximo *", min_value=0, value=int(producto.get('stock_maximo', 100)), key="edit_stock_max")
        
        col3, col4 = st.columns(2)
        with col3:
            cat_nombres = [c.get('nombre') for c in categorias]
            cat_actual = producto.get('categoria_id')
            cat_index = next((i for i, c in enumerate(categorias) if c.get('id') == cat_actual), 0)
            edit_cat = st.selectbox("Categoría *", cat_nombres, index=cat_index, key="edit_cat")
            edit_cat_id = next((c.get('id') for c in categorias if c.get('nombre') == edit_cat), 1)
            
            edit_descripcion = st.text_area("Descripción", value=producto.get('descripcion') or '', key="edit_descripcion", height=100)
        
        with col4:
            img_actual = producto.get('imagen_url')
            if img_actual and os.path.exists(img_actual):
                st.image(img_actual, width=150, caption="Imagen actual")
            
            edit_imagen = st.file_uploader("Cambiar imagen", type=['png', 'jpg', 'jpeg'], key="edit_imagen")
            if edit_imagen:
                st.image(edit_imagen, width=150, caption="Nueva imagen")
        
        # Botones
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            campos_ok = edit_nombre and edit_precio >= 0.01 and edit_stock_max > 0 and edit_cat_id
            guardar = st.form_submit_button("💾 Guardar cambios", use_container_width=True, disabled=not campos_ok)
        
        with col_btn2:
            cancelar = st.form_submit_button("❌ Cancelar", use_container_width=True)
    
    # Procesar acciones fuera del form
    if cancelar:
        clear_editar_producto()
        st.rerun()
    
    if guardar:
        if edit_precio < 0.01:
            st.error("El precio debe ser mayor a 0")
        else:
            # Guardar nueva imagen
            nueva_imagen_url = producto.get('imagen_url')
            if edit_imagen:
                os.makedirs("docs/productos", exist_ok=True)
                extension = edit_imagen.name.split('.')[-1]
                nombre_imagen = f"{producto.get('sku', 'prod').replace(' ', '_').replace('/', '_')}_edit.{extension}"
                ruta_imagen = f"docs/productos/{nombre_imagen}"
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
                "unidad_ingreso": producto.get('unidad_ingreso', 10),
                "tiempo_reposicion": edit_tiempo,
                "categoria_id": edit_cat_id,
                "proveedor_id": None,
                "descripcion": edit_descripcion,
                "imagen_url": nueva_imagen_url
            }
            
            result = api_put(f"/api/v1/productos/{prod_id}", data_edit)
            if result and result.get('id'):
                # Actualizar stock
                nuevo_stock = edit_stock_actual + edit_ingreso
                api_post(f"/api/v1/inventario/{prod_id}", {"cantidad": nuevo_stock, "ubicacion": "Almacén A"})
                
                # Limpiar cache
                _get_productos_data.clear()
                
                st.session_state['producto_actualizado'] = True
                clear_editar_producto()
                st.rerun()
            else:
                st.error("Error al actualizar")
