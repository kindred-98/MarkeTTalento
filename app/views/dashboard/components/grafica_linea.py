"""Gráfico de líneas"""
import plotly.graph_objects as go


def grafica_linea(data, color='#3b82f6'):
    if not data:
        return
    
    fig = go.Figure(go.Scatter(
        x=[d['label'] for d in data],
        y=[d['value'] for d in data],
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker={"size": 8},
        fill='tozeroy',
        fillcolor=f'{color}30'
    ))
    fig.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={"color": '#e2e8f0'},
        margin={"l": 30, "r": 30, "t": 20, "b": 50},
        xaxis={"color": '#94a3b8'},
        yaxis={"color": '#94a3b8', "gridcolor": 'rgba(255,255,255,.1)'}
    )
    return fig