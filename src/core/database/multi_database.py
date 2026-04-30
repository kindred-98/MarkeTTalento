"""
Configuración de Múltiples Bases de Datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Dict, Optional
import os

# Configuración de bases de datos disponibles
DATABASES = {
    "primary": {
        "name": "Principal (markettalento.db)",
        "url": "sqlite:///data/markettalento.db",
        "description": "Base de datos principal del sistema"
    },
    "secondary": {
        "name": "Secundaria (inventario.db)",
        "url": "sqlite:///data/inventario.db",
        "description": "Base de datos secundaria para respaldo o datos históricos"
    }
}

# Engines y SessionMakers para cada base de datos
_engines: Dict[str, any] = {}
_sessionmakers: Dict[str, any] = {}

_current_db = "primary"


def get_database_config(db_name: str) -> dict:
    """Obtiene la configuración de una base de datos."""
    return DATABASES.get(db_name, DATABASES["primary"])


def get_engine(db_name: str = None):
    """Obtiene el engine de una base de datos específica."""
    global _engines
    
    if db_name is None:
        db_name = _current_db
    
    if db_name not in _engines:
        config = get_database_config(db_name)
        _engines[db_name] = create_engine(
            config["url"],
            connect_args={"check_same_thread": False}
        )
    
    return _engines[db_name]


def get_sessionmaker(db_name: str = None):
    """Obtiene el sessionmaker de una base de datos específica."""
    global _sessionmakers
    
    if db_name is None:
        db_name = _current_db
    
    if db_name not in _sessionmakers:
        engine = get_engine(db_name)
        _sessionmakers[db_name] = sessionmaker(
            autocommit=False, 
            autoflush=False, 
            bind=engine
        )
    
    return _sessionmakers[db_name]


def get_db(db_name: str = None):
    """Obtiene una sesión de base de datos."""
    SessionLocal = get_sessionmaker(db_name)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def set_active_database(db_name: str):
    """Cambia la base de datos activa."""
    global _current_db
    if db_name not in DATABASES:
        raise ValueError(f"Base de datos '{db_name}' no existe. Opciones: {list(DATABASES.keys())}")
    _current_db = db_name
    print(f"[INFO] Base de datos activa cambiada a: {DATABASES[db_name]['name']}")


def get_active_database() -> str:
    """Obtiene el nombre de la base de datos activa."""
    return _current_db


def init_all_databases():
    """Inicializa todas las bases de datos (crea tablas)."""
    from src.core.database.base import Base
    
    for db_name in DATABASES.keys():
        engine = get_engine(db_name)
        Base.metadata.create_all(bind=engine)
        print(f"[OK] Base de datos inicializada: {DATABASES[db_name]['name']}")


def migrate_data(source_db: str, target_db: str, table_name: str = None):
    """
    Migra datos entre bases de datos.
    
    Args:
        source_db: Nombre de la base de datos origen
        target_db: Nombre de la base de datos destino
        table_name: Nombre de la tabla específica (opcional, si es None migra todo)
    """
    from sqlalchemy.orm import Session
    
    source_engine = get_engine(source_db)
    target_engine = get_engine(target_db)
    
    # Aquí iría la lógica de migración
    # Por ahora solo imprime información
    print(f"[INFO] Migrando datos de '{DATABASES[source_db]['name']}' a '{DATABASES[target_db]['name']}'")
    
    return {
        "source": source_db,
        "target": target_db,
        "status": "Funcionalidad en desarrollo"
    }


def list_databases():
    """Lista todas las bases de datos disponibles."""
    return {
        name: {
            **config,
            "active": name == _current_db
        }
        for name, config in DATABASES.items()
    }
