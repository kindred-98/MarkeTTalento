"""
Autenticación local para Streamlit Cloud
Maneja usuarios directamente desde SQLite
"""
import streamlit as st
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.dominio.entidades.entidades import Usuario
from src.core.security.auth import verify_password

_ENGINE_LOCAL = None

def get_engine_local():
    global _ENGINE_LOCAL
    if _ENGINE_LOCAL is None:
        _ENGINE_LOCAL = create_engine("sqlite:///data/markettalento.db", connect_args={"check_same_thread": False})
    return _ENGINE_LOCAL

def get_session_local():
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine_local())
    return SessionLocal()

def autenticar_usuario(username: str, password: str) -> dict:
    session = get_session_local()
    try:
        user = session.query(Usuario).filter_by(username=username, activo=True).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        user.ultimo_login = datetime.utcnow()
        session.commit()
        return {
            "id": user.id, "username": user.username,
            "nombre_completo": user.nombre_completo or user.username,
            "email": user.email, "rol": user.rol
        }
    finally:
        session.close()