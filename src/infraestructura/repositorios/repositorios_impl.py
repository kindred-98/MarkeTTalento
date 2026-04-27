from typing import List, Optional
from src.dominio.entidades.entidades import Producto, Inventario, Venta
from src.dominio.repositorios.repositorios import (
    ProductoRepositorio as IProductoRepositorio,
    InventarioRepositorio as IInventarioRepositorio,
    VentaRepositorio as IVentaRepositorio,
)
from src.core.database.database import SessionLocal
from datetime import datetime


class SQLAlchemyProductoRepositorio(IProductoRepositorio):
    """Implementación SQLAlchemy para productos."""

    def __init__(self):
        self.db = SessionLocal()

    def obtener_todos(self) -> List[Producto]:
        return self.db.query(Producto).filter(Producto.activo == True).all()

    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        return self.db.query(Producto).filter(
            Producto.id == producto_id, 
            Producto.activo == True
        ).first()

    def obtenir_per_sku(self, sku: str) -> Optional[Producto]:
        return self.db.query(Producto).filter(
            Producto.sku == sku, 
            Producto.activo == True
        ).first()

    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        return self.db.query(Producto).filter(
            Producto.categoria_id == categoria_id, 
            Producto.activo == True
        ).all()

    def crear(self, producto: Producto) -> Producto:
        self.db.add(producto)
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def actualizar(self, producto: Producto) -> Producto:
        self.db.commit()
        self.db.refresh(producto)
        return producto

    def eliminar(self, producto_id: int) -> bool:
        producto = self.obtener_por_id(producto_id)
        if producto:
            producto.activo = False
            self.db.commit()
            return True
        return False


class SQLAlchemyInventarioRepositorio(IInventarioRepositorio):
    """Implementación SQLAlchemy para inventario."""

    def __init__(self):
        self.db = SessionLocal()

    def obtener_por_producto(self, producto_id: int) -> Optional[Inventario]:
        return self.db.query(Inventario).filter(
            Inventario.producto_id == producto_id
        ).first()

    def obtener_todos(self) -> List[Inventario]:
        return self.db.query(Inventario).all()

    def actualizar_stock(self, producto_id: int, cantidad: int, ubicacion: Optional[str] = None) -> Inventario:
        inventario = self.obtener_por_producto(producto_id)
        if inventario:
            inventario.cantidad = cantidad
            if ubicacion:
                inventario.ubicacion = ubicacion
            inventario.fecha_ultima_actualizacion = datetime.utcnow()
        else:
            inventario = Inventario(
                producto_id=producto_id,
                cantidad=cantidad,
                ubicacion=ubicacion,
                fecha_ultima_actualizacion=datetime.utcnow()
            )
            self.db.add(inventario)
        self.db.commit()
        self.db.refresh(inventario)
        return inventario

    def obtener_bajo_stock(self, limite: int = 10) -> List[Inventario]:
        from src.dominio.entidades.entidades import Producto
        resultados = []
        inventarios = self.db.query(Inventario).all()
        for inv in inventarios:
            producto = self.db.query(Producto).filter(Producto.id == inv.producto_id).first()
            if producto and inv.cantidad < producto.stock_minimo:
                resultados.append(inv)
        return resultados


class SQLAlchemyVentaRepositorio(IVentaRepositorio):
    """Implementación SQLAlchemy para ventas."""

    def __init__(self):
        self.db = SessionLocal()

    def crear(self, venta: Venta) -> Venta:
        self.db.add(venta)
        self.db.commit()
        self.db.refresh(venta)
        
        # Actualizar inventario
        inventario_repo = SQLAlchemyInventarioRepositorio()
        inventario = inventario_repo.obtener_por_producto(venta.producto_id)
        if inventario:
            if venta.tipo_operacion == "venta":
                inventario.cantidad -= venta.cantidad
            else:  # devolucion
                inventario.cantidad += venta.cantidad
            inventario.fecha_ultima_actualizacion = datetime.utcnow()
            self.db.commit()
        
        return venta

    def obtener_por_producto(self, producto_id: int, limite: int = 30) -> List[Venta]:
        return self.db.query(Venta).filter(
            Venta.producto_id == producto_id
        ).order_by(Venta.fecha.desc()).limit(limite).all()

    def obtener_ventas_fecha(self, fecha_inicio, fecha_fin) -> List[Venta]:
        return self.db.query(Venta).filter(
            Venta.fecha >= fecha_inicio,
            Venta.fecha <= fecha_fin
        ).all()

    def obtener_todas(self, limite: int = 100) -> List[Venta]:
        return self.db.query(Venta).order_by(
            Venta.fecha.desc()
        ).limit(limite).all()