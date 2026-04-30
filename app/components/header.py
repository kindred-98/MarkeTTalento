"""
Componente de Header para la aplicación
"""
import streamlit as st


def render_header():
    """Renderiza el header animado de la aplicación."""
    st.markdown("""
    <style>
    .hdr-c{background:linear-gradient(135deg,rgba(0,240,255,0.15) 0%,rgba(139,92,246,0.15) 50%,rgba(236,72,153,0.15) 100%);padding:30px 40px;border-radius:20px;border:1px solid rgba(0,240,255,0.3);box-shadow:0 0 40px rgba(0,240,255,0.2),inset 0 0 30px rgba(0,240,255,0.05);margin-bottom:25px;position:relative;overflow:hidden;}.hdr-t,.hdr-b{position:absolute;left:0;right:0;height:2px;background:linear-gradient(90deg,transparent,#00f0ff,transparent);box-shadow:0 0 20px rgba(0,240,255,0.8);}.hdr-t{top:0;}.hdr-b{bottom:0;background:linear-gradient(90deg,transparent,#8b5cf6,transparent);box-shadow:0 0 20px rgba(139,92,246,0.8);}.hdr-x{text-align:center;position:relative;z-index:1;}.hdr-i{font-size:3.5rem;filter:drop-shadow(0 0 15px rgba(0,240,255,0.6));}.hdr-h{font-size:3rem;margin:15px 0 10px 0;font-weight:700;letter-spacing:3px;background:linear-gradient(90deg,#00f0ff,#8b5cf6,#ec4899);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}.hdr-p{color:#94a3b8;font-size:1.2rem;margin:0;font-weight:500;letter-spacing:2px;}.hdr-v{color:#00f0ff;text-shadow:0 0 10px rgba(0,240,255,0.5);}.hdr-bad{margin-top:20px;display:flex;justify-content:center;gap:15px;flex-wrap:wrap;}.hdr-b1,.hdr-b2,.hdr-b3{padding:6px 16px;border-radius:20px;font-size:0.85rem;font-weight:600;}.hdr-b1{background:rgba(0,240,255,0.15);border:1px solid rgba(0,240,255,0.4);color:#00f0ff;}.hdr-b2{background:rgba(139,92,246,0.15);border:1px solid rgba(139,92,246,0.4);color:#8b5cf6;}.hdr-b3{background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.4);color:#10b981;}
    </style>
    <div class="hdr-c">
        <div class="hdr-t"></div>
        <div class="hdr-b"></div>
        <div class="hdr-x">
            <span class="hdr-i">📦</span>
            <h1 class="hdr-h">MarkeTTalento</h1>
            <p class="hdr-p">Sistema de Inventario Inteligente con <span class="hdr-v">Visión Artificial</span></p>
            <div class="hdr-bad">
                <span class="hdr-b1">🤖 ML & IA</span>
                <span class="hdr-b2">📊 Analytics</span>
                <span class="hdr-b3">🔮 Predicciones</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
