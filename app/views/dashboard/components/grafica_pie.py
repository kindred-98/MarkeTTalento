"""Gráfico circular"""
import plotly.graph_objects as go


def grafica_pie(data, colors=None):
    if not data:
        return
    
    if colors is None:
        colors = ['#10b981', '#f59e0b', '#ef4444', '#6b7280']
    
    fig = go.Figure(go.Pie(
        labels=[d['label'] for d in data],
        values=[d['value'] for d in data],
        marker={"colors": colors[:len(data)]},
        hole=0.6,
        textinfo='label+percent',
        textfont={"color": 'white', "size": 12},
        hovertemplate='%{label}: %{value}<extra></extra>'
    ))
    fig.update_layout(
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={"color": '#e2e8f0'},
        margin={"l": 20, "r": 20, "t": 20, "b": 60},
        showlegend=True,
        legend={"orientation": 'h', "yanchor": 'top', "y": -0.2, "xanchor": 'center', "x": 0.5}
    )
    return fig