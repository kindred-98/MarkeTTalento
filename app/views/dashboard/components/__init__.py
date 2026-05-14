"""Dashboard components"""
from app.views.dashboard.components.metricas import metric_card, metric_row
from app.views.dashboard.components.grafica_bar import grafica_bar
from app.views.dashboard.components.grafica_linea import grafica_linea
from app.views.dashboard.components.grafica_pie import grafica_pie

__all__ = ['metric_card', 'metric_row', 'grafica_bar', 'grafica_linea', 'grafica_pie']