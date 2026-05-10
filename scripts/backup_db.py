"""
Backup automatico de la base de datos SQLite.
Crea copias diarias con timestamp en backups/ y mantiene los ultimos 7 dias.
"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "markettalento.db"
BACKUP_DIR = Path(__file__).parent.parent / "backups"
RETENTION_DAYS = 7


def crear_backup():
    """Crea un backup de la BD con timestamp."""
    if not DB_PATH.exists():
        print(f"[ERROR] Base de datos no encontrada: {DB_PATH}")
        return False

    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"markettalento_{timestamp}.db"

    shutil.copy2(DB_PATH, backup_file)
    print(f"[OK] Backup creado: {backup_file.name}")
    return True


def limpiar_backups_antiguos():
    """Elimina backups con mas de RETENTION_DAYS dias."""
    if not BACKUP_DIR.exists():
        return

    limite = datetime.now() - timedelta(days=RETENTION_DAYS)
    eliminados = 0

    for archivo in BACKUP_DIR.glob("markettalento_*.db"):
        # Extraer fecha del nombre: markettalento_YYYYMMDD_HHMMSS.db
        try:
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
    if crear_backup():
        limpiar_backups_antiguos()
        print("[OK] Proceso completado")
    else:
        print("[FAIL] No se pudo crear el backup")


if __name__ == "__main__":
    main()
