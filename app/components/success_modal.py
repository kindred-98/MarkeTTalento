"""
Componente de modal de éxito
"""
import streamlit as st
import time


def show_success_modal(titulo: str, mensaje: str, duracion: int = 3):
    """
    Muestra un modal de éxito con animación.
    
    Args:
        titulo: Título del mensaje
        mensaje: Mensaje descriptivo
        duracion: Tiempo en segundos antes de cerrar
    """
    # Mostrar globos
    st.balloons()
    
    # Mostrar modal
    st.markdown(f"""
    <div id="success-modal" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                background: rgba(0, 0, 0, 0.7); z-index: 9999; display: flex; 
                align-items: center; justify-content: center; animation: fadeIn 0.3s ease;">
        <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.95), rgba(10, 14, 23, 0.98)); 
                    padding: 50px 60px; border-radius: 20px; border: 3px solid rgba(16, 185, 129, 0.8);
                    text-align: center; box-shadow: 0 0 60px rgba(16, 185, 129, 0.5), 0 0 100px rgba(16, 185, 129, 0.3);
                    animation: scaleIn 0.5s ease; max-width: 500px; margin: 20px;">
            <div style="font-size: 5rem; margin-bottom: 20px; animation: bounce 1s ease infinite;">🎉</div>
            <div style="font-size: 2rem; font-weight: 700; color: #10b981; margin-bottom: 15px; text-shadow: 0 0 20px rgba(16, 185, 129, 0.5);">
                {titulo}
            </div>
            <div style="font-size: 1.1rem; color: #94a3b8; margin-bottom: 25px;">
                {mensaje}
            </div>
            <div style="font-size: 0.9rem; color: #64748b; font-style: italic;">
                Redirigiendo en {duracion} segundos...
            </div>
        </div>
    </div>
    <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        @keyframes scaleIn {{
            from {{ opacity: 0; transform: scale(0.8); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0); }}
            50% {{ transform: translateY(-10px); }}
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Esperar y retornar
    time.sleep(duracion)
    return True
