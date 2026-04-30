"""
Router de Ventas
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database.database import get_db
from src.dominio.entidades.entidades import Producto, Inventario, Venta
from src.aplicacion.schemas.schemas import VentaCreate, VentaResponse

router = APIRouter()


@router.post("", response_model=VentaResponse, status_code=status.HTTP_201_CREATED)
async def registrar_venta(venta: VentaCreate, db: Session = Depends(get_db)):
    """Registra una venta y actualiza el inventario."""
    producto = db.query(Producto).filter(Producto.id == venta.producto_id).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {venta.producto_id} no encontrado"
        )
    
    db_venta = Venta(
        producto_id=venta.producto_id,
        cantidad=venta.cantidad,
        precio_unitario=venta.precio_unitario,
        tipo_operacion=venta.tipo_operacion,
        fecha=datetime.now(timezone.utc)
    )
    db.add(db_venta)
    
    # Actualizar inventario
    inventario = db.query(Inventario).filter(Inventario.producto_id == venta.producto_id).first()
    if inventario:
        if venta.tipo_operacion == "venta":
            inventario.cantidad -= venta.cantidad
        else:
            inventario.cantidad += venta.cantidad
        inventario.fecha_ultima_actualizacion = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(db_venta)
    return db_venta


@router.get("", response_model=List[VentaResponse])
async def listar_ventas(limite: int = 100, db: Session = Depends(get_db)):
    """Lista últimas ventas."""
    return db.query(Venta).order_by(Venta.fecha.desc()).limit(limite).all()


@router.get("/producto/{producto_id}", response_model=List[VentaResponse])
async def ventas_por_producto(producto_id: int, limite: int = 30, db: Session = Depends(get_db)):
    """Obtiene historial de ventas de un producto."""
    return db.query(Venta).filter(
        Venta.producto_id == producto_id
    ).order_by(Venta.fecha.desc()).limit(limite).all()
