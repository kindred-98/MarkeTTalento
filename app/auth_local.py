"""
Autenticación local para Streamlit Cloud
Maneja usuarios directamente desde SQLite
"""
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.dominio.entidades.entidades import Usuario
from src.core.security.auth import verify_password

_ENGINE_LOCAL = None


def get_engine_local():
    global _ENGINE_LOCAL
    if _ENGINE_LOCAL is None:
        db_path = os.getenv("DATABASE_PATH", "data/markettalento.db")
        _ENGINE_LOCAL = create_engine(
            f"sqlite:///{db_path}", connect_args={"check_same_thread": False}
        )
    return _ENGINE_LOCAL


def get_session_local():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine_local())
    return SessionLocal()


def autenticar_usuario(username: str, password: str) -> Optional[dict]:
    """Valida credenciales contra SQLite. Devuelve None si el login falla."""
    session = get_session_local()
    try:
        user = session.query(Usuario).filter_by(username=username, activo=True).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        user.ultimo_login = datetime.now(timezone.utc).replace(tzinfo=None)
        session.commit()
        return {
            "id": user.id, "username": user.username,
            "nombre_completo": user.nombre_completo or user.username,
            "email": user.email, "rol": user.rol
        }
    finally:
        session.close()