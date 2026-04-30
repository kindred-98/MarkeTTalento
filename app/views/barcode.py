"""
Página de Barcode
"""
import streamlit as st
from app.utils.api import api_get


def render():
    """Renderiza la página de escaneo de códigos de barras."""
    st.markdown("<h2>🔍 Escáner de Códigos de Barras</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(139,92,246,0.1), rgba(236,72,153,0.1)); padding: 20px; border-radius: 15px; border: 1px solid rgba(139,92,246,0.3); margin-bottom: 20px;">
        <h4 style="color: #8b5cf6; margin: 0;">📱 Escanea o ingresa un código de barras</h4>
        <p style="color: #94a3b8; margin: 10px 0 0 0;">Busca productos por su código de barras</p>
    </div>
    """, unsafe_allow_html=True)
    
    codigo = st.text_input("Código de barras", placeholder="Ej: 7622210449283")
    
    if codigo:
        productos = api_get("/api/v1/productos")
        
        encontrado = None
        for p in productos:
            if p.get("codigo_barras") == codigo:
                encontrado = p
                break
        
        if encontrado:
            st.success("✅ Producto encontrado")
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                if encontrado.get("imagen_url"):
                    st.image(encontrado.get("imagen_url"), width=200)
                else:
                    st.markdown("<div style='width: 200px; height: 200px; background: rgba(0,240,255,0.1); border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 4rem;'>📦</div>", unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="background: rgba(26,35,50,0.8); border: 1px solid rgba(0,240,255,0.2); border-radius: 16px; padding: 20px;">
                    <h3 style="color: #00f0ff; margin: 0 0 10px 0;">{encontrado.get('nombre', 'Producto')}</h3>
                    <p style="color: #94a3b8; margin: 5px 0;"><strong>SKU:</strong> {encontrado.get('sku', 'N/A')}</p>
                    <p style="color: #94a3b8; margin: 5px 0;"><strong>Precio:</strong> <span style="color: #00f0ff; font-size: 1.5rem; font-weight: 600;">€{encontrado.get('precio_venta', 0):.2f}</span></p>
                    <p style="color: #94a3b8; margin: 5px 0;"><strong>Unidad:</strong> {encontrado.get('unidad', 'unidad')}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.error("❌ Producto no encontrado")
            
            # Sugerir crear producto
            st.info("💡 ¿Quieres crear este producto? Ve a la sección **Productos** > **Nuevo**")
    
    # Historial de escaneos (simulado con session_state)
    st.markdown("---")
    st.markdown("<h4>📜 Escaneos recientes</h4>", unsafe_allow_html=True)
    
    if 'escaneos_recientes' not in st.session_state:
        st.session_state['escaneos_recientes'] = []
    
    if not st.session_state['escaneos_recientes']:
        st.caption("No hay escaneos recientes")
    else:
        for escaneo in st.session_state['escaneos_recientes'][-5:]:
            st.caption(f"🔍 {escaneo}")
