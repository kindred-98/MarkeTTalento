from typing import List, Optional
from src.dominio.entidades.entidades import Producto, Categoria, Proveedor
from src.dominio.repositorios.repositorios import ProductoRepositorio
from src.aplicacion.schemas.schemas import (
    ProductoCreate, 
    ProductoResponse,
)


class ProductoServicio:
    """Servicio para gestión de productos."""

    def __init__(self, producto_repo: ProductoRepositorio):
        self.producto_repo = producto_repo

    def obtener_todos(self) -> List[Producto]:
        """Lista todos los productos activos."""
        return self.producto_repo.obtener_todos()

    def obtener_por_id(self, producto_id: int) -> Optional[Producto]:
        """Obtiene un producto por ID."""
        return self.producto_repo.obtener_por_id(producto_id)

    def obtener_por_sku(self, sku: str) -> Optional[Producto]:
        """Obtiene un producto por SKU."""
        return self.producto_repo.obtenir_per_sku(sku)

    def obtener_por_categoria(self, categoria_id: int) -> List[Producto]:
        """Lista productos por categoría."""
        return self.producto_repo.obtener_por_categoria(categoria_id)

    def crear(self, producto_data: dict) -> Producto:
        """Crea un nuevo producto."""
        producto = Producto(**producto_data)
        return self.producto_repo.crear(producto)

    def actualizar(self, producto_id: int, producto_data: dict) -> Optional[Producto]:
        """Actualiza un producto existente."""
        producto = self.producto_repo.obtener_por_id(producto_id)
        if not producto:
            return None
        
        for key, value in producto_data.items():
            if hasattr(producto, key):
                setattr(producto, key, value)
        
        return self.producto_repo.actualizar(producto)

    def eliminar(self, producto_id: int) -> bool:
        """Elimina (soft delete) un producto."""
        return self.producto_repo.eliminar(producto_id)

    def buscar(self, query: str) -> List[Producto]:
        """Busca productos por nombre o SKU."""
        todos = self.obtener_todos()
        return [p for p in todos if query.lower() in p.nombre.lower() or query in p.sku]

    def obtener_productos_bajo_stock(self) -> List[dict]:
        """Obtiene productos con stock bajo el mínimo."""
        todos = self.obtener_todos()
        resultado = []
        for producto in todos:
            if hasattr(producto, 'inventario') and producto.inventario:
                if producto.inventario.cantidad < producto.stock_minimo:
                    resultado.append({
                        "producto": producto,
                        "stock_actual": producto.inventario.cantidad,
                        "stock_minimo": producto.stock_minimo,
                        "diferencia": producto.stock_minimo - producto.inventario.cantidad
                    })
        return resultado
