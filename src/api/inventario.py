"""
Router de Inventario
"""
from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.core.database.database import get_db
from src.dominio.entidades.entidades import Producto, Inventario
from src.dominio.repositorios.repositorios import ProductoRepositorio, InventarioRepositorio, VentaRepositorio
from src.infraestructura.repositorios.repositorios_impl import (
    SQLAlchemyProductoRepositorio,
    SQLAlchemyInventarioRepositorio,
    SQLAlchemyVentaRepositorio,
)
from src.aplicacion.schemas.schemas import InventarioCreate, InventarioResponse
from src.aplicacion.servicios.inventario_servicio import InventarioServicio

router = APIRouter()


def get_producto_repo() -> ProductoRepositorio:
    return SQLAlchemyProductoRepositorio()


def get_inventario_repo() -> InventarioRepositorio:
    return SQLAlchemyInventarioRepositorio()


def get_venta_repo() -> VentaRepositorio:
    return SQLAlchemyVentaRepositorio()


@router.post("/{producto_id}", response_model=InventarioResponse)
async def actualizar_inventario(
    producto_id: int,
    inventario_data: InventarioCreate,
    db: Session = Depends(get_db)
):
    """Actualiza el inventario de un producto."""
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    if not producto:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {producto_id} no encontrado"
        )
    
    inventario = db.query(Inventario).filter(Inventario.producto_id == producto_id).first()
    
    if inventario:
        inventario.cantidad = inventario_data.cantidad
        inventario.ubicacion = inventario_data.ubicacion
        inventario.fecha_ultima_actualizacion = datetime.now(timezone.utc)
    else:
        inventario = Inventario(
            producto_id=producto_id,
            cantidad=inventario_data.cantidad,
            ubicacion=inventario_data.ubicacion
        )
        db.add(inventario)
    
    db.commit()
    db.refresh(inventario)
    return inventario


@router.get("", response_model=List[InventarioResponse])
async def listar_inventario(db: Session = Depends(get_db)):
    """Lista todo el inventario."""
    return db.query(Inventario).all()


@router.get("/bajo-stock", response_model=List[InventarioResponse])
async def productos_bajo_stock(limite: int = 10, db: Session = Depends(get_db)):
    """Lista productos con stock bajo."""
    inventarios = db.query(Inventario).all()
    resultados = []
    
    for inv in inventarios:
        producto = db.query(Producto).filter(Producto.id == inv.producto_id).first()
        if producto and inv.cantidad < producto.stock_minimo:
            resultados.append(inv)
    
    return resultados[:limite]


@router.get("/resumen")
async def resumen_inventario(db: Session = Depends(get_db)):
    """Obtiene resumen completo del inventario."""
    try:
        productos = db.query(Producto).filter(Producto.activo == True).all()
        inventarios = db.query(Inventario).all()
        
        total_productos = len(productos)
        total_unidades = sum(i.cantidad for i in inventarios)
        productos_criticos = 0
        productos_bajos = 0
        valor_total = 0.0
        
        for inv in inventarios:
            prod = next((p for p in productos if p.id == inv.producto_id), None)
            if prod:
                if inv.cantidad < prod.stock_minimo:
                    if inv.cantidad <= prod.stock_minimo * 0.3:
                        productos_criticos += 1
                    else:
                        productos_bajos += 1
                valor_total += inv.cantidad * prod.precio_venta
        
        return {
            "total_productos": total_productos,
            "total_unidades": total_unidades,
            "productos_criticos": productos_criticos,
            "productos_bajos": productos_bajos,
            "productos_adecuados": total_productos - productos_criticos - productos_bajos,
            "valor_total": round(valor_total, 2),
            "recomendaciones": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recomendaciones")
async def recomendaciones(
    producto_repo: ProductoRepositorio = Depends(get_producto_repo),
    inventario_repo: InventarioRepositorio = Depends(get_inventario_repo),
    venta_repo: VentaRepositorio = Depends(get_venta_repo)
):
    """Genera recomendaciones de reposición."""
    servicio = InventarioServicio(inventario_repo, venta_repo)
    return servicio.generar_recomendaciones()
