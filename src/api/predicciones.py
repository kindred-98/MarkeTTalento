"""
Router de Predicciones ML
Endpoints de Machine Learning para predicción de demanda e inteligencia de negocio
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status

from src.aplicacion.schemas.schemas import respuesta_error
from src.aplicacion.servicios.prediccion_ml import PrediccionServicioML

router = APIRouter()

SIN_DATOS_PRODUCTO = respuesta_error(
    status.HTTP_404_NOT_FOUND, "No hay datos suficientes para predecir este producto"
)
SIN_DATOS_CATEGORIA = respuesta_error(
    status.HTTP_404_NOT_FOUND, "No hay datos suficientes para predecir esta categoría"
)


def _get_servicio() -> PrediccionServicioML:
    return PrediccionServicioML()


@router.get("/producto/{producto_id}", responses=SIN_DATOS_PRODUCTO)
async def predecir_demanda_producto(producto_id: int, dias_historia: int = 90, dias_futuro: int = 30):
    """Predice la demanda futura para un producto específico."""
    servicio = _get_servicio()
    resultado = servicio.predecir_demanda_producto(producto_id, dias_historia, dias_futuro)
    if not resultado:
        raise HTTPException(status_code=404, detail="No hay datos suficientes para este producto")
    return resultado.to_dict()


@router.get("/categoria/{categoria_id}", responses=SIN_DATOS_CATEGORIA)
async def predecir_demanda_categoria(categoria_id: int, dias_historia: int = 90, dias_futuro: int = 30):
    """Predice la demanda agregada para una categoría."""
    servicio = _get_servicio()
    resultado = servicio.predecir_demanda_categoria(categoria_id, dias_historia, dias_futuro)
    if not resultado:
        raise HTTPException(status_code=404, detail="No hay datos suficientes para esta categoría")
    return resultado.to_dict()


@router.get("/alertas")
async def alertas_reposicion(dias_seguridad: int = 14):
    """Genera alertas de reposición para todos los productos."""
    servicio = _get_servicio()
    alertas = servicio.generar_alertas_reposicion(dias_seguridad)
    return [a.to_dict() for a in alertas]


@router.get("/abc")
async def analisis_abc(dias: int = 90):
    """Clasifica productos por método ABC (Pareto 80/20)."""
    servicio = _get_servicio()
    productos = servicio.analisis_abc(dias)
    return [p.to_dict() for p in productos]


@router.get("/precios")
async def sugerencias_precio(dias: int = 60):
    """Genera sugerencias de ajuste de precio basado en demanda y rotación."""
    servicio = _get_servicio()
    sugerencias = servicio.sugerencias_precio(dias)
    return [s.to_dict() for s in sugerencias]


@router.get("/estacionalidad")
async def analisis_estacionalidad():
    """Analiza patrones estacionales comparando mes actual vs anterior."""
    servicio = _get_servicio()
    return servicio.analisis_estacionalidad()


@router.get("/dashboard")
async def dashboard_predictivo():
    """Resumen global con todas las métricas predictivas."""
    servicio = _get_servicio()
    return servicio.dashboard_global()
