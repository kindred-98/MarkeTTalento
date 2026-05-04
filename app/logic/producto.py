"""
Lógica de negocio para productos
"""
from typing import Dict, List, Any, Optional
from app.config import CATEGORIA_EMOJIS, DESCRIPCIONES_DEFAULT


def get_categoria_emoji(nombre_categoria: str) -> str:
    """Obtiene el emoji para una categoría."""
    return CATEGORIA_EMOJIS.get(nombre_categoria, "📦")


def get_descripcion_default(nombre_producto: str) -> str:
    """Obtiene una descripción por defecto basada en el nombre."""
    nombre_lower = nombre_producto.lower()
    for key, desc in DESCRIPCIONES_DEFAULT.items():
        if key in nombre_lower:
            return desc
    return f"Producto de alta calidad, elaborado con los mejores ingredientes para garantizar frescura y sabor excepcional en cada consumo"


def validar_producto(data: Dict[str, Any], productos_existentes: List[Dict]) -> Dict[str, Any]:
    """Valida los datos de un producto."""
    errores = []
    
    # Campos obligatorios
    campos_obligatorios = {
        "sku": "Código SKU",
        "nombre": "Nombre del producto",
        "precio_venta": "Precio de venta",
        "unidad": "Unidad de medida",
        "stock_maximo": "Stock máximo",
        "categoria_id": "Categoría",
    }
    
    for campo, nombre in campos_obligatorios.items():
        if not data.get(campo):
            errores.append(f"{nombre} es obligatorio")
    
    # Validaciones numéricas
    if data.get("precio_venta", 0) < 0.01:
        errores.append("El precio de venta debe ser mayor a 0")
    
    if data.get("stock_maximo", 0) <= 0:
        errores.append("El stock máximo debe ser mayor a 0")
    
    # Validar nombre único
    nombre = data.get("nombre", "").lower()
    nombres_existentes = [p.get("nombre", "").lower() for p in productos_existentes]
    if nombre in nombres_existentes:
        errores.append("Ya existe un producto con ese nombre")
    
    return {
        "valido": len(errores) == 0,
        "errores": errores
    }


def filtrar_productos(
    productos: List[Dict],
    busqueda: str = "",
    categoria_id: Optional[int] = None,
    estado: Optional[str] = None,
    inventarios: Optional[List[Dict]] = None
) -> List[Dict]:
    """Filtra productos por múltiples criterios."""
    resultado = productos
    
    if busqueda:
        busq_lower = busqueda.lower()
        resultado = [p for p in resultado if 
            busq_lower in p.get("nombre", "").lower() or 
            busq_lower in p.get("sku", "").lower()]
    
    if categoria_id:
        resultado = [p for p in resultado if p.get("categoria_id") == categoria_id]
    
    if estado and inventarios:
        from app.logic.inventario import calcular_estado_stock
        resultado = []
        for p in productos:
            inv = next((i for i in inventarios if i.get("producto_id") == p.get("id")), None)
            if inv:
                stock = inv.get("cantidad", 0)
                max_s = p.get("stock_maximo", 100) or 100
                estado_calc = calcular_estado_stock(stock, max_s)
                if estado_calc == estado:
                    resultado.append(p)
    
    return resultado


def preparar_producto_data(
    sku: str,
    nombre: str,
    precio_venta: float,
    unidad: str,
    stock_maximo: int,
    categoria_id: int,
    **kwargs
) -> Dict[str, Any]:
    """Prepara los datos de un producto para enviar a la API."""
    data = {
        "sku": sku,
        "nombre": nombre,
        "precio_venta": precio_venta,
        "unidad": unidad,
        "stock_maximo": stock_maximo,
        "categoria_id": categoria_id,
        "stock_minimo": kwargs.get("stock_minimo", 0),
        "unidad_ingreso": kwargs.get("unidad_ingreso", 10),
        "tiempo_reposicion": kwargs.get("tiempo_reposicion", 3),
    }
    
    # Campos opcionales
    if kwargs.get("codigo_barras"):
        data["codigo_barras"] = kwargs["codigo_barras"]
    
    if kwargs.get("precio_coste", 0) > 0:
        data["precio_coste"] = kwargs["precio_coste"]
    
    if kwargs.get("proveedor_id"):
        data["proveedor_id"] = kwargs["proveedor_id"]
    
    if kwargs.get("descripcion"):
        data["descripcion"] = kwargs["descripcion"]
    
    if kwargs.get("imagen_url"):
        data["imagen_url"] = kwargs["imagen_url"]
    
    # Datos para inventario inicial
    cantidad = kwargs.get("cantidad_inicial", kwargs.get("unidad_ingreso"))
    data["cantidad_inicial"] = cantidad if cantidad is not None else 10
    data["ubicacion"] = kwargs.get("ubicacion", "Almacén A")
    
    return data
