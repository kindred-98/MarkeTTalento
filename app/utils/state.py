"""
Gestión del estado de la aplicación (session_state)
"""
import streamlit as st


def init_session_state():
    """Inicializa todas las variables de session_state necesarias."""
    defaults = {
        # API
        'api_conectada': False,
        
        # Menú
        'menu_activo': "🏠 Dashboard",
        
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
        
        # Dashboard métricas calculadas
        'dashboard_agotados': 0,
        'dashboard_criticos': 0,
        'dashboard_bajos': 0,
        'dashboard_saludables': 0,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def set_menu(menu: str):
    """Cambia el menú activo."""
    st.session_state['menu_activo'] = menu


def get_menu() -> str:
    """Obtiene el menú activo."""
    return st.session_state.get('menu_activo', "🏠 Dashboard")


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
