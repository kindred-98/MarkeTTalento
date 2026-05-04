"""
Lógica de negocio para inventario
"""
from typing import Dict, List, Any, Optional
from app.config import ESTADOS_STOCK


def calcular_estado_stock(stock: int, stock_maximo: int) -> str:
    """Calcula el estado del stock basado en el porcentaje del máximo."""
    if stock <= 0:
        return "Agotado"
    
    if stock_maximo > 0:
        pct = (stock / stock_maximo) * 100
        if pct <= 25:
            return "Crítico"
        elif pct <= 59:
            return "Bajo"
    
    return "Saludable"


def get_estado_info(estado: str) -> Dict[str, str]:
    """Obtiene la información visual de un estado."""
    return ESTADOS_STOCK.get(estado, ESTADOS_STOCK["Saludable"])


def filtrar_por_estado(datos: List[Dict], estado_filtro: str) -> List[Dict]:
    """Filtra productos por estado."""
    if estado_filtro == "Todos":
        return datos
    return [d for d in datos if d.get("estado") == estado_filtro]


def ordenar_inventario(datos: List[Dict], criterio: str) -> List[Dict]:
    """Ordena el inventario por diferentes criterios."""
    if criterio == "Producto (A-Z)":
        return sorted(datos, key=lambda x: x.get("producto", {}).get("nombre", ""))
    elif criterio == "Stock (mayor)":
        return sorted(datos, key=lambda x: x.get("stock", 0), reverse=True)
    elif criterio == "Stock (menor)":
        return sorted(datos, key=lambda x: x.get("stock", 0))
    return datos


def calcular_nuevo_stock(stock_actual: int, ingreso: int) -> int:
    """Calcula el nuevo stock después de un ingreso."""
    return stock_actual + ingreso


def preparar_datos_inventario(inventarios: List[Dict], productos: List[Dict]) -> List[Dict]:
    """Prepara los datos de inventario para visualización."""
    datos = []
    
    for inv in inventarios:
        prod = next((p for p in productos if p.get("id") == inv.get("producto_id")), None)
        if prod:
            stock = inv.get("cantidad", 0)
            max_s = prod.get("stock_maximo", 100) or 100
            estado = calcular_estado_stock(stock, max_s)
            
            precio_coste = prod.get("precio_coste", 0) or 0
            precio_venta = prod.get("precio_venta", 0)
            ganancia = precio_venta - precio_coste
            margen = (ganancia / precio_coste * 100) if precio_coste > 0 else 0
            
            datos.append({
                "producto": prod,
                "stock": stock,
                "min_s": prod.get("stock_minimo", 0),
                "max_s": max_s,
                "estado": estado,
                "ubicacion": inv.get("ubicacion", "N/A"),
                "precio_coste": precio_coste,
                "precio_venta": precio_venta,
                "ganancia": ganancia,
                "margen": margen,
            })
    
    return datos


def validar_stock(stock: int, stock_minimo: int, stock_maximo: int) -> Dict[str, Any]:
    """Valida que el stock esté dentro de los límites."""
    errores = []
    
    if stock < 0:
        errores.append("El stock no puede ser negativo")
    
    if stock_maximo > 0 and stock > stock_maximo:
        errores.append(f"El stock ({stock}) excede el máximo ({stock_maximo})")
    
    return {
        "valido": len(errores) == 0,
        "errores": errores,
        "alerta": stock <= stock_minimo if stock_minimo > 0 else False
    }
