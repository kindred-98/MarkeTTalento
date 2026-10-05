"""
Tests para el módulo de API (app/utils/api.py).

`app/utils/api.py` es una capa de acceso directo a SQLite (no un cliente HTTP),
por lo que los tests trabajan contra una base de datos temporal aislada en vez
de mockear `requests`.

Ejecutar con: python -m pytest tests/test_api.py -v
"""
import os
import tempfile

import pytest
from sqlalchemy.exc import SQLAlchemyError

# El path de la BD debe fijarse ANTES de importar app.utils.api: app/db.py
# construye el engine en tiempo de importacion.
_TMP_DIR = tempfile.mkdtemp(prefix="markettalento_test_")
os.environ["DATABASE_PATH"] = os.path.join(_TMP_DIR, "test.db")

from app.db import DatabaseAccess, get_engine  # noqa: E402
from app.utils import api as api_mod  # noqa: E402
from app.utils.api import (  # noqa: E402
    api_get,
    api_post,
    api_put,
    api_delete,
    verificar_api,
    esperar_api,
)
from src.core.database.base import Base  # noqa: E402
from src.dominio.entidades.entidades import (  # noqa: E402
    Categoria, Proveedor, Producto, Inventario, Ticket
)

MODELOS = (Ticket, Inventario, Producto, Proveedor, Categoria)


@pytest.fixture(scope="module")
def bd():
    """Crea el esquema y expone una sesion compartida durante el modulo."""
    Base.metadata.create_all(bind=get_engine())
    session = DatabaseAccess().session
    yield session
    session.close()


@pytest.fixture(autouse=True)
def limpio(bd):
    """Vacia todas las tablas antes de cada test para que sean independientes."""
    for modelo in MODELOS:
        bd.query(modelo).delete()
    bd.commit()
    return bd


@pytest.fixture
def datos(bd):
    """Categoría, proveedor y producto base. Devuelve sus ids."""
    cat = Categoria(nombre="Bebidas", descripcion="Refrescos y agua")
    prov = Proveedor(nombre="Distribuciones SL", email="ventas@distribuciones.es",
                     telefono="+34 600 000 000")
    bd.add_all([cat, prov])
    bd.flush()

    prod = Producto(
        sku="BEB-001", codigo_barras="8412345678901", nombre="Agua 1.5L",
        descripcion="Agua mineral sin gas", precio_venta=0.75, precio_coste=0.30,
        unidad="botella", stock_minimo=10, stock_maximo=100, tiempo_reposicion=3,
        categoria_id=cat.id, proveedor_id=prov.id,
    )
    bd.add(prod)
    bd.flush()
    bd.add(Inventario(producto_id=prod.id, cantidad=40, ubicacion="Almacén A"))
    bd.commit()

    return {"cat_id": cat.id, "prov_id": prov.id, "prod_id": prod.id}


class TestApiGet:
    """Tests para api_get."""

    def test_get_categorias(self, datos):
        resultado = api_get("/api/v1/categorias")

        assert any(c["nombre"] == "Bebidas" for c in resultado)
        assert {"id", "nombre", "descripcion"} <= set(resultado[0])

    def test_get_proveedores(self, datos):
        resultado = api_get("/api/v1/proveedores")

        assert any(p["nombre"] == "Distribuciones SL" for p in resultado)

    def test_get_productos(self, datos):
        resultado = api_get("/api/v1/productos")

        prod = next(p for p in resultado if p["id"] == datos["prod_id"])
        assert prod["sku"] == "BEB-001"
        assert prod["categoria"]["nombre"] == "Bebidas"
        assert prod["proveedor"]["nombre"] == "Distribuciones SL"
        assert prod["stock"] == 40

    def test_get_inventario(self, datos):
        resultado = api_get("/api/v1/inventario")

        fila = next(i for i in resultado if i["producto_id"] == datos["prod_id"])
        assert fila["stock"] == 40
        assert fila["max_s"] == 100
        assert fila["estado"] == "Saludable"
        assert fila["ubicacion"] == "Almacén A"

    def test_get_inventario_resumen(self, datos):
        resumen = api_get("/api/v1/inventario/resumen")

        assert resumen["total_productos"] >= 1
        assert resumen["total_unidades"] >= 40

    def test_get_tickets_vacio(self, datos):
        resultado = api_get("/api/v1/tickets")

        assert resultado == []

    def test_get_endpoint_desconocido(self, datos):
        assert api_get("/api/v1/inexistente") == []

    def test_get_salud(self, datos):
        assert api_get("/api/v1/salud") == {"estado": "saludable"}


class TestApiPost:
    """Tests para api_post."""

    def test_post_producto_crea_inventario(self, datos):
        resultado = api_post("/api/v1/productos", {
            "sku": "BEB-002", "nombre": "Refresco 2L", "precio_venta": 2.10,
            "unidad": "botella", "categoria_id": datos["cat_id"],
            "cantidad_inicial": 7, "ubicacion": "Almacén B",
        })

        assert resultado["mensaje"] == "Producto creado"
        filas = api_get("/api/v1/inventario")
        nuevo = next(i for i in filas if i["producto"]["sku"] == "BEB-002")
        assert nuevo["stock"] == 7
        assert nuevo["ubicacion"] == "Almacén B"

    def test_post_proveedor(self, datos):
        resultado = api_post("/api/v1/proveedores", {
            "nombre": "Proveedor Nuevo", "email": "nuevo@proveedor.es",
        })

        assert resultado["nombre"] == "Proveedor Nuevo"
        assert any(p["nombre"] == "Proveedor Nuevo"
                   for p in api_get("/api/v1/proveedores"))

    def test_post_inventario_actualiza_cantidad(self, datos):
        resultado = api_post(f"/api/v1/inventario/{datos['prod_id']}", {"cantidad": 12})

        assert resultado["mensaje"] == "Inventario actualizado"
        filas = api_get("/api/v1/inventario")
        assert next(i for i in filas
                    if i["producto_id"] == datos["prod_id"])["stock"] == 12

    def test_post_inventario_inexistente(self, datos):
        resultado = api_post("/api/v1/inventario/999999", {"cantidad": 5})

        assert resultado == {"error": "Inventario no encontrado"}

    def test_post_producto_sin_categoria_devuelve_error(self, datos):
        resultado = api_post("/api/v1/productos", {"sku": "SIN-CAT", "nombre": "X"})

        assert "error" in resultado

    def test_post_endpoint_no_soportado(self, datos):
        assert api_post("/api/v1/desconocido", {}) is None


class TestApiPut:
    """Tests para api_put."""

    def test_put_actualiza_producto(self, datos):
        resultado = api_put(f"/api/v1/productos/{datos['prod_id']}",
                            {"nombre": "Agua 1.5L Renovada"})

        assert resultado["mensaje"] == "Producto actualizado"
        prod = next(p for p in api_get("/api/v1/productos")
                    if p["id"] == datos["prod_id"])
        assert prod["nombre"] == "Agua 1.5L Renovada"

    def test_put_ignora_id(self, datos):
        api_put(f"/api/v1/productos/{datos['prod_id']}", {"id": 99999})

        prod = next(p for p in api_get("/api/v1/productos")
                    if p["id"] == datos["prod_id"])
        assert prod["id"] == datos["prod_id"]

    def test_put_producto_inexistente(self, datos):
        resultado = api_put("/api/v1/productos/999999", {"nombre": "Test"})

        assert resultado == {"error": "Producto no encontrado"}

    def test_put_endpoint_no_soportado(self, datos):
        resultado = api_put("/api/v1/categorias/1", {"nombre": "Test"})

        assert resultado == {"error": "Endpoint no soportado"}

    def test_put_id_no_numerico(self, datos):
        resultado = api_put("/api/v1/productos/abc", {"nombre": "Test"})

        assert "error" in resultado


class TestApiDelete:
    """Tests para api_delete."""

    def test_delete_hace_baja_logica(self, datos):
        assert api_delete(f"/api/v1/productos/{datos['prod_id']}") is True

        assert all(p["id"] != datos["prod_id"] for p in api_get("/api/v1/productos"))

    def test_delete_producto_inexistente(self, datos):
        assert api_delete("/api/v1/productos/999999") is False

    def test_delete_endpoint_no_soportado(self, datos):
        assert api_delete("/api/v1/categorias/1") is False

    def test_delete_id_no_numerico(self, datos):
        assert api_delete("/api/v1/productos/abc") is False


class TestVerificarApi:
    """Tests para verificar_api."""

    def test_bd_respondiendo(self):
        assert verificar_api() is True

    def test_falla_con_db_rota(self, monkeypatch):
        def _boom(*_args, **_kwargs):
            raise SQLAlchemyError("db no disponible")

        monkeypatch.setattr(api_mod.db.session, "execute", _boom)
        monkeypatch.setattr(api_mod.db.session, "rollback", lambda: None)

        assert verificar_api() is False


class TestEsperarApi:
    """Tests para esperar_api."""

    def test_exitoso_en_el_primer_intento(self):
        assert esperar_api(intentos=3, espera_s=0) is True

    def test_falla_despues_de_todos_los_intentos(self, monkeypatch):
        intentos = []

        def _falla():
            intentos.append(1)
            return False

        monkeypatch.setattr("app.utils.api.verificar_api", _falla)

        assert esperar_api(intentos=4, espera_s=0) is False
        assert len(intentos) == 4

    def test_exitoso_en_un_intento_posterior(self, monkeypatch):
        respuestas = iter([False, False, True])
        intentos = []

        def _secuencia():
            intentos.append(1)
            return next(respuestas)

        monkeypatch.setattr("app.utils.api.verificar_api", _secuencia)

        assert esperar_api(intentos=5, espera_s=0) is True
        assert len(intentos) == 3

    def test_intentos_no_positivo_usa_un_intento(self, monkeypatch):
        intentos = []

        def _falla():
            intentos.append(1)
            return False

        monkeypatch.setattr("app.utils.api.verificar_api", _falla)

        assert esperar_api(intentos=0, espera_s=0) is False
        assert len(intentos) == 1
