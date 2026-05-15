"""
Sistema de Logging Profesional para MarkeTTalento
Guarda logs diarios: logs/2026-05-15.log
"""
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_error_log = []
_success_log = []
MAX_ENTRIES = 100


def _get_daily_log_path():
    """Retorna la ruta del log del día actual."""
    today = datetime.now().strftime("%Y-%m-%d")
    return LOGS_DIR / f"{today}.log"


def setup_logging(level=logging.INFO, log_to_file=True, log_to_console=True):
    """Configura el sistema de logging con archivo diario."""
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers = []
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if log_to_file:
        log_path = _get_daily_log_path()
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=7,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def log_info(msg: str):
    """Registra información."""
    logger = get_logger("markettalento")
    logger.info(msg)


def log_success(msg: str):
    """Registra un éxito."""
    logger = get_logger("markettalento")
    logger.info(f"✅ {msg}")
    timestamp = datetime.now().strftime(DATE_FORMAT)
    _success_log.insert(0, {"timestamp": timestamp, "mensaje": msg})
    if len(_success_log) > MAX_ENTRIES:
        _success_log.pop()


def log_warning(msg: str):
    """Registra una advertencia."""
    logger = get_logger("markettalento")
    logger.warning(f"⚠️ {msg}")


def log_error(modulo: str, mensaje: str, exc: Exception = None):
    """Registra un error."""
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
    if len(_error_log) > MAX_ENTRIES:
        _error_log.pop()


def get_errores_recientes(limite: int = 20):
    return _error_log[:limite]


def get_exitos_recientes(limite: int = 20):
    return _success_log[:limite]


def get_log_dia():
    """Lee el contenido del log del día."""
    log_path = _get_daily_log_path()
    if log_path.exists():
        with open(log_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "No hay logs para hoy aún."
