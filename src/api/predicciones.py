"""
Router de Predicciones
Endpoints de Machine Learning para predicción de demanda
"""
from typing import List
from fastapi import APIRouter, Depends

from src.dominio.repositorios.repositorios import VentaRepositorio
from src.implementaciones.repositorios_impl import SQLAlchemyVentaRepositorio
from src.aplicacion.servicios.prediccion_servicio import PrediccionServicio

router = APIRouter()


def get_venta_repo() -> VentaRepositorio:
    return SQLAlchemyVentaRepositorio()


@router.get("/{producto_id}")
async def predecir_demanda(
    producto_id: int,
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Predice la demanda para un producto específico."""
    servicio = PrediccionServicio(venta_repo)
    prediccion = servicio.predecir_demanda(producto_id)
    
    return {
        "producto": prediccion.producto_nombre,
        "dias_hasta_agotarse": round(prediccion.dias_hasta_agotarse, 1),
        "consumo_promedio_diario": round(prediccion.consumo_promedio, 2),
        "tendencia": prediccion.tendencia,
        "estado": prediccion.estado,
        "historial": prediccion.datos_grafico
    }


@router.get("/todos")
async def predecir_todos(venta_repo: VentaRepositorio = Depends(get_venta_repo)):
    """Predice demanda para todos los productos."""
    servicio = PrediccionServicio(venta_repo)
    predicciones = servicio.predecir_todos()
    
    return [
        {
            "producto": p.producto_nombre,
            "dias_hasta_agotarse": round(p.dias_hasta_agotarse, 1),
            "consumo_promedio_diario": round(p.consumo_promedio, 2),
            "tendencia": p.tendencia,
            "estado": p.estado
        }
        for p in predicciones
    ]


@router.get("/semanal/{producto_id}")
async def pronostico_semanal(
    producto_id: int,
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Genera pronóstico semanal para un producto."""
    servicio = PrediccionServicio(venta_repo)
    return servicio.generar_pronostico_semanal(producto_id)
