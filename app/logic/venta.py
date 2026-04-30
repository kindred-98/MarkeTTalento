"""
Lógica de negocio para ventas
"""
from typing import Dict, List, Any
from datetime import datetime


def calcular_total_venta(cantidad: int, precio_unitario: float) -> float:
    """Calcula el total de una venta."""
    return cantidad * precio_unitario


def validar_venta(producto_id: int, cantidad: int, stock_actual: int) -> Dict[str, Any]:
    """Valida si una venta es posible."""
    errores = []
    
    if cantidad <= 0:
        errores.append("La cantidad debe ser mayor a 0")
    
    if cantidad > stock_actual:
        errores.append(f"Stock insuficiente. Disponible: {stock_actual}")
    
    return {
        "valido": len(errores) == 0,
        "errores": errores
    }


def preparar_venta_data(producto_id: int, cantidad: int, precio_unitario: float) -> Dict[str, Any]:
    """Prepara los datos de una venta para enviar a la API."""
    return {
        "producto_id": producto_id,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
    }


def formatear_fecha_venta(fecha_str: str) -> str:
    """Formatea la fecha de una venta."""
    try:
        dt = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y - %H:%M").replace("Apr", "Abr").replace("May", "May")
    except Exception:
        return "Fecha desconocida"


def preparar_datos_ventas(ventas: List[Dict], productos: List[Dict]) -> List[Dict]:
    """Prepara los datos de ventas para visualización."""
    from app.utils.helpers import get_prod_name
    
    datos = []
    for venta in ventas:
        cantidad = venta.get("cantidad", 0)
        precio = venta.get("precio_unitario", 0)
        total = calcular_total_venta(cantidad, precio)
        
        datos.append({
            "id": venta.get("id"),
            "producto_id": venta.get("producto_id"),
            "producto_nombre": get_prod_name(venta.get("producto_id"), productos),
            "cantidad": cantidad,
            "precio_unitario": precio,
            "total": total,
            "fecha": venta.get("fecha"),
            "fecha_formateada": formatear_fecha_venta(venta.get("fecha", "")),
        })
    
    return datos


def calcular_totales_ventas(ventas: List[Dict]) -> Dict[str, Any]:
    """Calcula totales de ventas."""
    total_cantidad = sum(v.get("cantidad", 0) for v in ventas)
    total_ingresos = sum(v.get("total", 0) for v in ventas)
    
    return {
        "total_ventas": len(ventas),
        "total_unidades": total_cantidad,
        "total_ingresos": total_ingresos,
    }
