"""
Módulo de validaciones para la aplicación.
Centraliza todas las validaciones de datos.
"""
from typing import List, Dict, Any, Optional


def validar_sku(sku: str, productos_existentes: List[Dict], producto_actual_id: Optional[int] = None) -> List[str]:
    """
    Valida un SKU según las reglas de negocio.
    
    Args:
        sku: El SKU a validar
        productos_existentes: Lista de productos para verificar duplicados
        producto_actual_id: ID del producto que se está editando (para excluirlo de duplicados)
    
    Returns:
        Lista de mensajes de error (vacía si es válido)
    """
    errores = []
    
    if not sku:
        errores.append("SKU obligatorio")
    elif len(sku) < 4:
        errores.append("Mínimo 4 caracteres")
    elif len(sku) > 20:
        errores.append("Máximo 20 caracteres")
    else:
        # Verificar duplicados (excluyendo el producto actual si se está editando)
        sku_lower = sku.lower()
        for p in productos_existentes:
            if p.get("id") != producto_actual_id:
                if p.get("sku", "").lower() == sku_lower:
                    errores.append("SKU duplicado")
                    break
    
    return errores


def validar_email_proveedor(email: str, proveedores_existentes: List[Dict]) -> tuple[bool, Optional[str]]:
    """
    Valida que un email de proveedor no esté duplicado.
    
    Args:
        email: El email a validar
        proveedores_existentes: Lista de proveedores existentes
    
    Returns:
        Tupla (es_valido, mensaje_error)
    """
    if not email:
        return False, "Email obligatorio"
    
    email_lower = email.lower()
    for p in proveedores_existentes:
        if p.get("email", "").lower() == email_lower:
            return False, "Email ya existe"
    
    return True, None


def validar_proveedor_nuevo(nombre: str, email: str, telefono: str) -> List[str]:
    """
    Valida datos de un nuevo proveedor.
    
    Args:
        nombre: Nombre del proveedor
        email: Email del proveedor
        telefono: Teléfono del proveedor (opcional)
    
    Returns:
        Lista de mensajes de error
    """
    errores = []
    
    if not nombre:
        errores.append("Nombre obligatorio")
    elif len(nombre) < 2:
        errores.append("Nombre muy corto")
    
    if not email:
        errores.append("Email obligatorio")
    elif "@" not in email or "." not in email:
        errores.append("Email inválido")
    
    return errores


def calcular_margen_ganancia(precio_venta: float, precio_coste: float) -> float:
    """
    Calcula el margen de ganancia sobre el coste.
    
    Args:
        precio_venta: Precio de venta
        precio_coste: Precio de coste
    
    Returns:
        Porcentaje de margen (0-100)
    """
    if precio_coste and precio_coste > 0:
        return round(((precio_venta - precio_coste) / precio_coste) * 100, 2)
    return 0.0


def validar_stock(stock: int, stock_minimo: int, stock_maximo: int) -> Dict[str, Any]:
    """
    Valida que el stock esté dentro de los límites.
    
    Args:
        stock: Stock actual
        stock_minimo: Stock mínimo permitido
        stock_maximo: Stock máximo permitido
    
    Returns:
        Dict con 'valido', 'errores' y 'alerta'
    """
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
