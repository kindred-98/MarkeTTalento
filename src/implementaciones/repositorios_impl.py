from typing import List, Optional
from sqlalchemy.orm import joinedload
from src.dominio.entidades.entidades import Producto, Inventario, Venta, Ticket, TicketLinea
from src.dominio.repositorios.repositorios import (
    ProductoRepositorio as IProductoRepositorio,
    InventarioRepositorio as IInventarioRepositorio,
    VentaRepositorio as IVentaRepositorio,
    TicketRepositorio as ITicketRepositorio,
)
from src.core.database.database import SessionLocal
from datetime import datetime, timedelta


class SQLAlchemyProductoRepositorio(IProductoRepositorio):
    """Implementación SQLAlchemy para productos.
    Cada método gestiona su propia sesión para evitar problemas de cierre prematuro."""

    def obtener_todos(self) -> List[Producto]:
        db = SessionLocal()
        try:
            return db.query(Producto).filter(Producto.activo == True).all()
        finally:
            db.close()

    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        db = SessionLocal()
        try:
            return db.query(Producto).filter(
                Producto.id == producto_id,
                Producto.activo == True
            ).first()
        finally:
            db.close()

    def obtenir_per_sku(self, sku: str) -> Optional[Producto]:
        db = SessionLocal()
        try:
            return db.query(Producto).filter(
                Producto.sku == sku,
                Producto.activo == True
            ).first()
        finally:
            db.close()

    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        db = SessionLocal()
        try:
            return db.query(Producto).filter(
                Producto.categoria_id == categoria_id,
                Producto.activo == True
            ).all()
        finally:
            db.close()

    def crear(self, producto: Producto) -> Producto:
        db = SessionLocal()
        try:
            db.add(producto)
            db.commit()
            db.refresh(producto)
            return producto
        except:
            db.rollback()
            raise
        finally:
            db.close()

    def actualizar(self, producto: Producto) -> Producto:
        db = SessionLocal()
        try:
            # Merge para asegurar que el objeto está asociado a esta sesión
            producto = db.merge(producto)
            db.commit()
            db.refresh(producto)
            return producto
        except:
            db.rollback()
            raise
        finally:
            db.close()

    def eliminar(self, producto_id: int) -> bool:
        db = SessionLocal()
        try:
            producto = db.query(Producto).filter(
                Producto.id == producto_id,
                Producto.activo == True
            ).first()
            if producto:
                producto.activo = False
                db.commit()
                return True
            return False
        except:
            db.rollback()
            raise
        finally:
            db.close()


class SQLAlchemyInventarioRepositorio(IInventarioRepositorio):
    """Implementación SQLAlchemy para inventario."""

    def obtener_por_producto(self, producto_id: int) -> Optional[Inventario]:
        db = SessionLocal()
        try:
            return db.query(Inventario).filter(
                Inventario.producto_id == producto_id
            ).first()
        finally:
            db.close()

    def obtener_todos(self) -> List[Inventario]:
        db = SessionLocal()
        try:
            return db.query(Inventario).all()
        finally:
            db.close()

    def actualizar_stock(self, producto_id: int, cantidad: int, ubicacion: Optional[str] = None) -> Inventario:
        db = SessionLocal()
        try:
            inventario = db.query(Inventario).filter(
                Inventario.producto_id == producto_id
            ).first()
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
                db.add(inventario)
            db.commit()
            db.refresh(inventario)
            return inventario
        except:
            db.rollback()
            raise
        finally:
            db.close()

    def obtener_bajo_stock(self, limite: int = 10) -> List[Inventario]:
        db = SessionLocal()
        try:
            resultados = []
            inventarios = db.query(Inventario).all()
            for inv in inventarios:
                producto = db.query(Producto).filter(Producto.id == inv.producto_id).first()
                if producto and inv.cantidad < producto.stock_minimo:
                    resultados.append(inv)
            return resultados[:limite]
        finally:
            db.close()


class SQLAlchemyVentaRepositorio(IVentaRepositorio):
    """Implementación SQLAlchemy para ventas."""

    def crear(self, venta: Venta) -> Venta:
        db = SessionLocal()
        try:
            db.add(venta)

            inventario = db.query(Inventario).filter(
                Inventario.producto_id == venta.producto_id
            ).first()
            if inventario:
                if venta.tipo_operacion == "venta":
                    inventario.cantidad -= venta.cantidad
                else:
                    inventario.cantidad += venta.cantidad
                inventario.fecha_ultima_actualizacion = datetime.utcnow()

            db.commit()
            db.refresh(venta)
            return venta
        except:
            db.rollback()
            raise
        finally:
            db.close()

    def obtener_por_producto(self, producto_id: int, limite: int = 30) -> List[Venta]:
        db = SessionLocal()
        try:
            return db.query(Venta).filter(
                Venta.producto_id == producto_id
            ).order_by(Venta.fecha.desc()).limit(limite).all()
        finally:
            db.close()

    def obtener_ventas_fecha(self, fecha_inicio, fecha_fin) -> List[Venta]:
        db = SessionLocal()
        try:
            return db.query(Venta).filter(
                Venta.fecha >= fecha_inicio,
                Venta.fecha <= fecha_fin
            ).all()
        finally:
            db.close()

    def obtener_todas(self, limite: int = 100) -> List[Venta]:
        db = SessionLocal()
        try:
            return db.query(Venta).order_by(
                Venta.fecha.desc()
            ).limit(limite).all()
        finally:
            db.close()


class SQLAlchemyTicketRepositorio(ITicketRepositorio):
    """Implementación SQLAlchemy para tickets."""

    def obtener_por_producto(self, producto_id: int, dias: int = 90) -> List[TicketLinea]:
        db = SessionLocal()
        try:
            fecha_limite = datetime.utcnow() - timedelta(days=dias)
            return db.query(TicketLinea).options(
                joinedload(TicketLinea.ticket),
                joinedload(TicketLinea.producto)
            ).join(Ticket).filter(
                TicketLinea.producto_id == producto_id,
                Ticket.estado == "completado",
                Ticket.fecha >= fecha_limite
            ).order_by(Ticket.fecha.desc()).all()
        finally:
            db.close()

    def obtener_por_fecha(self, fecha_inicio, fecha_fin) -> List[Ticket]:
        db = SessionLocal()
        try:
            return db.query(Ticket).options(
                joinedload(Ticket.lineas).joinedload(TicketLinea.producto).joinedload(Producto.categoria)
            ).filter(
                Ticket.estado == "completado",
                Ticket.fecha >= fecha_inicio,
                Ticket.fecha <= fecha_fin
            ).order_by(Ticket.fecha.desc()).all()
        finally:
            db.close()

    def obtener_todos_completados(self, limite: int = 500) -> List[Ticket]:
        db = SessionLocal()
        try:
            return db.query(Ticket).options(
                joinedload(Ticket.lineas).joinedload(TicketLinea.producto).joinedload(Producto.categoria)
            ).filter(
                Ticket.estado == "completado"
            ).order_by(Ticket.fecha.desc()).limit(limite).all()
        finally:
            db.close()

    def obtener_lineas_por_categoria(self, categoria_id: int, dias: int = 90) -> List[TicketLinea]:
        db = SessionLocal()
        try:
            fecha_limite = datetime.utcnow() - timedelta(days=dias)
            return db.query(TicketLinea).options(
                joinedload(TicketLinea.ticket),
                joinedload(TicketLinea.producto)
            ).join(Ticket).join(Producto).filter(
                Producto.categoria_id == categoria_id,
                Ticket.estado == "completado",
                Ticket.fecha >= fecha_limite
            ).order_by(Ticket.fecha.desc()).all()
        finally:
            db.close()
