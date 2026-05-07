from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.core.database.base import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(500), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    productos = relationship("Producto", back_populates="categoria")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False)
    contacto = Column(String(200), nullable=True)
    email = Column(String(200), unique=True, nullable=False)
    telefono = Column(String(20), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    productos = relationship("Producto", back_populates="proveedor")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, nullable=False, index=True)
    codigo_barras = Column(String(50), unique=True, nullable=True)
    nombre = Column(String(200), nullable=False)
    descripcion = Column(String(1000), nullable=True)
    precio_venta = Column(Float, nullable=False)
    precio_coste = Column(Float, nullable=True)
    unidad = Column(String(50), nullable=False)
    stock_minimo = Column(Integer, default=5)
    stock_maximo = Column(Integer, default=30)
    tiempo_reposicion = Column(Integer, default=3)

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)

    imagen_url = Column(String(500), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    categoria = relationship("Categoria", back_populates="productos")
    proveedor = relationship("Proveedor", back_populates="productos")
    ventas = relationship("Venta", back_populates="producto")
    inventario = relationship("Inventario", back_populates="producto", uselist=False)
    ticket_lineas = relationship("TicketLinea", back_populates="producto")


class Inventario(Base):
    __tablename__ = "inventario"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), unique=True, nullable=False)
    cantidad = Column(Integer, default=0)
    ubicacion = Column(String(100), nullable=True)
    fecha_ultima_actualizacion = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto", back_populates="inventario")


class Venta(Base):
    """Legacy: mantenida por compatibilidad histórica. Ya no se usa en el TPV."""
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    tipo_operacion = Column(String(20), default="venta")
    fecha = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto", back_populates="ventas")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    numero_ticket = Column(String(20), unique=True, nullable=False, index=True)
    cajero = Column(String(100), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, nullable=False)
    metodo_pago = Column(String(50), nullable=False)  # efectivo, tarjeta, transferencia
    entrega_efectivo = Column(Float, nullable=True)
    cambio = Column(Float, nullable=True)
    estado = Column(String(20), default="completado")  # completado, anulado

    lineas = relationship("TicketLinea", back_populates="ticket", cascade="all, delete-orphan")


class TicketLinea(Base):
    __tablename__ = "ticket_lineas"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)

    ticket = relationship("Ticket", back_populates="lineas")
    producto = relationship("Producto", back_populates="ticket_lineas")
