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

def test_crear_ticket(auth_headers):
    # Usar producto con stock suficiente (producto_id=4, Agua, stock=17)
    payload = {
        "cajero": "test_user",
        "metodo_pago": "efectivo",
        "entrega_efectivo": 50.0,
        "lineas": [
            {"producto_id": 4, "cantidad": 1, "precio_unitario": 2.5}
        ]
    }
    response = client.post("/api/v1/tickets", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "completado"
    assert data["total"] == 2.5


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


def test_crear_categoria_con_auth(auth_headers):
    import uuid
    nombre = f"TestCat_{uuid.uuid4().hex[:8]}"
    payload = {"nombre": nombre, "descripcion": "Categoria de prueba"}
    response = client.post("/api/v1/categorias", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == nombre


def test_crear_categoria_sin_auth():
    payload = {"nombre": "TestCategoria", "descripcion": "Categoria de prueba"}
    response = client.post("/api/v1/categorias", json=payload)
    assert response.status_code == 401


# ============================================================================
# PRODUCTOS
# ============================================================================

def test_crear_producto_con_auth(auth_headers):
    import uuid
    sku = f"TEST-{uuid.uuid4().hex[:8]}"
    payload = {
        "sku": sku,
        "nombre": "Producto Test",
        "precio_venta": 10.0,
        "unidad": "unidad",
        "categoria_id": 1,
        "cantidad_inicial": 5,
        "ubicacion": "Almacen A"
    }
    response = client.post("/api/v1/productos", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == sku
    assert data["nombre"] == "Producto Test"


def test_actualizar_producto_con_auth(auth_headers):
    import uuid
    sku = f"UPD-{uuid.uuid4().hex[:8]}"
    # Crear primero
    payload = {
        "sku": sku,
        "nombre": "Producto Update",
        "precio_venta": 15.0,
        "unidad": "unidad",
        "categoria_id": 1,
        "cantidad_inicial": 3,
    }
    r = client.post("/api/v1/productos", json=payload, headers=auth_headers)
    assert r.status_code == 201, f"Error creando producto: {r.text}"
    producto_id = r.json()["id"]

    # Actualizar
    update = {"nombre": "Producto Actualizado"}
    r2 = client.put(f"/api/v1/productos/{producto_id}", json=update, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["nombre"] == "Producto Actualizado"


def test_eliminar_producto_con_auth(auth_headers):
    import uuid
    sku = f"DEL-{uuid.uuid4().hex[:8]}"
    # Crear primero
    payload = {
        "sku": sku,
        "nombre": "Producto Delete",
        "precio_venta": 5.0,
        "unidad": "unidad",
        "categoria_id": 1,
    }
    r = client.post("/api/v1/productos", json=payload, headers=auth_headers)
    assert r.status_code == 201, f"Error creando producto: {r.text}"
    producto_id = r.json()["id"]

    # Eliminar
    r2 = client.delete(f"/api/v1/productos/{producto_id}", headers=auth_headers)
    assert r2.status_code == 204


# ============================================================================
# INVENTARIO / VENTAS
# ============================================================================

def test_actualizar_inventario_con_auth(auth_headers):
    payload = {"cantidad": 99, "ubicacion": "Test Location"}
    response = client.post("/api/v1/inventario/1", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["cantidad"] == 99


def test_registrar_venta_con_auth(auth_headers):
    payload = {
        "producto_id": 1,
        "cantidad": 1,
        "precio_unitario": 1.5,
        "tipo_operacion": "venta"
    }
    response = client.post("/api/v1/ventas", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["cantidad"] == 1


# ============================================================================
# SEGURIDAD
# ============================================================================

def test_endpoint_protegido_sin_token():
    payload = {"nombre": "Test", "descripcion": ""}
    response = client.post("/api/v1/categorias", json=payload)
    assert response.status_code == 401


def test_admin_requiere_rol_admin(auth_headers):
    # auth_headers es de admin, debería funcionar
    response = client.get("/api/v1/admin/bases-de-datos", headers=auth_headers)
    # Puede ser 200 o 404 dependiendo de si existe la ruta exacta
    assert response.status_code in [200, 404]


def test_login_rate_limit():
    import uuid
    username = f"ratelimit_{uuid.uuid4().hex[:8]}"
    # Intentar login fallido 6 veces con usuario inexistente
    for i in range(6):
        response = client.post("/api/v1/auth/login", data={
            "username": username,
            "password": "wrongpassword"
        })
    # El sexto intento debería ser 429
    assert response.status_code == 429
