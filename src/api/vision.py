"""
Router de Visión AI - Control de Stock Visual Profesional
Escenario A: Detección por Similitud Visual (ResNet50 + YOLOv8)
"""
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, Form

from src.aplicacion.servicios.vision_stock_servicio import VisionStockServicio
from src.core.database.database import SessionLocal
from src.dominio.entidades.entidades import ProductoImagenReferencia, Producto

router = APIRouter()
servicio = VisionStockServicio()

IMG_REF_DIR = Path(__file__).parent.parent.parent / "docs" / "img_productos"


@router.get("/referencias")
async def listar_referencias():
    """Lista todos los productos con sus imágenes de referencia."""
    db = SessionLocal()
    try:
        productos = db.query(Producto).filter(Producto.activo == True).all()
        resultado = []
        for p in productos:
            refs = db.query(ProductoImagenReferencia).filter(
                ProductoImagenReferencia.producto_id == p.id
            ).all()
            resultado.append({
                "producto_id": p.id,
                "nombre": p.nombre,
                "sku": p.sku,
                "categoria": p.categoria.nombre if p.categoria else "",
                "stock_actual": p.inventario.cantidad if p.inventario else 0,
                "num_imagenes": len(refs),
                "imagenes": [
                    {"id": r.id, "ruta": r.ruta_imagen} for r in refs
                ],
            })
        return resultado
    finally:
        db.close()


@router.post("/referencias")
async def agregar_referencia(
    producto_id: int = Form(...),
    archivo: UploadFile = File(...)
):
    """Sube una nueva imagen de referencia para un producto."""
    db = SessionLocal()
    try:
        producto = db.query(Producto).filter(Producto.id == producto_id).first()
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        # Guardar archivo
        timestamp = int(datetime.now(timezone.utc).timestamp())
        ext = Path(archivo.filename).suffix
        nombre_archivo = f"REF_{producto_id}_{timestamp}{ext}"
        ruta_destino = IMG_REF_DIR / nombre_archivo

        with open(ruta_destino, "wb") as f:
            shutil.copyfileobj(archivo.file, f)

        # Registrar en BD
        ref = ProductoImagenReferencia(
            producto_id=producto_id,
            ruta_imagen=str(ruta_destino),
        )
        db.add(ref)
        db.commit()
        db.refresh(ref)

        return {
            "mensaje": "Imagen de referencia agregada",
            "imagen_id": ref.id,
            "ruta": str(ruta_destino),
        }
    finally:
        db.close()


@router.delete("/referencias/{imagen_id}")
async def eliminar_referencia(imagen_id: int):
    """Elimina una imagen de referencia por ID."""
    db = SessionLocal()
    try:
        ref = db.query(ProductoImagenReferencia).filter(
            ProductoImagenReferencia.id == imagen_id
        ).first()
        if not ref:
            raise HTTPException(status_code=404, detail="Imagen de referencia no encontrada")

        # Eliminar archivo físico si existe
        ruta = Path(ref.ruta_imagen)
        if ruta.exists():
            ruta.unlink()

        db.delete(ref)
        db.commit()

        return {"mensaje": "Imagen de referencia eliminada", "imagen_id": imagen_id}
    finally:
        db.close()


@router.post("/entrenar")
async def entrenar_modelo_visual():
    """Regenera los embeddings de referencia. Llámalo tras agregar/quitar fotos."""
    resultado = servicio.regenerar_embeddings()
    if resultado["returncode"] != 0:
        raise HTTPException(status_code=500, detail="Error entrenando modelo: " + resultado["stderr"])
    return {
        "mensaje": "Modelo visual re-entrenado correctamente",
        "detalle": resultado["stdout"],
    }


@router.post("/conteo")
async def conteo_visual(
    archivo: UploadFile = File(...),
    confianza_min_yolo: float = 0.15,
    umbral_similitud: float = 0.65,
):
    """
    Recibe una foto del estante/almacén.
    Detecta objetos, clasifica por similitud visual y compara con inventario.
    """
    timestamp = int(datetime.now(timezone.utc).timestamp())
    ruta_temp = Path(f"temp_conteo_{timestamp}_{archivo.filename}")

    try:
        with open(ruta_temp, "wb") as f:
            shutil.copyfileobj(archivo.file, f)

        # 1. Conteo visual
        resultado_vision = servicio.contar_productos_en_imagen(
            str(ruta_temp),
            confianza_min_yolo=confianza_min_yolo,
            umbral_similitud=umbral_similitud,
        )

        # 2. Enriquecer con nombres de producto
        db = SessionLocal()
        try:
            conteo = resultado_vision["conteo"]
            productos_enriquecidos = {}
            for pid, cantidad in conteo.items():
                prod = db.query(Producto).filter(Producto.id == pid).first()
                nombre = prod.nombre if prod else f"Producto {pid}"
                productos_enriquecidos[pid] = {
                    "producto_id": pid,
                    "nombre": nombre,
                    "cantidad_detectada": cantidad,
                }
        finally:
            db.close()

        resultado_vision["productos_enriquecidos"] = productos_enriquecidos

        # 3. Comparar con inventario
        discrepancias = servicio.comparar_con_inventario(conteo)

        return {
            "conteo_ia": resultado_vision,
            "discrepancias": discrepancias,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if ruta_temp.exists():
            ruta_temp.unlink()
