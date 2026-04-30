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
    unidad = Column(String(50), nullable=False)  # litro, kg, unidad, paquete, etc.
    stock_minimo = Column(Integer, default=5)
    stock_maximo = Column(Integer, default=30)
    tiempo_reposicion = Column(Integer, default=3)  # días

    categoria_id = Column(Integer, ForeignKey("categorias.id"), nullable=False)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"), nullable=True)
    
    imagen_url = Column(String(500), nullable=True)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    categoria = relationship("Categoria", back_populates="productos")
    proveedor = relationship("Proveedor", back_populates="productos")
    ventas = relationship("Venta", back_populates="producto")
    inventario = relationship("Inventario", back_populates="producto", uselist=False)


class Inventario(Base):
    __tablename__ = "inventario"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), unique=True, nullable=False)
    cantidad = Column(Integer, default=0)
    ubicacion = Column(String(100), nullable=True)  # Estantería A1, Pasillo 3, etc.
    fecha_ultima_actualizacion = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto", back_populates="inventario")


class Venta(Base):
    __tablename__ = "ventas"

    id = Column(Integer, primary_key=True, index=True)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Float, nullable=False)
    tipo_operacion = Column(String(20), default="venta")  # venta, devolucion
    fecha = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto", back_populates="ventas")
