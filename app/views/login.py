"""
Página de Login para Streamlit
Autenticación directa contra SQLite
"""
import streamlit as st
from app.auth_local import autenticar_usuario


def render():
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
        <div class="login-subtitle">Inventario Inteligente</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("👤 Usuario", placeholder="admin", key="login_user")
        password = st.text_input("🔒 Contraseña", type="password", placeholder="••••••", key="login_pass")

        if st.button("Iniciar Sesión", type="primary", width="stretch"):
            if not username or not password:
                st.error("Introduce usuario y contraseña")
                return

            with st.spinner("Autenticando..."):
                try:
                    user = autenticar_usuario(username, password)
                    if user:
                        st.session_state["auth_token"] = f"local_{user['id']}"
                        st.session_state["auth_user"] = user
                        st.success(f"Bienvenido, {user.get('nombre_completo', username)}")
                        st.rerun()
                    else:
                        st.error("Usuario o contraseña incorrectos")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("""
        <div style="text-align:center; margin-top:1rem; color:#64748b; font-size:0.8rem;">
            <p>Usuario: <strong>admin</strong> / <strong>admin123</strong></p>
        </div>
        """, unsafe_allow_html=True)