"""
Gestión del estado de la aplicación (session_state)
"""
import streamlit as st
from typing import Any, Optional


def init_session_state():
    """Inicializa todas las variables de session_state necesarias."""
    defaults = {
        # API
        'api_conectada': False,
        
        # Menú
        'menu_activo': "🏠 Dashboard",
        'menu_previo': None,  # Para detectar cambio de pestaña
        
        # Productos
        'form_version': 0,
        'producto_tab_activo': 0,  # Catálogo | Nuevo | Edición
        'producto_actualizado': False,
        'editar_producto': None,
        
        # Dashboard filtros
        'filtro_agotados': True,
        'filtro_criticos': True,
        'filtro_bajos': True,
        'filtro_saludables': True,
        'pagina_stock': 1,
        
        # Dashboard métricas calculadas (cache de cálculos)
        'dashboard_agotados': 0,
        'dashboard_criticos': 0,
        'dashboard_bajos': 0,
        'dashboard_saludables': 0,
        'dashboard_datos_hash': None,  # Hash para invalidar cache
        
        # Cache de datos cargados
        '_cache_productos': None,
        '_cache_inventarios': None,
        '_cache_categorias': None,
        '_cache_proveedores': None,
        '_cache_timestamp': 0,
        
        # UI State - prevención de recargas innecesarias
        '_last_render_tab': None,
        '_render_count': 0,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_menu(menu: str):
    """Cambia el menú activo."""
    st.session_state['menu_previo'] = st.session_state.get('menu_activo')
    st.session_state['menu_activo'] = menu


def get_menu() -> str:
    """Obtiene el menú activo."""
    return st.session_state.get('menu_activo', "🏠 Dashboard")


def is_tab_changed() -> bool:
    """Detecta si el usuario cambió de pestaña."""
    return st.session_state.get('menu_previo') != st.session_state.get('menu_activo')


def reset_producto_form():
    """Resetea el formulario de productos."""
    st.session_state['form_version'] = st.session_state.get('form_version', 0) + 1


def set_editar_producto(producto_id: int):
    """Establece el producto a editar."""
    st.session_state['editar_producto'] = producto_id
    st.session_state['producto_tab_activo'] = 2


def clear_editar_producto():
    """Limpia el estado de edición de producto."""
    if 'editar_producto' in st.session_state:
        del st.session_state['editar_producto']


def get_filtro_dashboard() -> dict:
    """Obtiene los filtros del dashboard."""
    return {
        'agotados': st.session_state.get('filtro_agotados', True),
        'criticos': st.session_state.get('filtro_criticos', True),
        'bajos': st.session_state.get('filtro_bajos', True),
        'saludables': st.session_state.get('filtro_saludables', True),
    }


def get_cached_data(key: str) -> Optional[Any]:
    """Obtiene datos cacheados del session_state."""
    return st.session_state.get(f'_cache_{key}')


def set_cached_data(key: str, data: Any):
    """Guarda datos en cache del session_state."""
    st.session_state[f'_cache_{key}'] = data


def invalidate_cache():
    """Invalida todos los datos cacheados."""
    cache_keys = ['_cache_productos', '_cache_inventarios', '_cache_categorias', '_cache_proveedores']
    for key in cache_keys:
        if key in st.session_state:
            st.session_state[key] = None


def update_dashboard_metrics(agotados: int, criticos: int, bajos: int, saludables: int, datos_hash: str):
    """Actualiza las métricas del dashboard con hash para evitar recálculos."""
    st.session_state['dashboard_agotados'] = agotados
    st.session_state['dashboard_criticos'] = criticos
    st.session_state['dashboard_bajos'] = bajos
    st.session_state['dashboard_saludables'] = saludables
    st.session_state['dashboard_datos_hash'] = datos_hash


def get_dashboard_metrics() -> tuple:
    """Obtiene las métricas cacheadas del dashboard."""
    return (
        st.session_state.get('dashboard_agotados', 0),
        st.session_state.get('dashboard_criticos', 0),
        st.session_state.get('dashboard_bajos', 0),
        st.session_state.get('dashboard_saludables', 0),
        st.session_state.get('dashboard_datos_hash')
    )


# ============================================================================
# TPV - Estado del Terminal Punto de Venta
# ============================================================================

def init_tpv_state():
    """Inicializa el estado del TPV si no existe."""
    defaults = {
        'tpv_cajero': 'andres',
        'tpv_carrito': [],
        'tpv_categoria_activa': 'todos',
        'tpv_linea_seleccionada': None,
        'tpv_teclado_buffer': '',
        'tpv_mostrar_ticket': False,
        'tpv_ticket_reciente': None,
        'tpv_pagina_historial': 1,
        'tpv_filtro_historial_cajero': 'Todos',
        'tpv_filtro_historial_desde': None,
        'tpv_filtro_historial_hasta': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_tpv_carrito() -> list:
    """Obtiene el carrito actual del TPV."""
    return st.session_state.get('tpv_carrito', [])


def set_tpv_carrito(carrito: list):
    """Establece el carrito del TPV."""
    st.session_state['tpv_carrito'] = carrito


def limpiar_carrito():
    """Limpia el carrito y estado relacionado."""
    st.session_state['tpv_carrito'] = []
    st.session_state['tpv_linea_seleccionada'] = None
    st.session_state['tpv_teclado_buffer'] = ''
    st.session_state['tpv_mostrar_ticket'] = False
    st.session_state['tpv_ticket_reciente'] = None


def agregar_linea_carrito(producto: dict):
    """Agrega una línea al carrito o incrementa cantidad si ya existe."""
    carrito = get_tpv_carrito()
    prod_id = producto.get('id')
    
    for linea in carrito:
        if linea['producto_id'] == prod_id:
            linea['cantidad'] += 1
            linea['subtotal'] = round(linea['cantidad'] * linea['precio_unitario'], 2)
            set_tpv_carrito(carrito)
            return
    
    carrito.append({
        'producto_id': prod_id,
        'nombre': producto.get('nombre'),
        'precio_unitario': producto.get('precio_venta', 0),
        'cantidad': 1,
        'subtotal': producto.get('precio_venta', 0),
        'imagen_url': producto.get('imagen_url'),
    })
    set_tpv_carrito(carrito)


def actualizar_cantidad_linea(index: int, cantidad: int):
    """Actualiza la cantidad de una línea del carrito."""
    carrito = get_tpv_carrito()
    if 0 <= index < len(carrito):
        if cantidad <= 0:
            carrito.pop(index)
        else:
            carrito[index]['cantidad'] = cantidad
            carrito[index]['subtotal'] = round(cantidad * carrito[index]['precio_unitario'], 2)
        set_tpv_carrito(carrito)
        st.session_state['tpv_linea_seleccionada'] = None
        st.session_state['tpv_teclado_buffer'] = ''


def calcular_total_carrito() -> float:
    """Calcula el total del carrito."""
    return round(sum(linea['subtotal'] for linea in get_tpv_carrito()), 2)


def get_cajeros() -> list:
    """Lista de cajeros disponibles."""
    return ["andres", "edu", "carlos", "alberto", "irrael", "YioQueSe", "fernando", "ernesto", "raul"]
