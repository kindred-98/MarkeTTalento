import os
import sys
import torch
from typing import List, Optional
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime

MODELO_RETAIL = "foduucom/product-detection-in-shelf-yolov8"

torch.serialization.add_safe_globals(['ultralytics.nn.tasks.DetectionModel'])


class DeteccionProducto:
    """Resultado de detección de un producto."""
    
    def __init__(self, nombre: str, cantidad: int, confianza: float, bbox: dict):
        self.nombre = nombre
        self.cantidad = cantidad
        self.confianza = confianza
        self.bbox = bbox
    
    def to_dict(self) -> dict:
        return {
            "nombre": self.nombre,
            "cantidad": self.cantidad,
            "confianza": round(self.confianza, 2),
            "bbox": self.bbox
        }


class ResultadoVision:
    """Resultado completo del análisis de visión."""
    
    def __init__(self, imagen_path: str, productos_detectados: List[DeteccionProducto]):
        self.imagen_path = imagen_path
        self.productos_detectados = productos_detectados
        self.timestamp = datetime.utcnow()
    
    @property
    def total_productos(self) -> int:
        return len(self.productos_detectados)
    
    @property
    def total_unidades(self) -> int:
        return sum(p.cantidad for p in self.productos_detectados)
    
    def to_dict(self) -> dict:
        return {
            "imagen": self.imagen_path,
            "total_productos": self.total_productos,
            "total_unidades": self.total_unidades,
            "productos": [p.to_dict() for p in self.productos_detectados],
            "timestamp": self.timestamp.isoformat()
        }


class VisionServicio:
    """Servicio para detección de productos usando YOLOv8."""

    def __init__(self, modelo_path: str = "yolov8n.pt"):
        self.modelo_path = modelo_path
        self.modelo = None

    def _cargar_modelo(self):
        """Carga el modelo YOLOv8 pre-entrenado para retail."""
        if self.modelo is not None:
            return
        
        try:
            print(f"Cargando modelo de retail: {MODELO_RETAIL}")
            self.modelo = YOLO(MODELO_RETAIL)
        except Exception as e:
            print(f"Error cargando modelo: {e}", file=sys.stderr)
            self.modelo = YOLO("yolov8n.pt")

    def detectar_en_imagen(self, imagen_path: str, confianza_min: float = 0.25) -> ResultadoVision:
        """Detecta productos en una imagen."""
        self._cargar_modelo()
        
        if not self.modelo:
            raise Exception("Modelo no cargado")
        
        resultados = self.modelo(imagen_path, conf=confianza_min, verbose=False)
        
        productos_encontrados = []
        
        for resultado in resultados:
            boxes = resultado.boxes
            for box in boxes:
                clase_id = int(box.cls[0])
                confianza = float(box.conf[0])
                nombre = resultado.names[clase_id]
                
                xyxy = box.xyxy[0].cpu().numpy()
                bbox = {
                    "x1": int(xyxy[0]),
                    "y1": int(xyxy[1]),
                    "x2": int(xyxy[2]),
                    "y2": int(xyxy[3])
                }
                
                productos_encontrados.append(DeteccionProducto(
                    nombre=nombre,
                    cantidad=1,
                    confianza=confianza,
                    bbox=bbox
                ))
        
        return ResultadoVision(imagen_path, productos_encontrados)

    def detectar_en_imagen_con_mapeo(self, imagen_path: str, 
                                   mapeo_productos: dict,
                                   confianza_min: float = 0.25) -> ResultadoVision:
        """Detecta productos y los mapea a nuestro inventario."""
        resultado = self.detectar_en_imagen(imagen_path, confianza_min)
        
        conteo = {}
        for producto in resultado.productos_detectados:
            nombre_inventario = mapeo_productos.get(producto.nombre, producto.nombre)
            if nombre_inventario in conteo:
                conteo[nombre_inventario]["cantidad"] += 1
                confianza_anterior = conteo[nombre_inventario]["confianza"]
                conteo[nombre_inventario]["confianza"] = (confianza_anterior + producto.confianza) / 2
            else:
                conteo[nombre_inventario] = {
                    "cantidad": 1,
                    "confianza": producto.confianza,
                    "bbox": producto.bbox
                }
        
        productos_mapeados = []
        for nombre, datos in conteo.items():
            productos_mapeados.append(DeteccionProducto(
                nombre=nombre,
                cantidad=datos["cantidad"],
                confianza=datos["confianza"],
                bbox=datos["bbox"]
            ))
        
        return ResultadoVision(imagen_path, productos_mapeados)

    def contar_en_imagen(self, imagen_path: str, clase_objetivo: str) -> int:
        """Cuenta productos de una clase específica."""
        resultado = self.detectar_en_imagen(imagen_path)
        return sum(1 for p in resultado.productos_detectados if p.nombre == clase_objetivo)

    def detectar_desde_camara(self, camara_index: int = 0) -> None:
        """Detecta productos en tiempo real desde cámara web."""
        self._cargar_modelo()
        
        if not self.modelo:
            raise Exception("Modelo no cargado")
        
        cap = cv2.VideoCapture(camara_index)
        
        if not cap.isOpened():
            raise Exception("No se pudo abrir la camara")
        
        print("Presiona 'q' para salir")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            resultados = self.modelo(frame, verbose=False)
            
            for resultado in resultados:
                frame = resultado.plot()
            
            cv2.imshow("YOLOv8 - Deteccion en tiempo real", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()