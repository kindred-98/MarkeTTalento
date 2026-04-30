"""
Configuración de Entornos para MarkeTTalento
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class BaseConfig(BaseSettings):
    """Configuración base."""
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8002
    DEBUG: bool = False
    
    # Base de datos
    DATABASE_URL: str = "sqlite:///data/markettalento.db"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    
    # Visión Artificial
    YOLO_MODEL: str = "yolov8n.pt"
    VISION_CONFIDENCE_THRESHOLD: float = 0.25
    
    # ML
    ML_PREDICTION_DAYS: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


class DevelopmentConfig(BaseConfig):
    """Configuración para desarrollo."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    

class TestingConfig(BaseConfig):
    """Configuración para testing."""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: str = "sqlite:///data/test_markettalento.db"
    LOG_TO_FILE: bool = False


class ProductionConfig(BaseConfig):
    """Configuración para producción."""
    DEBUG: bool = False
    LOG_LEVEL: str = "WARNING"
    LOG_TO_FILE: bool = True


# Diccionario de configuraciones
configurations = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env: Optional[str] = None) -> BaseConfig:
    """
    Obtiene la configuración según el entorno.
    
    Args:
        env: Nombre del entorno (development, testing, production)
             Si es None, usa la variable de entorno ENV o 'development'
    
    Returns:
        Instancia de la configuración
    """
    import os
    
    if env is None:
        env = os.getenv("ENV", "development").lower()
    
    config_class = configurations.get(env, DevelopmentConfig)
    return config_class()


# Configuración actual (singleton)
@lru_cache()
def get_current_config() -> BaseConfig:
    """Obtiene la configuración actual (cacheada)."""
    return get_config()
