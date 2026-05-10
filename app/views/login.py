"""
Pagina de Login para Streamlit
Autenticacion JWT contra la API
"""
import streamlit as st
import requests
from app.config import API_URL


def render():
    """Renderiza la pantalla de login."""
    st.markdown("""
    <style>
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: rgba(15,23,42,0.8);
        border-radius: 16px;
        border: 1px solid rgba(0,240,255,0.2);
        margin-top: 10vh;
    }
    .login-title {
        background: linear-gradient(90deg, #00f0ff, #8b5cf6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .login-subtitle {
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 0.95rem;
    }
    </style>
    <div class="login-container">
        <div class="login-title">MarkeTTalento</div>
        <div class="login-subtitle">Inventario Inteligente con ML</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("👤 Usuario", placeholder="admin", key="login_user")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="••••••", key="login_pass")

        if st.button("Iniciar Sesión", type="primary", use_container_width=True):
            if not username or not password:
                st.error("Introduce usuario y contraseña")
                return

            with st.spinner("Autenticando..."):
                try:
                    r = requests.post(
                        f"{API_URL}/api/v1/auth/login",
                        data={"username": username, "password": password},
                        timeout=10
                    )
                    if r.status_code == 200:
                        data = r.json()
                        st.session_state["auth_token"] = data["access_token"]
                        st.session_state["auth_user"] = data["usuario"]
                        st.success(f"Bienvenido, {data['usuario']['nombre_completo'] or username}")
                        st.rerun()
                    elif r.status_code == 401:
                        st.error("Usuario o contraseña incorrectos")
                    else:
                        st.error(f"Error del servidor: {r.status_code}")
                except requests.ConnectionError:
                    st.error("❌ No se pudo conectar con la API. Asegúrate de que está corriendo.")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("""
        <div style="text-align:center; margin-top:1rem; color:#64748b; font-size:0.8rem;">
            <p>Usuario por defecto: <strong>admin</strong> / <strong>admin123</strong></p>
        </div>
        """, unsafe_allow_html=True)
