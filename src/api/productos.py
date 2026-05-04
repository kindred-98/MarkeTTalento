"""
Router de Productos
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database.database import get_db
from src.dominio.entidades.entidades import Producto, Inventario
from src.aplicacion.schemas.schemas import ProductoCreate, ProductoResponse, ProductoUpdate

router = APIRouter()


@router.post("", response_model=ProductoResponse, status_code=status.HTTP_201_CREATED)
async def crear_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db)
):
    """Crea un nuevo producto con inventario inicial."""
    # Extraer campos de inventario
    cantidad_inicial = getattr(producto, 'cantidad_inicial', 0) or 0
    ubicacion = getattr(producto, 'ubicacion', None) or "Almacén A"
    
    # Crear el producto
    producto_data = producto.model_dump(exclude={'cantidad_inicial', 'ubicacion'})
    db_producto = Producto(**producto_data)
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    
    # Crear el inventario
    inventario = Inventario(
        producto_id=db_producto.id,
        cantidad=cantidad_inicial,
        ubicacion=ubicacion
    )
    db.add(inventario)
    db.commit()
    
    return db_producto


@router.get("", response_model=List[ProductoResponse])
async def listar_productos(
    categoria_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lista productos activos."""
    query = db.query(Producto).filter(Producto.activo == True)
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    return query.all()


@router.get("/{producto_id}", response_model=ProductoResponse)
async def obtener_producto(producto_id: int, db: Session = Depends(get_db)):
    """Obtiene un producto por ID."""
    producto = db.query(Producto).filter(
        Producto.id == producto_id,
        Producto.activo == True
    ).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado"
        )
    return producto


@router.get("/sku/{sku}", response_model=ProductoResponse)
async def obtener_producto_por_sku(sku: str, db: Session = Depends(get_db)):
    """Obtiene un producto por SKU."""
    producto = db.query(Producto).filter(
        Producto.sku == sku,
        Producto.activo == True
    ).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto con SKU {sku} no encontrado"
        )
    return producto


@router.put("/{producto_id}", response_model=ProductoResponse)
async def actualizar_producto(
    producto_id: int,
    producto_data: ProductoUpdate,
    db: Session = Depends(get_db)
):
    """Actualiza un producto."""
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado"
        )
    
    update_data = producto_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_producto, key, value)
    
    db.commit()
    db.refresh(db_producto)
    return db_producto


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_producto(producto_id: int, db: Session = Depends(get_db)):
    """Elimina un producto y su inventario."""
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not db_producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado"
        )
    
    # Eliminar inventario asociado
    inventario = db.query(Inventario).filter(Inventario.producto_id == producto_id).first()
    if inventario:
        db.delete(inventario)
    
    # Eliminar producto
    db.delete(db_producto)
    db.commit()
    return None
