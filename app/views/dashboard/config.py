"""Dashboard configuration"""
CACHE_TTL = 60

COLORS = {
    'primary': '#3b82f6',
    'success': '#10b981',
    'warning': '#f59e0b',
    'danger': '#ef4444',
    'purple': '#8b5cf6',
    'gray': '#6b7280',
    'white': '#e2e8f0',
    'bg': 'rgba(15,23,42,.9)',
}

HEIGHTS = {
    'metric_card': 100,
    'pie_chart': 350,
    'bar_chart': 350,
    'line_chart': 300,
    'heatmap': 280,
}

STOCK_AGOTADO = 'Agotado'
STOCK_CRITICO = 'Crítico'
STOCK_BAJO = 'Bajo'
STOCK_SALUDABLE = 'Saludable'

STOCK_STATUS = {
    STOCK_AGOTADO: {'color': '#6b7280', 'threshold': 0},
    STOCK_CRITICO: {'color': '#ef4444', 'threshold': 0.2},
    STOCK_BAJO: {'color': '#f59e0b', 'threshold': 0.5},
    STOCK_SALUDABLE: {'color': '#10b981', 'threshold': 1.0},
}

# Orden de mayor a menor gravedad, para graficas y alertas.
STOCK_STATUS_ORDEN = (STOCK_SALUDABLE, STOCK_BAJO, STOCK_CRITICO, STOCK_AGOTADO)
STOCK_STATUS_ALERTA = (STOCK_CRITICO, STOCK_AGOTADO)


def get_stock_status(stock, max_s):
    if stock is None:
        stock = 0
    if max_s is None:
        max_s = 100
    if stock <= 0:
        return STOCK_AGOTADO
    ratio = stock / max_s if max_s > 0 else 0
    if ratio <= 0.2:
        return STOCK_CRITICO
    elif ratio <= 0.5:
        return STOCK_BAJO
    return STOCK_SALUDABLE