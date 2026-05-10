"""
Router de Autenticacion
Endpoints para login, registro y gestion de usuarios
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.core.database.database import get_db
from src.core.security.auth import (
    verify_password, get_password_hash, create_access_token, get_current_user, get_current_active_admin
)
from src.dominio.entidades.entidades import Usuario
import time

router = APIRouter()

# Rate limiting específico para login (memoria, se pierde al reiniciar)
_login_attempts: dict = {}
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW = 300  # 5 minutos


def _check_login_rate_limit(ip: str):
    now = time.time()
    attempts = _login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < LOGIN_WINDOW]
    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Demasiados intentos de login. Espera {LOGIN_WINDOW // 60} minutos."
        )
    _login_attempts[ip] = attempts + [now]


def _validate_password(password: str):
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La contraseña debe tener al menos 6 caracteres"
        )


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Autentica un usuario y devuelve un token JWT."""
    # Rate limiting por IP (usar username como proxy si no hay IP real)
    client_id = form_data.username
    _check_login_rate_limit(client_id)

    user = db.query(Usuario).filter(Usuario.username == form_data.username, Usuario.activo == True).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos")

    user.ultimo_login = datetime.now(timezone.utc)
    db.commit()

    access_token = create_access_token(data={"sub": str(user.id), "rol": user.rol, "username": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "usuario": {
            "id": user.id,
            "username": user.username,
            "nombre_completo": user.nombre_completo,
            "rol": user.rol,
        }
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    username: str,
    password: str,
    nombre_completo: str = None,
    email: str = None,
    rol: str = "cajero",
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_active_admin)
):
    """Registra un nuevo usuario. Requiere rol admin."""
    if db.query(Usuario).filter(Usuario.username == username).first():
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    _validate_password(password)

    user = Usuario(
        username=username,
        hashed_password=get_password_hash(password),
        nombre_completo=nombre_completo,
        email=email,
        rol=rol,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"mensaje": "Usuario creado", "id": user.id, "username": user.username}


@router.get("/me")
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    """Devuelve la informacion del usuario autenticado."""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "nombre_completo": current_user.nombre_completo,
        "email": current_user.email,
        "rol": current_user.rol,
        "ultimo_login": str(current_user.ultimo_login) if current_user.ultimo_login else None,
    }


@router.get("/usuarios")
async def listar_usuarios(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_active_admin)):
    """Lista todos los usuarios. Requiere admin."""
    usuarios = db.query(Usuario).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "nombre_completo": u.nombre_completo,
            "email": u.email,
            "rol": u.rol,
            "activo": u.activo,
        }
        for u in usuarios
    ]
