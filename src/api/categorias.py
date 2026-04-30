"""
Router de Categorías
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database.database import get_db
from src.dominio.entidades.entidades import Categoria
from src.aplicacion.schemas.schemas import CategoriaCreate, CategoriaResponse

router = APIRouter()


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
async def crear_categoria(
    categoria: CategoriaCreate,
    db: Session = Depends(get_db)
):
    """Crea una nueva categoría."""
    db_categoria = Categoria(**categoria.model_dump())
    db.add(db_categoria)
    db.commit()
    db.refresh(db_categoria)
    return db_categoria


@router.get("", response_model=List[CategoriaResponse])
async def listar_categorias(db: Session = Depends(get_db)):
    """Lista todas las categorías activas."""
    return db.query(Categoria).filter(Categoria.activo == True).all()
