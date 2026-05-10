"""
Tests de integracion para la API de MarkeTTalento.
Usa FastAPI TestClient para probar endpoints reales.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="module")
def admin_token():
    """Obtiene un token JWT de admin para tests autenticados."""
    response = client.post("/api/v1/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers con token Bearer."""
    return {"Authorization": f"Bearer {admin_token}"}


# ============================================================================
# AUTH
# ============================================================================

def test_login_exitoso():
    response = client.post("/api/v1/auth/login", data={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["usuario"]["username"] == "admin"


def test_login_fallido():
    response = client.post("/api/v1/auth/login", data={
        "username": "admin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401


def test_get_me(auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "admin"
    assert data["rol"] == "admin"


# ============================================================================
# SISTEMA / SALUD
# ============================================================================

def test_salud():
    response = client.get("/api/v1/salud")
    assert response.status_code == 200
    assert "estado" in response.json()


# ============================================================================
# PRODUCTOS
# ============================================================================

def test_listar_productos():
    response = client.get("/api/v1/productos")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_obtener_producto_por_id():
    response = client.get("/api/v1/productos/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert "nombre" in data


def test_obtener_producto_por_sku():
    response = client.get("/api/v1/productos/sku/PROD001")
    assert response.status_code == 200
    assert response.json()["nombre"] == "Leche Asturiana"


def test_obtener_producto_por_barcode_no_existe():
    response = client.get("/api/v1/productos/barcode/999999999")
    assert response.status_code == 404


# ============================================================================
# INVENTARIO
# ============================================================================

def test_resumen_inventario():
    response = client.get("/api/v1/inventario/resumen")
    assert response.status_code == 200
    data = response.json()
    assert "total_productos" in data
    assert "valor_total" in data


def test_obtener_inventario_producto():
    response = client.get("/api/v1/inventario/1")
    assert response.status_code == 200
    data = response.json()
    assert "cantidad" in data


# ============================================================================
# TICKETS
# ============================================================================

def test_crear_ticket():
    payload = {
        "cajero": "test_user",
        "metodo_pago": "efectivo",
        "entrega_efectivo": 50.0,
        "lineas": [
            {"producto_id": 1, "cantidad": 1, "precio_unitario": 2.0}
        ]
    }
    response = client.post("/api/v1/tickets", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "completado"
    assert data["total"] == 2.0


def test_listar_tickets():
    response = client.get("/api/v1/tickets")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_mapa_calor_ventas():
    response = client.get("/api/v1/tickets/estadisticas/mapa-calor?dias=7")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_historial_producto():
    response = client.get("/api/v1/tickets/historial/1?limite=5")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ============================================================================
# PREDICCIONES
# ============================================================================

def test_prediccion_producto():
    response = client.get("/api/v1/prediccion/producto/1?dias_futuro=7")
    assert response.status_code == 200
    data = response.json()
    assert "producto_nombre" in data


def test_alertas_reposicion():
    response = client.get("/api/v1/prediccion/alertas")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analisis_abc():
    response = client.get("/api/v1/prediccion/abc")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_dashboard_predictivo():
    response = client.get("/api/v1/prediccion/dashboard")
    assert response.status_code == 200
    assert "alertas" in response.json()


# ============================================================================
# VISION
# ============================================================================

def test_listar_referencias():
    response = client.get("/api/v1/vision/referencias")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ============================================================================
# CATEGORIAS
# ============================================================================

def test_listar_categorias():
    response = client.get("/api/v1/categorias")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
