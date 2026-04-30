"""
Página de Visión AI
"""
import streamlit as st
from app.utils.api import api_get, api_post
import requests
from app.config import API_URL


def render():
    """Renderiza la página de Visión AI."""
    st.markdown("<h2>📸 Visión Artificial</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, rgba(0,240,255,0.1), rgba(139,92,246,0.1)); padding: 20px; border-radius: 15px; border: 1px solid rgba(0,240,255,0.3); margin-bottom: 20px;">
        <h4 style="color: #00f0ff; margin: 0;">🤖 Detección Automática de Productos</h4>
        <p style="color: #94a3b8; margin: 10px 0 0 0;">Usa la cámara o sube una imagen para detectar productos automáticamente con IA</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Selector de fuente
    fuente = st.radio("Fuente de imagen:", ["📷 Cámara", "📁 Subir imagen"], horizontal=True)
    
    imagen = None
    
    if fuente == "📷 Cámara":
        imagen = st.camera_input("Captura una imagen")
    else:
        imagen = st.file_uploader("Sube una imagen", type=['jpg', 'jpeg', 'png'])
    
    if imagen:
        st.image(imagen, caption="Imagen capturada", use_container_width=True)
        
        if st.button("🔍 Analizar con IA", type="primary", use_container_width=True):
            with st.spinner("Analizando imagen con YOLOv8..."):
                try:
                    files = {"imagen": imagen.getvalue()}
                    response = requests.post(f"{API_URL}/api/v1/vision/analizar-y-actualizar", files=files, timeout=30)
                    
                    if response.status_code == 200:
                        resultado = response.json()
                        
                        st.success(f"✅ {resultado.get('mensaje', 'Análisis completado')}")
                        
                        # Mostrar detecciones
                        detecciones = resultado.get("detecciones", [])
                        if detecciones:
                            st.markdown("<h4>📦 Productos detectados:</h4>", unsafe_allow_html=True)
                            
                            for det in detecciones:
                                nombre = det.get("nombre", "Desconocido")
                                cantidad = det.get("cantidad", 1)
                                confianza = det.get("confianza", 0)
                                
                                st.markdown(f"""
                                <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); border-radius: 10px; padding: 15px; margin-bottom: 10px;">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <span style="font-size: 1.2rem; font-weight: 600; color: #f1f5f9;">{nombre}</span>
                                        <span style="background: rgba(16,185,129,0.2); color: #10b981; padding: 4px 12px; border-radius: 20px; font-size: 0.9rem;">Cantidad: {cantidad}</span>
                                    </div>
                                    <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 5px;">Confianza: {confianza:.0%}</div>
                                </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.warning("No se detectaron productos en la imagen")
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                
                except Exception as e:
                    st.error(f"❌ Error al analizar: {e}")
