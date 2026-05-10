"""
Utilidades para calcular el estado del stock de forma unificada.
Usado por la API y los servicios para mantener consistencia.
"""


def calcular_estado_stock(cantidad: int, stock_minimo: int, stock_maximo: int) -> str:
    """
    Calcula el estado del stock basado en porcentaje del stock máximo.

    Criterios:
        - AGOTADO: cantidad <= 0
        - CRITICO: <= 25% del stock máximo
        - BAJO: <= 50% del stock máximo
        - MODERADO: <= 75% del stock máximo
        - ADECUADO: > 75% del stock máximo
    """
    if cantidad <= 0:
        return "AGOTADO"

    maximo = stock_maximo or 100
    if maximo <= 0:
        maximo = 100

    pct = (cantidad / maximo) * 100

    if pct <= 25:
        return "CRITICO"
    elif pct <= 50:
        return "BAJO"
    elif pct <= 75:
        return "MODERADO"
    else:
        return "ADECUADO"


def calcular_necesita_reposicion(cantidad: int, stock_minimo: int, stock_maximo: int) -> bool:
    """Determina si el producto necesita reposición."""
    if cantidad <= 0:
        return True

    maximo = stock_maximo or 100
    if maximo <= 0:
        maximo = 100

    pct = (cantidad / maximo) * 100
    return pct <= 25


def clasificar_resumen_inventario(cantidad: int, stock_minimo: int, stock_maximo: int) -> str:
    """
    Clasificación simplificada para el resumen del dashboard.
    Retorna: critico, bajo, adecuado
    """
    estado = calcular_estado_stock(cantidad, stock_minimo, stock_maximo)
    if estado in ("AGOTADO", "CRITICO"):
        return "critico"
    elif estado == "BAJO":
        return "bajo"
    else:
        return "adecuado"
