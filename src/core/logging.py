"""
Sistema de Logging Profesional para MarkeTTalento
"""
import logging
import sys
from datetime import datetime
from pathlib import Path

# Crear directorio de logs si no existe
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Formato de los logs
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level=logging.INFO,
    log_to_file=True,
    log_to_console=True,
    log_filename=None
):
    """
    Configura el sistema de logging.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Si debe guardar logs en archivo
        log_to_console: Si debe mostrar logs en consola
        log_filename: Nombre del archivo de log (opcional)
    """
    # Configurar logger raíz
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    logger.handlers = []
    
    # Formato
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # Handler para consola
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # Handler para archivo
    if log_to_file:
        if log_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d")
            log_filename = f"markettalento_{timestamp}.log"
        
        file_handler = logging.FileHandler(
            LOGS_DIR / log_filename,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Obtiene un logger configurado."""
    return logging.getLogger(name)


# Loggers específicos para cada módulo
api_logger = get_logger("markettalento.api")
db_logger = get_logger("markettalento.database")
ml_logger = get_logger("markettalento.ml")
vision_logger = get_logger("markettalento.vision")
