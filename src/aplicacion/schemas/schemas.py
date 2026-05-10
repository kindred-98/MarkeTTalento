from pydantic import BaseModel, Field, ConfigDict, EmailStr, model_validator
from datetime import datetime
from typing import Optional, List, Literal


class CategoriaBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: Optional[str] = Field(None, max_length=500)


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaResponse(CategoriaBase):
    id: int
    activo: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class ProveedorBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=200)
    contacto: Optional[str] = Field(None, max_length=200)
    email: EmailStr = Field(..., max_length=200)
    telefono: Optional[str] = Field(None, max_length=20, pattern=r"^[\d\s\+\-\(\)]{7,20}$")


class ProveedorCreate(ProveedorBase):
    pass


class ProveedorResponse(ProveedorBase):
    id: int
    activo: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductoBase(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    codigo_barras: Optional[str] = Field(None, max_length=50)
    nombre: str = Field(..., min_length=1, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    precio_venta: float = Field(..., gt=0, le=100000, description="Precio de venta mayor que 0")
    precio_coste: Optional[float] = Field(None, gt=0, le=100000)
    unidad: str = Field(..., min_length=1, max_length=50)
    stock_minimo: int = Field(default=5, ge=0, le=100000)
    stock_maximo: int = Field(default=30, ge=0, le=100000)
    tiempo_reposicion: int = Field(default=3, ge=1, le=365)
    categoria_id: int = Field(..., gt=0)
    proveedor_id: Optional[int] = Field(None, ge=1)
    imagen_url: Optional[str] = Field(None, max_length=500)

    @model_validator(mode='after')
    def check_stock_range(self):
        if self.stock_minimo is not None and self.stock_maximo is not None:
            if self.stock_minimo > self.stock_maximo:
                raise ValueError('stock_minimo no puede ser mayor que stock_maximo')
        return self


class ProductoCreate(ProductoBase):
    sku: str = Field(..., min_length=3, max_length=50, pattern=r"^[A-Za-z0-9\-/\s]+$", description="Formato: letras, números, guiones, barras y espacios")
    codigo_barras: Optional[str] = Field(None, max_length=50, pattern=r"^[A-Za-z0-9\-]*$", description="Código de barras alfanumérico")
    cantidad_inicial: Optional[int] = Field(default=0, ge=0, description="Cantidad inicial en inventario")
    ubicacion: Optional[str] = Field(default="Almacén A", max_length=100, description="Ubicación inicial del producto")


class ProductoUpdate(BaseModel):
    sku: Optional[str] = Field(None, max_length=50, pattern=r"^[A-Za-z0-9\-/\s]+$")
    codigo_barras: Optional[str] = Field(None, max_length=50, pattern=r"^[A-Za-z0-9\-]*$")
    nombre: Optional[str] = Field(None, max_length=200)
    descripcion: Optional[str] = Field(None, max_length=1000)
    precio_venta: Optional[float] = Field(None, gt=0, le=100000)
    precio_coste: Optional[float] = Field(None, gt=0, le=100000)
    unidad: Optional[str] = Field(None, max_length=50)
    stock_minimo: Optional[int] = Field(None, ge=0, le=100000)
    stock_maximo: Optional[int] = Field(None, ge=0, le=100000)
    tiempo_reposicion: Optional[int] = Field(None, ge=1, le=365)
    categoria_id: Optional[int] = Field(None, ge=1)
    proveedor_id: Optional[int] = Field(None, ge=1)
    imagen_url: Optional[str] = Field(None, max_length=500)
    activo: Optional[bool] = None

    @model_validator(mode='after')
    def check_at_least_one_field(self):
        # Evitar body vacío {}
        campos_set = [k for k, v in self.model_dump().items() if v is not None]
        if not campos_set:
            raise ValueError('Debe proporcionar al menos un campo para actualizar')
        # Validar rango de stock si ambos están presentes
        if self.stock_minimo is not None and self.stock_maximo is not None:
            if self.stock_minimo > self.stock_maximo:
                raise ValueError('stock_minimo no puede ser mayor que stock_maximo')
        return self


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
    producto_id: Optional[int] = Field(None, gt=0)


class InventarioResponse(InventarioBase):
    id: int
    producto_id: int
    fecha_ultima_actualizacion: datetime

    model_config = ConfigDict(from_attributes=True)


class VentaBase(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, le=10000)
    precio_unitario: float = Field(..., gt=0, le=100000)
    tipo_operacion: Literal["venta", "devolucion"] = Field(default="venta")


class VentaCreate(VentaBase):
    pass


class VentaResponse(VentaBase):
    id: int
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# TICKETS - Nuevo modelo TPV
# ============================================================================

class TicketLineaBase(BaseModel):
    producto_id: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, le=10000)
    precio_unitario: float = Field(..., gt=0, le=100000)


class TicketLineaCreate(TicketLineaBase):
    pass


class TicketLineaResponse(TicketLineaBase):
    id: int
    subtotal: float
    producto: Optional[ProductoResponse] = None

    model_config = ConfigDict(from_attributes=True)


class TicketBase(BaseModel):
    cajero: str = Field(..., min_length=1, max_length=100)
    metodo_pago: Literal["efectivo", "tarjeta", "transferencia"] = Field(...)
    entrega_efectivo: Optional[float] = Field(None, ge=0)
    cambio: Optional[float] = Field(None, ge=0)


class TicketCreate(TicketBase):
    lineas: List[TicketLineaCreate]


class TicketResponse(TicketBase):
    id: int
    numero_ticket: str
    fecha: datetime
    total: float
    estado: str
    lineas: List[TicketLineaResponse]

    model_config = ConfigDict(from_attributes=True)
