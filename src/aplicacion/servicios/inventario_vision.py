"""
Servicio de análisis de inventario desde imagen
Conecta visión artificial con base de datos
"""
from typing import List, Dict, Optional
from src.dominio.entidades.entidades import Producto, Inventario
from src.core.database.database import SessionLocal


class MapeoProducto:
    """Mapea objetos detectados a productos de la BD"""
    
    # Mapeo simple: nombre YOLO -> nombre en BD
    MAPA_YOLO_A_PRODUCTO = {
        "bottle": "Agua",
        "cup": "Cafe",
        "food": "Comida",
        "banana": "Fruta",
        "apple": "Manzana",
        "orange": "Naranja",
        "bread": "Pan",
        "egg": "Huevos",
        "milk": "Leche",
        "cheese": "Queso",
        "carrot": "Zanahoria",
        "broccoli": "Brocoli",
    }
    
    PRODUCTOS_BD = None
    
    @classmethod
    def obtener_productos_bd(cls):
        if cls.PRODUCTOS_BD is None:
            db = SessionLocal()
            productos = db.query(Producto).filter(Producto.activo == True).all()
            cls.PRODUCTOS_BD = {p.nombre.lower(): p for p in productos}
            db.close()
        return cls.PRODUCTOS_BD
    
    @classmethod
    def mapear_objeto_a_producto(cls, nombre_yolo: str) -> Optional[Producto]:
        productos = cls.obtener_productos_bd()
        
        if nombre_yolo.lower() in productos:
            return productos[nombre_yolo.lower()]
        
        if nombre_yolo.lower() in cls.MAPA_YOLO_A_PRODUCTO:
            nombre_bd = cls.MAPA_YOLO_A_PRODUCTO[nombre_yolo.lower()]
            if nombre_bd.lower() in productos:
                return productos[nombre_bd.lower()]
        
        return None
    
    @classmethod
    def mapear_todos(cls, objetos_detectados: List[Dict]) -> Dict:
        productos_mapeados = []
        productos_no_encontrados = []
        
        # Contar objetos por tipo
        conteo = {}
        for obj in objetos_detectados:
            nombre = obj.get('nombre', 'unknown')
            if nombre in conteo:
                conteo[nombre] += 1
            else:
                conteo[nombre] = 1
        
        # Mapear cada tipo
        for nombre, cantidad in conteo.items():
            producto = cls.mapear_objeto_a_producto(nombre)
            
            if producto:
                productos_mapeados.append({
                    "producto_id": producto.id,
                    "producto_nombre": producto.nombre,
                    "cantidad_detectada": cantidad,
                    "sku": producto.sku,
                    "stock_minimo": producto.stock_minimo,
                    "mapeado": True
                })
            else:
                productos_no_encontrados.append({
                    "objeto": nombre,
                    "cantidad": cantidad,
                    "mapeado": False
                })
        
        return {
            "mapeados": productos_mapeados,
            "no_encontrados": productos_no_encontrados,
            "total_detectado": len(objetos_detectados),
            "total_mapeado": len(productos_mapeados)
        }


def actualizar_inventario_desde_deteccion(mapeo_resultado: Dict) -> Dict:
    """Actualiza el inventario basado en la detección"""
    from datetime import datetime
    
    db = SessionLocal()
    resultados = []
    
    for item in mapeo_resultado.get("mapeados", []):
        producto_id = item["producto_id"]
        cantidad = item["cantidad_detectada"]
        
        inventario = db.query(Inventario).filter(
            Inventario.producto_id == producto_id
        ).first()
        
        if inventario:
            stock_anterior = inventario.cantidad
            inventario.cantidad = cantidad
            inventario.fecha_ultima_actualizacion = datetime.utcnow()
        else:
            inventario = Inventario(
                producto_id=producto_id,
                cantidad=cantidad,
                ubicacion="Detección automática"
            )
            db.add(inventario)
            stock_anterior = 0
        
        resultados.append({
            "producto": item["producto_nombre"],
            "stock_anterior": stock_anterior,
            "stock_nuevo": cantidad
        })
    
    db.commit()
    db.close()
    
    return {
        "actualizados": resultados,
        "total": len(resultados)
    }
