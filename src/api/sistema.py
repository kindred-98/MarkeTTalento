"""
Router de Sistema - Endpoints de utilidad y monitoreo
"""
from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter
from sqlalchemy import text

from src.core.database.database import SessionLocal

router = APIRouter()


@router.get("/estado")
async def estado_sistema():
    """
    Verifica el estado del sistema.
    Retorna informacion sobre el estado de salud de la API.
    """
    return {
        "estado": "operativo",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "servicios": ["FastAPI", "SQLite", "YOLOv8"],
        "mensaje": "Sistema funcionando correctamente"
    }


@router.get("/salud")
async def salud():
    """
    Endpoint de health check para verificar disponibilidad.
    """
    return {
        "estado": "saludable",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "servicios": ["FastAPI", "SQLite", "YOLOv8"]
    }


@router.get("/health")
async def health_check_avanzado():
    """
    Health check avanzado que verifica todos los componentes criticos.
    """
    checks = {
        "api": {"status": "ok", "response_time_ms": 0},
        "database": {"status": "unknown", "response_time_ms": 0},
        "embeddings": {"status": "unknown"},
        "yolo_model": {"status": "unknown"},
    }

    # Check database
    import time
    t0 = time.time()
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["database"] = {"status": "ok", "response_time_ms": round((time.time() - t0) * 1000, 2)}
    except Exception as e:
        checks["database"] = {"status": "error", "error": str(e)}

    # Check embeddings file
    emb_path = Path(__file__).parent.parent.parent / "data" / "embeddings_productos.pkl"
    checks["embeddings"] = {"status": "ok" if emb_path.exists() else "missing"}

    # Check YOLO model
    yolo_path = Path(__file__).parent.parent.parent / "yolov8n.pt"
    checks["yolo_model"] = {"status": "ok" if yolo_path.exists() else "missing"}

    overall = "healthy" if all(c["status"] == "ok" for c in checks.values()) else "degraded"

    return {
        "status": overall,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
    }


# Métricas simples tipo Prometheus
_request_count = 0
_request_errors = 0


@router.get("/metrics")
async def metrics():
    """
    Endpoint de métricas en formato Prometheus simple.
    """
    db = SessionLocal()
    try:
        productos_count = db.execute(text("SELECT COUNT(*) FROM productos WHERE activo = 1")).scalar()
        tickets_count = db.execute(text("SELECT COUNT(*) FROM tickets")).scalar()
        usuarios_count = db.execute(text("SELECT COUNT(*) FROM usuarios")).scalar()
        stock_total = db.execute(text("SELECT COALESCE(SUM(cantidad), 0) FROM inventario")).scalar()
    except Exception:
        productos_count = tickets_count = usuarios_count = stock_total = 0
    finally:
        db.close()

    lines = [
        "# HELP markettalento_productos_total Total de productos activos",
        "# TYPE markettalento_productos_total gauge",
        f"markettalento_productos_total {productos_count}",
        "",
        "# HELP markettalento_tickets_total Total de tickets",
        "# TYPE markettalento_tickets_total gauge",
        f"markettalento_tickets_total {tickets_count}",
        "",
        "# HELP markettalento_usuarios_total Total de usuarios",
        "# TYPE markettalento_usuarios_total gauge",
        f"markettalento_usuarios_total {usuarios_count}",
        "",
        "# HELP markettalento_stock_total Unidades totales en inventario",
        "# TYPE markettalento_stock_total gauge",
        f"markettalento_stock_total {stock_total}",
    ]

    return {"metrics": "\n".join(lines)}
