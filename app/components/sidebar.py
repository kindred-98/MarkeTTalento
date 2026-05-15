"""
Componente de Sidebar para navegación
"""
import html
import streamlit as st

from app.config import API_URL as _API_URL_CFG
from app.utils.api_health import refresh_api_health_cache
from app.utils.state import get_menu, set_menu

# Etiquetas de UI (sin emojis) — valores internos sin cambiar para compatibilidad con main.py
_NAV_OPTIONS: list[tuple[str, str]] = [
    ("Dashboard", "🏠 Dashboard"),
    ("Productos", "📦 Productos"),
    ("Inventario", "📊 Inventario"),
    ("Ventas", "💰 Ventas"),
    ("Predicciones", "🔮 Predicciones"),
    ("Inspector", "🔍 Inspector"),
    ("Logs", "📋 Logs"),
    ("Documentación API", " API Docs"),
]
_NAV_LABELS = [pair[0] for pair in _NAV_OPTIONS]
_NAV_LABEL_TO_MENU = {pair[0]: pair[1] for pair in _NAV_OPTIONS}


def _render_api_status_sidebar():
    """Estado de la API FastAPI (HTTP): auto cada ~25 s o al pulsar Comprobar."""
    force = st.button("Comprobar API", key="sidebar_check_api", width="stretch")
    cache = refresh_api_health_cache(force=force)
    ok = cache.get("ok", False)
    err = cache.get("error") or ""
    ms = cache.get("latency_ms")
    url = html.escape(str(cache.get("url") or _API_URL_CFG))
    lat_txt = f"{ms} ms" if ms is not None else "—"
    state_cls = "sidebar-api-card--ok" if ok else "sidebar-api-card--down"
    dot_cls = "sidebar-api-dot--ok" if ok else "sidebar-api-dot--down"
    title = "API en línea" if ok else "API no disponible"
    err_html = f'<div class="sidebar-api-err">{html.escape(err)}</div>' if (not ok and err) else ""

    st.markdown(
        f"""
        <div class="sidebar-api-card {state_cls}">
            <div class="sidebar-api-card__row">
                <span class="sidebar-api-dot {dot_cls}" aria-hidden="true"></span>
                <div class="sidebar-api-card__text">
                    <div class="sidebar-api-card__title">{html.escape(title)}</div>
                    <div class="sidebar-api-card__meta">Latencia: {html.escape(lat_txt)}</div>
                </div>
            </div>
            <div class="sidebar-api-card__url" title="{url}">{url}</div>
            {err_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


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

        st.markdown('<p class="sidebar-section-label">Conectividad</p>', unsafe_allow_html=True)
        _render_api_status_sidebar()

        st.markdown('<div class="sidebar-spacer-sm"></div>', unsafe_allow_html=True)

        if st.button("Cerrar sesión", key="sidebar_logout", width="stretch", type="secondary"):
            for key in ["auth_token", "auth_user", "api_conectada", "_api_health_cache"]:
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
