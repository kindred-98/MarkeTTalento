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
        'producto_tab_activo': 0,  # 0 = Catálogo, 1 = Nuevo, 2 = Edición
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
