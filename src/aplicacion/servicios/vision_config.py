"""
Configuración de Visión Artificial
Usa modelo YOLOv8 con clases de alimentos y retail
"""
import os
import torch
from ultralytics import YOLO

MODELO_BASE = "yolov8n.pt"

# Clases relevantes de COCO para retail/alimentos
CLASES_RELEVANTES = [
    'bottle', 'cup', 'glass', 'wine glass', 'fork', 'knife', 'spoon', 'bowl',
    'banana', 'apple', 'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 
    'pizza', 'donut', 'cake', 'chair', 'couch', 'bed', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'book', 'clock', 'vase', 'scissors',
    'teddy bear', 'hair drier', 'toothbrush', 'food', 'person', 'handbag',
    'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball', 'kite',
    'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket'
]

# Intentar cargar el modelo
try:
    torch.serialization.add_safe_globals(['ultralytics.nn.tasks.DetectionModel'])
except:
    pass

def obtener_modelo_vision():
    """Carga el modelo YOLOv8."""
    try:
        print(f"Cargando modelo: {MODELO_BASE}")
        modelo = YOLO(MODELO_BASE)
        print("Modelo cargado correctamente")
        return modelo
    except Exception as e:
        print(f"Error cargando modelo: {e}")
        raise

def obtener_modelo_vision():
    """Carga el modelo de visión para detección de productos."""
    try:
        print(f"Cargando modelo: {MODELO_RETAIL}")
        modelo = YOLO(MODELO_RETAIL)
        print("Modelo de retail cargado correctamente")
        return modelo
    except Exception as e:
        print(f"Error cargando modelo de retail: {e}")
        print("Usando modelo COCO como fallback")
        return YOLO(MODELO_COCO)


def detectar_productos_en_imagen(ruta_imagen, confianza=0.25):
    """
    Detecta productos en una imagen.
    
    Args:
        ruta_imagen: Ruta a la imagen
        confianza: Umbral de confianza (0-1)
    
    Returns:
        Lista de productos detectados con bounding boxes
    """
    modelo = obtener_modelo_vision()
    
    resultados = modelo(ruta_imagen, conf=confianza, verbose=False)
    
    productos = []
    for resultado in resultados:
        boxes = resultado.boxes
        for box in boxes:
            clase_id = int(box.cls[0])
            confianza_box = float(box.conf[0])
            nombre = resultado.names[clase_id]
            
            xyxy = box.xyxy[0].cpu().numpy()
            productos.append({
                "nombre": nombre,
                "confianza": round(confianza_box, 2),
                "bbox": {
                    "x1": int(xyxy[0]),
                    "y1": int(xyxy[1]),
                    "x2": int(xyxy[2]),
                    "y2": int(xyxy[3])
                }
            })
    
    return productos


def contar_productos(productos_detectados):
    """Cuenta productos por tipo."""
    conteo = {}
    for p in productos_detectados:
        nombre = p["nombre"]
        if nombre in conteo:
            conteo[nombre]["cantidad"] += 1
            conteo[nombre]["confianza"] = (conteo[nombre]["confianza"] + p["confianza"]) / 2
        else:
            conteo[nombre] = {
                "cantidad": 1,
                "confianza": p["confianza"]
            }
    return conteo
