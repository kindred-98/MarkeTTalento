"""
Página de Predicciones
"""
import streamlit as st
import plotly.graph_objects as go
from app.utils.api import api_get


def render():
    """Renderiza la página de predicciones."""
    st.markdown("<h2>🔮 Predicciones ML</h2>", unsafe_allow_html=True)
    
    predicciones = api_get("/api/v1/prediccion/todos")
    productos = api_get("/api/v1/productos")
    
    if not predicciones:
        st.info("No hay datos suficientes para generar predicciones")
        return
    
    for pred in predicciones[:10]:
        prod = next((p for p in productos if p.get("id") == pred.get("producto_id")), None)
        if prod:
            with st.expander(f"📊 {prod.get('nombre', 'Producto')}"):
                hist = pred.get("historico", [])
                pron = pred.get("pronostico", [])
                
                if hist and pron:
                    fig = go.Figure()
                    
                    # Histórico
                    fig.add_trace(go.Scatter(
                        x=list(range(len(hist))),
                        y=hist,
                        mode='lines+markers',
                        name='Histórico',
                        line=dict(color='#00f0ff', width=2)
                    ))
                    
                    # Pronóstico
                    fig.add_trace(go.Scatter(
                        x=list(range(len(hist), len(hist) + len(pron))),
                        y=pron,
                        mode='lines+markers',
                        name='Pronóstico',
                        line=dict(color='#8b5cf6', width=2, dash='dash')
                    ))
                    
                    fig.update_layout(
                        title="Tendencia de demanda",
                        paper_bgcolor="#0a0e17",
                        plot_bgcolor="#0a0e17",
                        font=dict(color="white"),
                        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        yaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
                        height=300
                    )
                    
                    st.plotly_chart(fig, width='stretch')
                
                # Recomendación
                tendencia = pred.get("tendencia", "estable")
                color = {"alza": "#10b981", "baja": "#ef4444", "estable": "#f59e0b"}.get(tendencia, "#f59e0b")
                
                st.markdown(f"""
                <div style="padding: 10px; background: {color}20; border-left: 3px solid {color}; border-radius: 0 8px 8px 0;">
                    <strong style="color: {color};">Tendencia: {tendencia.upper()}</strong>
                </div>
                """, unsafe_allow_html=True)
