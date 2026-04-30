#!/usr/bin/env python3
"""
MarkeTTalento API
Punto de entrada principal de la API FastAPI
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config.config import settings
from src.core.config.environments import get_current_config
from src.core.database.database import init_db
from src.core.logging import setup_logging, get_logger
from src.core.errors import setup_error_handlers
from src.api.router import api_router

# Configurar logging al inicio
config = get_current_config()
setup_logging(
    level=config.LOG_LEVEL,
    log_to_file=config.LOG_TO_FILE,
    log_to_console=True
)

logger = get_logger("markettalento.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    # Startup
    try:
        logger.info("Iniciando aplicación MarkeTTalento...")
        init_db()
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.warning(f"Base de datos no disponible - modo desarrollo: {e}")
    
    yield
    
    # Shutdown
    logger.info("Cerrando aplicación MarkeTTalento...")


app = FastAPI(
    title="MarkeTTalento API",
    description="""
## Sistema de Inventario Inteligente

### Características
- **Gestión de Productos**: CRUD completo de productos, categorías y proveedores
- **Control de Inventario**: Seguimiento de stock en tiempo real con alertas
- **Ventas**: Registro y seguimiento de ventas
- **Predicciones ML**: Predicción de demanda basada en historial
- **Visión Artificial**: Detección de productos con YOLOv8 + actualización automática de inventario

### Autenticación
Por ahora en modo desarrollo (sin autenticación).

### Notas
- Base de datos: SQLite (desarrollo)
- Puerto: 8002
- Dashboard: http://localhost:8501
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar manejo de errores global
setup_error_handlers(app)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def raiz():
    """Página principal de la API."""
    logger.info("Acceso a endpoint raíz")
    return {
        "mensaje": "MarkeTTalento API",
        "version": "1.0.0",
        "documentacion": "/docs",
        "endpoints": "/api/v1",
        "entorno": config.LOG_LEVEL
    }


# Incluir todos los routers de la API
app.include_router(api_router, prefix="/api/v1")

logger.info("Routers de API registrados correctamente")


if __name__ == "__main__":
    import uvicorn
    logger.info(f"Iniciando servidor en {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        app, 
        host=settings.API_HOST, 
        port=settings.API_PORT,
        log_level=config.LOG_LEVEL.lower()
    )
