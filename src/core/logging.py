"""
Sistema de Logging Profesional para MarkeTTalento
"""
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_error_log = []  # Almacena últimos errores en memoria para consulta rápida
MAX_ERRORS = 50

# Configuracion de rotacion
MAX_LOG_SIZE_MB = 10  # Tamaño maximo antes de rotar
MAX_BACKUP_FILES = 5  # Numero de archivos de backup a mantener


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
    
    # Handler para archivo (con rotacion)
    if log_to_file:
        if log_filename is None:
            log_filename = "markettalento.log"
        
        file_handler = RotatingFileHandler(
            LOGS_DIR / log_filename,
            maxBytes=MAX_LOG_SIZE_MB * 1024 * 1024,
            backupCount=MAX_BACKUP_FILES,
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


def log_error(modulo: str, mensaje: str, exc: Exception = None):
    """Registra un error y lo guarda en memoria para consulta rápida."""
    timestamp = datetime.now().strftime(DATE_FORMAT)
    error_entry = {
        "timestamp": timestamp,
        "modulo": modulo,
        "mensaje": mensaje,
    }
    if exc:
        error_entry["tipo"] = type(exc).__name__
        error_entry["detalle"] = str(exc)
        error_entry["traceback"] = traceback.format_exc()
        logger = get_logger(f"markettalento.{modulo}")
        logger.error(f"{mensaje}: {exc}\n{traceback.format_exc()}")
    else:
        logger = get_logger(f"markettalento.{modulo}")
        logger.error(mensaje)
    
    _error_log.insert(0, error_entry)
    if len(_error_log) > MAX_ERRORS:
        _error_log.pop()


def get_errores_recientes(limite: int = 20):
    """Retorna los últimos errores registrados."""
    return _error_log[:limite]
