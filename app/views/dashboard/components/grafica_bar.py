"""Gráfico de barras"""
import plotly.graph_objects as go
from app.views.dashboard.config import COLORS


def grafica_bar(data, color=None):
    if not data:
        return
    
    if color is None:
        color = COLORS['primary']
    
    fig = go.Figure(go.Bar(
        x=[d['label'] for d in data],
        y=[d['value'] for d in data],
        marker_color=color,
        text=[d['value'] for d in data],
        textposition='outside'
    ))
    fig.update_layout(
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={"color": '#e2e8f0'},
        margin={"l": 30, "r": 30, "t": 20, "b": 70},
        xaxis={"tickangle": -45, "color": '#94a3b8'},
        yaxis={"color": '#94a3b8', "gridcolor": 'rgba(255,255,255,.1)'}
    )
    return fig