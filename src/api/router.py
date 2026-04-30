"""
Router principal de la API
Agrupa todos los routers de endpoints
"""
from fastapi import APIRouter

from src.api import sistema, categorias, proveedores, productos, inventario, ventas, predicciones, vision

api_router = APIRouter()

# Incluir todos los routers
api_router.include_router(sistema.router, tags=["Sistema"])
api_router.include_router(categorias.router, prefix="/categorias", tags=["Categorías"])
api_router.include_router(proveedores.router, prefix="/proveedores", tags=["Proveedores"])
api_router.include_router(productos.router, prefix="/productos", tags=["Productos"])
api_router.include_router(inventario.router, prefix="/inventario", tags=["Inventario"])
api_router.include_router(ventas.router, prefix="/ventas", tags=["Ventas"])
api_router.include_router(predicciones.router, prefix="/prediccion", tags=["Predicciones"])
api_router.include_router(vision.router, prefix="/vision", tags=["Visión Artificial"])
