"""
Entrena/genera embeddings de referencia para todos los productos.
Usa ResNet50 pre-entrenado para extraer huellas digitales visuales.
Guarda en data/embeddings_productos.pkl
"""
import os
import sys
import json
import pickle
import sqlite3
from pathlib import Path

import numpy as np
import torch
import torchvision.transforms as T
from torchvision.models import resnet50, ResNet50_Weights
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = Path(__file__).parent.parent / "data" / "markettalento.db"
EMB_PATH = Path(__file__).parent.parent / "data" / "embeddings_productos.pkl"

# Transformaciones para ResNet50
transform = T.Compose([
    T.Resize((224, 224)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def cargar_modelo_embedding():
    """Carga ResNet50 sin la última capa (feature extractor)."""
    weights = ResNet50_Weights.IMAGENET1K_V2
    model = resnet50(weights=weights)
    model.fc = torch.nn.Identity()  # Eliminar capa de clasificación
    model.eval()
    return model


def extraer_embedding(model, image_path):
    """Extrae embedding de 2048 dimensiones de una imagen."""
    try:
        img = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            embedding = model(tensor).squeeze().numpy()
        return embedding
    except Exception as e:
        print(f"  Error procesando {image_path}: {e}")
        return None


def normalizar(v):
    """Normaliza un vector a longitud 1."""
    norm = np.linalg.norm(v)
    return v / norm if norm > 0 else v


def main():
    print("=== Generando embeddings de referencia ===")
    model = cargar_modelo_embedding()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT id, producto_id, ruta_imagen FROM producto_imagenes_referencia ORDER BY producto_id"
    )
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("No hay imágenes de referencia en la BD.")
        return

    # estructura: {producto_id: {"nombre": str, "embeddings": [array1, array2, ...]}}
    data = {}

    for img_id, producto_id, ruta in rows:
        print(f"Procesando producto_id={producto_id}: {ruta}")
        emb = extraer_embedding(model, ruta)
        if emb is not None:
            if producto_id not in data:
                data[producto_id] = {"embeddings": []}
            data[producto_id]["embeddings"].append(normalizar(emb))

    # Promediar embeddings por producto (múltiples fotos -> un solo embedding promedio)
    for pid in data:
        embs = data[pid]["embeddings"]
        if embs:
            avg = normalizar(np.mean(embs, axis=0))
            data[pid]["embedding"] = avg
            data[pid]["num_fotos"] = len(embs)
            del data[pid]["embeddings"]

    # Guardar
    with open(EMB_PATH, "wb") as f:
        pickle.dump(data, f)

    print(f"\n[OK] Embeddings guardados en {EMB_PATH}")
    print(f"   Productos con embedding: {len(data)}")
    for pid, info in data.items():
        print(f"   - producto_id={pid}: {info['num_fotos']} foto(s)")


if __name__ == "__main__":
    main()
