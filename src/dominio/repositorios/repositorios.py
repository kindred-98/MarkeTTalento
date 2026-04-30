from abc import ABC, abstractmethod
from typing import List, Optional
from src.dominio.entidades.entidades import Producto, Inventario, Venta


class ProductoRepositorio(ABC):
    """Contrato para acceso a datos de productos."""

    @abstractmethod
    def obtener_todos(self) -> List[Producto]:
        """Lista todos los productos activos."""
        pass

    @abstractmethod
    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        """Busca un producto por ID."""
        pass

    @abstractmethod
    def obtenir_per_sku(self, sku: str) -> Optional[Producto]:
        """Busca un producto por SKU."""
        pass

    @abstractmethod
    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        """Lista productos por categoría."""
        pass

    @abstractmethod
    def crear(self, producto: Producto) -> Producto:
        """Crea un nuevo producto."""
        pass

    @abstractmethod
    def actualizar(self, producto: Producto) -> Producto:
        """Actualiza un producto."""
        pass

    @abstractmethod
    def eliminar(self, producto_id: int) -> bool:
        """Elimina (soft delete) un producto."""
        pass


class InventarioRepositorio(ABC):
    """Contrato para acceso a datos de inventario."""

    @abstractmethod
    def obtener_por_producto(self, producto_id: int) -> Optional[Inventario]:
        """Obtiene inventario de un producto."""
        pass

    @abstractmethod
    def obtener_todos(self) -> List[Inventario]:
        """Lista todos los inventarios."""
        pass

    @abstractmethod
    def actualizar_stock(self, producto_id: int, cantidad: int, ubicacion: Optional[str] = None) -> Inventario:
        """Actualiza el stock de un producto."""
        pass

    @abstractmethod
    def obtener_bajo_stock(self, limite: int = 10) -> List[Inventario]:
        """Lista productos con stock bajo."""
        pass


class VentaRepositorio(ABC):
    """Contrato para acceso a datos de ventas."""

    @abstractmethod
    def crear(self, venta: Venta) -> Venta:
        """Registra una venta."""
        pass

    @abstractmethod
    def obtener_por_producto(self, producto_id: int, limite: int = 30) -> List[Venta]:
        """Obtiene historial de ventas de un producto."""
        pass

    @abstractmethod
    def obtener_ventas_fecha(self, fecha_inicio, fecha_fin) -> List[Venta]:
        """Obtiene ventas en un rango de fechas."""
        pass

    @abstractmethod
    def obtener_todas(self, limite: int = 100) -> List[Venta]:
        """Lista últimas ventas."""
        pass
