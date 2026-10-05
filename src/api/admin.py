"""
Router de Administración de Bases de Datos
Endpoints para gestionar múltiples bases de datos
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, List
from src.aplicacion.schemas.schemas import respuesta_error
from src.core.database.multi_database import (
    list_databases,
    set_active_database,
    get_active_database,
    migrate_data,
    init_all_databases
)
from src.core.security.auth import get_current_active_admin
from src.dominio.entidades.entidades import Usuario

router = APIRouter()


@router.get("/bases-de-datos", response_model=Dict)
async def obtener_bases_de_datos(current_user: Usuario = Depends(get_current_active_admin)):
    """Lista todas las bases de datos disponibles."""
    return {
        "bases_de_datos": list_databases(),
        "activa": get_active_database()
    }


@router.post(
    "/bases-de-datos/cambiar/{db_name}",
    responses=respuesta_error(status.HTTP_400_BAD_REQUEST, "La base de datos solicitada no existe"),
)
async def cambiar_base_de_datos(db_name: str, current_user: Usuario = Depends(get_current_active_admin)):
    """Cambia la base de datos activa."""
    try:
        set_active_database(db_name)
        return {
            "mensaje": f"Base de datos cambiada a: {db_name}",
            "activa": get_active_database()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/bases-de-datos/inicializar-todas",
    responses=respuesta_error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error al inicializar las bases de datos"),
)
async def inicializar_todas(current_user: Usuario = Depends(get_current_active_admin)):
    """Inicializa todas las bases de datos (crea tablas)."""
    try:
        init_all_databases()
        return {
            "mensaje": "Todas las bases de datos han sido inicializadas",
            "bases": list(list_databases().keys())
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno al inicializar bases de datos")


@router.post(
    "/bases-de-datos/migrar",
    responses=respuesta_error(status.HTTP_500_INTERNAL_SERVER_ERROR, "Error durante la migración"),
)
async def migrar_entre_bases(
    source_db: str,
    target_db: str,
    tabla: str = None,
    current_user: Usuario = Depends(get_current_active_admin)
):
    """
    Migra datos entre bases de datos.
    
    Args:
        source_db: Base de datos origen
        target_db: Base de datos destino
        tabla: Tabla específica a migrar (opcional)
    """
    try:
        resultado = migrate_data(source_db, target_db, tabla)
        return {
            "mensaje": "Migración iniciada",
            "resultado": resultado
        }
    except Exception:
        raise HTTPException(status_code=500, detail="Error interno durante la migración")
