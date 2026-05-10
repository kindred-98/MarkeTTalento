"""
Servicio de Visión AI para Control de Stock Visual.
Combina YOLOv8 (detección de regiones) + ResNet50 (embeddings)
+ similitud coseno para identificar productos reales del catálogo.
"""
import os
import pickle
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

import numpy as np
import torch
import torchvision.transforms as T
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image
from ultralytics import YOLO


EMB_PATH = Path(__file__).parent.parent.parent.parent / "data" / "embeddings_productos.pkl"
YOLO_PATH = Path(__file__).parent.parent.parent.parent / "yolov8n.pt"


@dataclass
class RegionDetectada:
    """Región de imagen donde YOLO detectó un objeto."""
    x1: int
    y1: int
    x2: int
    y2: int
    confianza: float


@dataclass
class ProductoDetectado:
    """Producto identificado tras comparación de embeddings."""
    producto_id: int
    nombre: str
    confianza: float
    region: RegionDetectada


class VisionStockServicio:
    """Servicio para conteo visual de stock usando similitud de embeddings."""

    def __init__(self):
        self._modelo_yolo = None
        self._modelo_resnet = None
        self._transform = None
        self._embeddings_ref = {}
        self._device = torch.device("cpu")

    # ------------------------------------------------------------------
    # Carga lazy de modelos
    # ------------------------------------------------------------------

    def _cargar_yolo(self):
        if self._modelo_yolo is None:
            self._modelo_yolo = YOLO(str(YOLO_PATH))
        return self._modelo_yolo

    def _cargar_resnet(self):
        if self._modelo_resnet is None:
            weights = ResNet50_Weights.IMAGENET1K_V2
            model = resnet50(weights=weights)
            model.fc = torch.nn.Identity()
            model.eval()
            self._modelo_resnet = model
            self._transform = T.Compose([
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
        return self._modelo_resnet

    def _cargar_embeddings(self):
        if not self._embeddings_ref and EMB_PATH.exists():
            with open(EMB_PATH, "rb") as f:
                self._embeddings_ref = pickle.load(f)
        return self._embeddings_ref

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    @staticmethod
    def _normalizar(v: np.ndarray) -> np.ndarray:
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    def _extraer_embedding_region(self, imagen: Image.Image, region: RegionDetectada) -> np.ndarray:
        """Extrae embedding de una región recortada de la imagen."""
        model = self._cargar_resnet()
        recorte = imagen.crop((region.x1, region.y1, region.x2, region.y2)).convert("RGB")
        tensor = self._transform(recorte).unsqueeze(0)
        with torch.no_grad():
            emb = model(tensor).squeeze().numpy()
        return self._normalizar(emb)

    def _clasificar_por_similitud(self, embedding_detectado: np.ndarray) -> Optional[Tuple[int, float]]:
        """Compara embedding detectado con referencias y devuelve (producto_id, similitud)."""
        refs = self._cargar_embeddings()
        if not refs:
            return None

        mejor_pid = None
        mejor_sim = -1.0

        for pid, datos in refs.items():
            emb_ref = datos.get("embedding")
            if emb_ref is None:
                continue
            sim = float(np.dot(embedding_detectado, emb_ref))
            if sim > mejor_sim:
                mejor_sim = sim
                mejor_pid = pid

        return (mejor_pid, mejor_sim) if mejor_pid is not None else None

    # ------------------------------------------------------------------
    # Detección de objetos en imagen del estante
    # ------------------------------------------------------------------

    def detectar_regiones(self, imagen_path: str, confianza_min: float = 0.15) -> List[RegionDetectada]:
        """Usa YOLOv8 para detectar regiones candidatas en la imagen."""
        modelo = self._cargar_yolo()
        resultados = modelo(imagen_path, conf=confianza_min, verbose=False)

        regiones = []
        for r in resultados:
            for box in r.boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                regiones.append(RegionDetectada(
                    x1=int(xyxy[0]),
                    y1=int(xyxy[1]),
                    x2=int(xyxy[2]),
                    y2=int(xyxy[3]),
                    confianza=float(box.conf[0]),
                ))
        return regiones

    def contar_productos_en_imagen(self, imagen_path: str,
                                   confianza_min_yolo: float = 0.15,
                                   umbral_similitud: float = 0.65) -> Dict:
        """
        Flujo completo:
        1. Detecta regiones con YOLO.
        2. Para cada región, extrae embedding y compara con referencias.
        3. Clasifica si similitud >= umbral.
        4. Cuenta productos detectados.
        """
        imagen = Image.open(imagen_path).convert("RGB")
        regiones = self.detectar_regiones(imagen_path, confianza_min_yolo)

        productos_detectados: List[ProductoDetectado] = []
        no_clasificados = 0

        for region in regiones:
            emb = self._extraer_embedding_region(imagen, region)
            resultado = self._clasificar_por_similitud(emb)

            if resultado is None or resultado[1] < umbral_similitud:
                no_clasificados += 1
                continue

            pid, sim = resultado
            productos_detectados.append(ProductoDetectado(
                producto_id=pid,
                nombre="",  # Se rellena después con BD
                confianza=round(sim, 3),
                region=region,
            ))

        # Conteo agregado
        conteo = {}
        for pd in productos_detectados:
            conteo[pd.producto_id] = conteo.get(pd.producto_id, 0) + 1

        return {
            "total_regiones": len(regiones),
            "productos_detectados": productos_detectados,
            "conteo": conteo,
            "no_clasificados": no_clasificados,
            "imagen_ancho": imagen.width,
            "imagen_alto": imagen.height,
        }

    # ------------------------------------------------------------------
    # Comparativa con inventario
    # ------------------------------------------------------------------

    def comparar_con_inventario(self, conteo_ia: Dict[int, int]) -> List[Dict]:
        """
        Compara conteo de la IA con stock teórico de la BD.
        Devuelve lista de discrepancias.
        """
        from sqlalchemy.orm import joinedload
        from src.core.database.database import SessionLocal
        from src.dominio.entidades.entidades import Producto, Inventario, Categoria

        db = SessionLocal()
        try:
            productos = db.query(Producto).options(
                joinedload(Producto.categoria),
                joinedload(Producto.inventario)
            ).filter(Producto.activo == True).all()

            resultado = []
            for prod in productos:
                stock_bd = prod.inventario.cantidad if prod.inventario else 0
                detectado = conteo_ia.get(prod.id, 0)
                diferencia = detectado - stock_bd

                if diferencia != 0:
                    estado = "SOBRANTE" if diferencia > 0 else "FALTANTE"
                else:
                    estado = "OK"

                resultado.append({
                    "producto_id": prod.id,
                    "nombre": prod.nombre,
                    "categoria": prod.categoria.nombre if prod.categoria else "",
                    "stock_bd": stock_bd,
                    "detectado_ia": detectado,
                    "diferencia": diferencia,
                    "estado": estado,
                })

            # Ordenar: discrepancias primero
            resultado.sort(key=lambda x: (0 if x["estado"] != "OK" else 1, abs(x["diferencia"]), x["nombre"]), reverse=False)
            return resultado
        finally:
            db.close()

    # ------------------------------------------------------------------
    # Regenerar embeddings (usado por admin)
    # ------------------------------------------------------------------

    @staticmethod
    def regenerar_embeddings() -> Dict:
        """Ejecuta el script de entrenamiento y retorna resumen."""
        import subprocess
        script = Path(__file__).parent.parent.parent.parent / "scripts" / "entrenar_modelo_visual.py"
        result = subprocess.run(["python", str(script)], capture_output=True, text=True)
        return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}
