"""Página de Logs del día"""
import streamlit as st
from src.core.logging import get_log_dia, get_errores_recientes, get_exitos_recientes, log_info
from pathlib import Path
from datetime import datetime


def render():
    st.markdown("<h2> Logs del Día</h2>", unsafe_allow_html=True)
    
    if st.button("🔄 Forzar log de prueba"):
        log_info("Log de prueba desde página de logs")
        st.rerun()
    
    log_path = Path("logs") / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    
    st.caption(f"📁 Archivo: {log_path}")
    st.caption(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d')}")
    
    if log_path.exists():
        with open(log_path, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        exitos = [l.strip() for l in lineas if 'INFO' in l and '✅' in l]
        errores = [l.strip() for l in lineas if 'ERROR' in l]
        warns = [l.strip() for l in lineas if 'WARNING' in l]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("✅ Éxitos", len(exitos))
        with col2:
            st.metric("❌ Errores", len(errores))
        with col3:
            st.metric("️ Warns", len(warns))
        
        st.markdown("---")
        st.markdown("<h4>📄 Log completo</h4>", unsafe_allow_html=True)
        
        if lineas:
            log_text = "".join(lineas[-100:])
            st.code(log_text, language="log")
        else:
            st.info("Archivo vacío")
    else:
        st.warning("️ No hay archivo de log para hoy")
        st.info("Los logs se crean cuando ocurren eventos (crear, editar, eliminar productos)")
