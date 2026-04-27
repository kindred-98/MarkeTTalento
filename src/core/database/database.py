import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.core.database.base import Base
from src.dominio.entidades.entidades import Categoria, Proveedor, Producto, Inventario, Venta

URL_DATABASE = os.getenv("DATABASE_URL", "")

if URL_DATABASE.startswith("postgresql"):
    engine = create_engine(URL_DATABASE, poolclass=StaticPool, echo=False)
else:
    if URL_DATABASE.startswith("sqlite"):
        engine = create_engine(URL_DATABASE, connect_args={"check_same_thread": False})
    else:
        if URL_DATABASE:
            print(f"[WARN] SQLite - DATABASE_URL={URL_DATABASE}")
        else:
            print("[INFO] Modo desarrollo - SQLite archivo")
        engine = create_engine("sqlite:///markettalento.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)