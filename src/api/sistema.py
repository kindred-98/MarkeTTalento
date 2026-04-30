"""
Router de Sistema - Endpoints de utilidad y monitoreo
"""
from datetime import datetime, timezone
from fastapi import APIRouter

router = APIRouter()


@router.get("/estado")
async def estado_sistema():
    """
    Verifica el estado del sistema.
    Retorna información sobre el estado de salud de la API.
    """
    return {
        "estado": "operativo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "servicios": ["FastAPI", "SQLite", "YOLOv8"],
        "mensaje": "Sistema funcionando correctamente"
    }


@router.get("/salud")
async def salud():
    """
    Endpoint de health check para verificar disponibilidad.
    """
    return {
        "estado": "saludable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "servicios": ["FastAPI", "SQLite", "YOLOv8"]
    }
