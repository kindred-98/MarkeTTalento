"""
Crea el usuario administrador por defecto si no existe.
Ejecutar una vez al instalar: python scripts/crear_admin.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.database.database import SessionLocal, engine
from src.core.security.auth import get_password_hash
from src.dominio.entidades.entidades import Usuario, Base


def main():
    # Asegurar que la tabla existe
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Verificar si ya existe admin
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()
        if admin:
            print("Usuario admin ya existe. No se creo nada nuevo.")
            return

        # Crear admin por defecto
        admin = Usuario(
            username="admin",
            email="admin@markettalento.com",
            hashed_password=get_password_hash("admin123"),
            nombre_completo="Administrador",
            rol="admin",
            activo=True,
        )
        db.add(admin)

        # Crear cajeros de ejemplo (los 9 hardcodeados del TPV)
        cajeros = ["andres", "edu", "carlos", "alberto", "irrael", "YioQueSe", "fernando", "ernesto", "raul"]
        for c in cajeros:
            if not db.query(Usuario).filter(Usuario.username == c).first():
                db.add(Usuario(
                    username=c,
                    hashed_password=get_password_hash(c),
                    nombre_completo=c.capitalize(),
                    rol="cajero",
                    activo=True,
                ))

        db.commit()
        print("[OK] Usuario admin creado: username=admin, password=admin123")
        print("[OK] Cajeros de ejemplo creados: " + ", ".join(cajeros))
    finally:
        db.close()


if __name__ == "__main__":
    main()
