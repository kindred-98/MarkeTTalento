from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


class CategoriaBase(BaseModel):
    nombre: str = Field(..., max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int
    activo: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class ProveedorBase(BaseModel):
    nombre: str = Field(..., max_length=200)
    contacto: Optional[str] = Field(None, max_length=200)
    email: str = Field(..., max_length=200)
    telefono: Optional[str] = Field(None, max_length=20)


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorResponse(ProveedorBase):
    id: int
    activo: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductoBase(BaseModel):
    sku: str = Field(..., max_length=50)
    codigo_barras: Optional[str] = Field(None, max_length=50)
    nombre: str = Field(..., max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    precio_venta: float = Field(..., gt=0)
    precio_coste: Optional[float] = Field(None, gt=0)
    unidad: str = Field(..., max_length=50)
    stock_minimo: int = Field(default=5, ge=0)
    stock_maximo: int = Field(default=30, ge=0)
    tiempo_reposicion: int = Field(default=3, ge=1)
    categoria_id: int
    proveedor_id: Optional[int] = None
    imagen_url: Optional[str] = Field(None, max_length=500)


class ProductoCreate(ProductoBase):
    cantidad_inicial: Optional[int] = Field(default=0, ge=0, description="Cantidad inicial en inventario")
    ubicacion: Optional[str] = Field(default="Almacén A", max_length=100, description="Ubicación inicial del producto")


class ProductoResponse(ProductoBase):
    id: int
    activo: bool
    fecha_creacion: datetime
    categoria: CategoriaResponse
    proveedor: Optional[ProveedorResponse]

    model_config = ConfigDict(from_attributes=True)


class InventarioBase(BaseModel):
    cantidad: int = Field(default=0, ge=0)
    ubicacion: Optional[str] = Field(None, max_length=100)


class InventarioCreate(InventarioBase):
    producto_id: Optional[int] = None


class InventarioResponse(InventarioBase):
    id: int
    producto_id: int
    fecha_ultima_actualizacion: datetime

    model_config = ConfigDict(from_attributes=True)


class VentaBase(BaseModel):
    producto_id: int
    cantidad: int = Field(..., gt=0)
    precio_unitario: float = Field(..., gt=0)
    tipo_operacion: str = Field(default="venta")


class VentaCreate(VentaBase):
    pass


class VentaResponse(VentaBase):
    id: int
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)