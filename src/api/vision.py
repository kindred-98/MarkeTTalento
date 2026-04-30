"""
Router de Visión Artificial
Endpoints para detección de productos con YOLOv8
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter, UploadFile, File, HTTPException

from src.aplicacion.servicios.vision_servicio import VisionServicio
from src.aplicacion.servicios.inventario_vision import MapeoProducto, actualizar_inventario_desde_deteccion

router = APIRouter()


@router.post("/detectar")
async def detectar_en_imagen(
    archivo: UploadFile = File(...),
    confianza_min: float = 0.15
):
    """Detecta productos en una imagen usando YOLOv8."""
    timestamp = datetime.now(timezone.utc).timestamp()
    ruta_temporal = f"temp_{timestamp}_{archivo.filename}"
    
    try:
        with open(ruta_temporal, "wb") as f:
            contenido = await archivo.read()
            f.write(contenido)
        
        vision = VisionServicio()
        resultado = vision.detectar_en_imagen(ruta_temporal, confianza_min)
        
        return resultado.to_dict()
    
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@router.post("/analizar-y-actualizar")
async def detectar_y_actualizar_inventario(
    archivo: UploadFile = File(...),
    confianza_min: float = 0.15,
    actualizar_stock: bool = True
):
    """
    Detecta productos en imagen y opcionalmente actualiza el inventario.
    """
    timestamp = datetime.now(timezone.utc).timestamp()
    ruta_temporal = f"temp_{timestamp}_{archivo.filename}"
    
    try:
        with open(ruta_temporal, "wb") as f:
            contenido = await archivo.read()
            f.write(contenido)
        
        # 1. Detectar objetos
        vision = VisionServicio()
        resultado_vision = vision.detectar_en_imagen(ruta_temporal, confianza_min)
        
        # Convertir a lista de diccionarios
        objetos_detectados = []
        for det in resultado_vision.productos_detectados:
            objetos_detectados.append({
                "nombre": det.nombre,
                "confianza": det.confianza,
                "cantidad": det.cantidad
            })
        
        # 2. Mapear objetos a productos
        mapeo = MapeoProducto.mapear_todos(objetos_detectados)
        
        resultado = {
            "deteccion": {
                "total_objetos": resultado_vision.total_productos,
                "objetos": objetos_detectados
            },
            "mapeo": mapeo
        }
        
        # 3. Actualizar inventario si se solicita
        if actualizar_stock and mapeo["mapeados"]:
            resultado["actualizacion"] = actualizar_inventario_desde_deteccion(mapeo)
        
        return resultado
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
