"""
Router de Proveedores
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database.database import get_db
from src.dominio.entidades.entidades import Proveedor
from src.aplicacion.schemas.schemas import ProveedorCreate, ProveedorResponse

router = APIRouter()


@router.post("", response_model=ProveedorResponse, status_code=status.HTTP_201_CREATED)
async def crear_proveedor(
    proveedor: ProveedorCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo proveedor."""
    db_proveedor = Proveedor(**proveedor.model_dump())
    db.add(db_proveedor)
    db.commit()
    db.refresh(db_proveedor)
    return db_proveedor


@router.get("", response_model=List[ProveedorResponse])
async def listar_proveedores(db: Session = Depends(get_db)):
    """Lista todos los proveedores activos."""
    return db.query(Proveedor).filter(Proveedor.activo == True).all()
