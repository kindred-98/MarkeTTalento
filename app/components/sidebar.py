"""
Componente de Sidebar para navegación
"""
import html
import streamlit as st
from app.utils.state import get_menu, set_menu

# Etiquetas de UI (sin emojis) — valores internos sin cambiar para compatibilidad con main.py
_NAV_OPTIONS: list[tuple[str, str]] = [
    ("Dashboard", "🏠 Dashboard"),
    ("Productos", "📦 Productos"),
    ("Inventario", "📊 Inventario"),
    ("Ventas", "💰 Ventas"),
    ("Predicciones", "🔮 Predicciones"),
    ("Inspector", "🔍 Inspector"),
    ("Documentación API", "📚 API Docs"),
]
_NAV_LABELS = [pair[0] for pair in _NAV_OPTIONS]
_NAV_LABEL_TO_MENU = {pair[0]: pair[1] for pair in _NAV_OPTIONS}


def _on_sidebar_nav_change():
    label = st.session_state.get("sidebar_nav")
    if label and label in _NAV_LABEL_TO_MENU:
        set_menu(_NAV_LABEL_TO_MENU[label])


def render_sidebar():
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-title">MarkeTTalento</div>
                <div class="sidebar-brand-sub">Panel operativo</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        menu = get_menu()

        user = st.session_state.get("auth_user", {})
        if user:
            nombre = html.escape(str(user.get("nombre_completo", user.get("username", "Usuario"))))
            rol = html.escape((str(user.get("rol") or "usuario")).replace("_", " ").title())
            st.markdown(
                f"""
                <div class="sidebar-user">
                    <div class="sidebar-user-name">{nombre}</div>
                    <div class="sidebar-user-role">{rol}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        try:
            nav_index = [_m for _, _m in _NAV_OPTIONS].index(menu)
        except ValueError:
            nav_index = 0

        st.markdown('<p class="sidebar-section-label">Navegación</p>', unsafe_allow_html=True)
        st.radio(
            "Navegación",
            options=_NAV_LABELS,
            index=nav_index,
            key="sidebar_nav",
            label_visibility="collapsed",
            on_change=_on_sidebar_nav_change,
        )

        st.markdown('<div class="sidebar-spacer-sm"></div>', unsafe_allow_html=True)

        if st.button("Cerrar sesión", key="sidebar_logout", width="stretch", type="secondary"):
            for key in ["auth_token", "auth_user", "api_conectada"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

        st.markdown(
            """
            <div class="sidebar-status-card">
                <span class="sidebar-status-dot" aria-hidden="true"></span>
                <span class="sidebar-status-text">Aplicación en ejecución</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        return menu
