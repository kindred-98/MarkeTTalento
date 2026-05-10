"""
Backup de Base de Datos.
Compatible con SQLite (copia de archivo) y PostgreSQL (pg_dump).
"""
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

DB_URL = os.getenv("DATABASE_URL", "")
BACKUP_DIR = Path(__file__).parent.parent / "backups"
RETENTION_DAYS = 7


def _get_db_path():
    """Extrae la ruta del archivo SQLite de DATABASE_URL."""
    if DB_URL.startswith("sqlite:///"):
        relative = DB_URL.replace("sqlite:///", "")
        # Puede ser relativo al proyecto
        return Path(__file__).parent.parent / relative
    return None


def crear_backup():
    """Crea un backup de la BD."""
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if DB_URL.startswith("postgresql"):
        # Backup con pg_dump
        backup_file = BACKUP_DIR / f"markettalento_{timestamp}.sql"
        # Extraer componentes de DATABASE_URL (formato: postgresql://user:pass@host:port/dbname)
        try:
            # Usar la variable de entorno directamente con pg_dump
            # pg_dump requiere formato libpq, no la URL completa de SQLAlchemy
            # postgresql://user:pass@host:port/dbname -> host=... user=... dbname=...
            env = os.environ.copy()
            result = subprocess.run(
                ["pg_dump", "-Fc", DB_URL, "-f", str(backup_file)],
                capture_output=True,
                text=True,
                env=env,
            )
            if result.returncode == 0:
                print(f"[OK] Backup PostgreSQL creado: {backup_file.name}")
                return True
            else:
                print(f"[ERROR] pg_dump fallo: {result.stderr}")
                return False
        except FileNotFoundError:
            print("[ERROR] pg_dump no encontrado. Instala postgresql-client.")
            return False
    else:
        # Backup SQLite (copia de archivo)
        db_path = _get_db_path()
        if not db_path or not db_path.exists():
            print(f"[ERROR] Base de datos no encontrada: {db_path}")
            return False

        backup_file = BACKUP_DIR / f"markettalento_{timestamp}.db"
        shutil.copy2(db_path, backup_file)
        print(f"[OK] Backup SQLite creado: {backup_file.name}")
        return True


def limpiar_backups_antiguos():
    """Elimina backups con mas de RETENTION_DAYS dias."""
    if not BACKUP_DIR.exists():
        return

    limite = datetime.now() - timedelta(days=RETENTION_DAYS)
    eliminados = 0

    for archivo in BACKUP_DIR.glob("markettalento_*"):
        try:
            # Extraer fecha del nombre: markettalento_YYYYMMDD_HHMMSS.ext
            fecha_str = archivo.stem.split("_")[1] + archivo.stem.split("_")[2]
            fecha_archivo = datetime.strptime(fecha_str, "%Y%m%d%H%M%S")
            if fecha_archivo < limite:
                archivo.unlink()
                eliminados += 1
        except (IndexError, ValueError):
            continue

    if eliminados > 0:
        print(f"[OK] {eliminados} backup(s) antiguo(s) eliminado(s)")


def main():
    print("=== Backup de Base de Datos ===")
    print(f"DATABASE_URL detectada: {'PostgreSQL' if DB_URL.startswith('postgresql') else 'SQLite'}")
    if crear_backup():
        limpiar_backups_antiguos()
        print("[OK] Proceso completado")
    else:
        print("[FAIL] No se pudo crear el backup")


if __name__ == "__main__":
    main()
