"""
Utilidades para calcular el estado del stock de forma unificada.
Usado por la API y los servicios para mantener consistencia.
"""

STOCK_MAXIMO_POR_DEFECTO = 100
UMBRAL_CRITICO = 25
UMBRAL_BAJO = 50
UMBRAL_MODERADO = 75

ESTADOS_AGOTADO = ("AGOTADO", "CRITICO")


def _porcentaje_stock(cantidad: int, stock_maximo: int) -> float:
    """Porcentaje del stock máximo, con máximo por defecto si el indicado no es utilizable."""
    maximo = stock_maximo or STOCK_MAXIMO_POR_DEFECTO
    if maximo <= 0:
        maximo = STOCK_MAXIMO_POR_DEFECTO
    return (cantidad / maximo) * 100


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

    pct = _porcentaje_stock(cantidad, stock_maximo)

    if pct <= UMBRAL_CRITICO:
        return "CRITICO"
    if pct <= UMBRAL_BAJO:
        return "BAJO"
    if pct <= UMBRAL_MODERADO:
        return "MODERADO"
    return "ADECUADO"


def calcular_necesita_reposicion(cantidad: int, stock_minimo: int, stock_maximo: int) -> bool:
    """Determina si el producto necesita reposición."""
    return calcular_estado_stock(cantidad, stock_minimo, stock_maximo) in ESTADOS_AGOTADO


def clasificar_resumen_inventario(cantidad: int, stock_minimo: int, stock_maximo: int) -> str:
    """
    Clasificación simplificada para el resumen del dashboard.
    Retorna: critico, bajo, adecuado
    """
    estado = calcular_estado_stock(cantidad, stock_minimo, stock_maximo)

    if estado in ESTADOS_AGOTADO:
        return "critico"
    if estado == "BAJO":
        return "bajo"
    return "adecuado"
