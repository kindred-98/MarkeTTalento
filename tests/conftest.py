"""
Configuración de fixtures para tests
"""
import pytest
from app.logic.inventario import calcular_estado_stock
from app.utils.helpers import calcular_porcentaje


@pytest.fixture
def producto_ejemplo():
    return {
        "id": 1,
        "sku": "SKU001",
        "nombre": "Leche Entera",
        "precio_venta": 1.50,
        "unidad": "litro",
        "stock_minimo": 5,
        "stock_maximo": 50,
        "categoria_id": 1,
    }


@pytest.fixture
def producto_sin_stock():
    return {
        "id": 2,
        "sku": "SKU002",
        "nombre": "Yogur Fresco",
        "stock": 0,
        "stock_maximo": 30,
    }


@pytest.fixture
def producto_critico():
    return {
        "id": 3,
        "sku": "SKU003",
        "nombre": "Queso Artesanal",
        "stock": 5,
        "stock_maximo": 50,
    }


@pytest.fixture
def producto_bajo():
    return {
        "id": 4,
        "sku": "SKU004",
        "nombre": "Mantequilla",
        "stock": 20,
        "stock_maximo": 50,
    }


@pytest.fixture
def producto_saludable():
    return {
        "id": 5,
        "sku": "SKU005",
        "nombre": "Crema de Leche",
        "stock": 40,
        "stock_maximo": 50,
    }


@pytest.fixture
def inventario_ejemplo():
    return {
        "id": 1,
        "producto_id": 1,
        "cantidad": 25,
        "ubicacion": "Almacén A",
    }


@pytest.fixture
def lista_productos():
    return [
        {"id": 1, "sku": "SKU001", "nombre": "Leche Entera", "stock_maximo": 50, "categoria_id": 1},
        {"id": 2, "sku": "SKU002", "nombre": "Yogur Fresco", "stock_maximo": 30, "categoria_id": 1},
        {"id": 3, "sku": "SKU003", "nombre": "Queso Artesanal", "stock_maximo": 50, "categoria_id": 2},
        {"id": 4, "sku": "SKU004", "nombre": "Mantequilla", "stock_maximo": 40, "categoria_id": 2},
        {"id": 5, "sku": "SKU005", "nombre": "Crema de Leche", "stock_maximo": 50, "categoria_id": 1},
    ]