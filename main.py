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
from src.core.database.multi_database import init_all_databases
from src.core.logging import setup_logging, get_logger
from src.core.errors import setup_error_handlers
from src.core.middleware.rate_limit import RateLimitMiddleware
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
        init_all_databases()
        logger.info("Todas las bases de datos inicializadas correctamente")
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
- **Ventas**: TPV profesional con tickets y cobro
- **Predicciones ML**: Predicción de demanda con scikit-learn
- **Visión Artificial**: Control de stock visual con YOLOv8 + ResNet50
- **Inspector de Producto**: Escaneo de código de barras con inteligencia de negocio

### Autenticación
- Usar `/api/v1/auth/login` con OAuth2PasswordRequestForm
- Devuelve JWT Bearer token
- Incluir token en header: `Authorization: Bearer <token>`

### Notas
- Base de datos: SQLite
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

# Middleware CORS (configurable via entorno)
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
if cors_origins == ["*"]:
    # En produccion, especificar origenes explicitamente
    cors_origins = ["http://localhost:8501", "http://127.0.0.1:8501"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Rate limiting
app.add_middleware(RateLimitMiddleware)


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
