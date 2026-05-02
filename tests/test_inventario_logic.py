"""
Tests para lógica de inventario
"""
import pytest
from app.logic.inventario import (
    calcular_estado_stock,
    get_estado_info,
    filtrar_por_estado,
    ordenar_inventario,
    calcular_nuevo_stock,
    preparar_datos_inventario,
    validar_stock,
)


class TestCalcularEstadoStock:
    """Tests para calcular_estado_stock"""

    def test_stock_cero_devuelve_agotado(self):
        assert calcular_estado_stock(0, 50) == "Agotado"

    def test_stock_negativo_devuelve_agotado(self):
        assert calcular_estado_stock(-5, 50) == "Agotado"

    def test_stock_25_porciento_es_critico(self):
        assert calcular_estado_stock(12, 50) == "Crítico"

    def test_stock_25_porciento_exacto_es_critico(self):
        assert calcular_estado_stock(12.5, 50) == "Crítico"

    def test_stock_26_porciento_es_bajo(self):
        assert calcular_estado_stock(13, 50) == "Bajo"

    def test_stock_59_porciento_es_bajo(self):
        assert calcular_estado_stock(29.5, 50) == "Bajo"

    def test_stock_60_porciento_es_saludable(self):
        assert calcular_estado_stock(30, 50) == "Saludable"

    def test_stock_100_porciento_es_saludable(self):
        assert calcular_estado_stock(50, 50) == "Saludable"

    def test_stock_maximo_cero_devuelve_saludable(self):
        assert calcular_estado_stock(10, 0) == "Saludable"

    def test_stock_mayor_al_maximo_devuelve_saludable(self):
        assert calcular_estado_stock(100, 50) == "Saludable"


class TestGetEstadoInfo:
    """Tests para get_estado_info"""

    def test_estado_agotado_devuelve_info(self):
        info = get_estado_info("Agotado")
        assert "color" in info
        assert "texto" in info

    def test_estado_critico_devuelve_info(self):
        info = get_estado_info("Crítico")
        assert info["color"] == "#ef4444"

    def test_estado_bajo_devuelve_info(self):
        info = get_estado_info("Bajo")
        assert info["color"] == "#f59e0b"

    def test_estado_saludable_devuelve_info(self):
        info = get_estado_info("Saludable")
        assert info["color"] == "#10b981"

    def test_estado_desconocido_devuelve_saludable(self):
        info = get_estado_info("Desconocido")
        assert info["color"] == "#10b981"


class TestFiltrarPorEstado:
    """Tests para filtrar_por_estado"""

    def test_filtro_todos_devuelve_todos(self):
        datos = [
            {"estado": "Agotado", "nombre": "A"},
            {"estado": "Crítico", "nombre": "B"},
            {"estado": "Saludable", "nombre": "C"},
        ]
        resultado = filtrar_por_estado(datos, "Todos")
        assert len(resultado) == 3

    def test_filtro_agotado_devuelve_solo_agotados(self):
        datos = [
            {"estado": "Agotado", "nombre": "A"},
            {"estado": "Crítico", "nombre": "B"},
            {"estado": "Agotado", "nombre": "C"},
        ]
        resultado = filtrar_por_estado(datos, "Agotado")
        assert len(resultado) == 2
        assert all(d["estado"] == "Agotado" for d in resultado)

    def test_filtro_sin_coincidencias_devuelve_vacio(self):
        datos = [{"estado": "Crítico", "nombre": "A"}]
        resultado = filtrar_por_estado(datos, "Agotado")
        assert len(resultado) == 0


class TestOrdenarInventario:
    """Tests para ordenar_inventario"""

    def test_ordenar_por_nombre_ascendente(self):
        datos = [
            {"producto": {"nombre": "Zapato"}, "stock": 10},
            {"producto": {"nombre": "Ana"}, "stock": 20},
            {"producto": {"nombre": "Bravo"}, "stock": 5},
        ]
        resultado = ordenar_inventario(datos, "Producto (A-Z)")
        assert resultado[0]["producto"]["nombre"] == "Ana"
        assert resultado[1]["producto"]["nombre"] == "Bravo"
        assert resultado[2]["producto"]["nombre"] == "Zapato"

    def test_ordenar_por_stock_mayor(self):
        datos = [
            {"stock": 10},
            {"stock": 50},
            {"stock": 5},
        ]
        resultado = ordenar_inventario(datos, "Stock (mayor)")
        assert resultado[0]["stock"] == 50
        assert resultado[1]["stock"] == 10
        assert resultado[2]["stock"] == 5

    def test_ordenar_por_stock_menor(self):
        datos = [
            {"stock": 10},
            {"stock": 50},
            {"stock": 5},
        ]
        resultado = ordenar_inventario(datos, "Stock (menor)")
        assert resultado[0]["stock"] == 5
        assert resultado[1]["stock"] == 10
        assert resultado[2]["stock"] == 50


class TestCalcularNuevoStock:
    """Tests para calcular_nuevo_stock"""

    def test_ingreso_suma_correctamente(self):
        assert calcular_nuevo_stock(20, 10) == 30

    def test_ingreso_cero_devuelve_stock_actual(self):
        assert calcular_nuevo_stock(20, 0) == 20

    def test_ingreso_negativo_resta_correctamente(self):
        assert calcular_nuevo_stock(20, -5) == 15


class TestPrepararDatosInventario:
    """Tests para preparar_datos_inventario"""

    def test_prepara_datos_correctamente(self):
        inventarios = [{"producto_id": 1, "cantidad": 35, "ubicacion": "Almacén A"}]
        productos = [{"id": 1, "nombre": "Leche", "stock_maximo": 50, "stock_minimo": 5}]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        
        assert len(resultado) == 1
        assert resultado[0]["stock"] == 35
        assert resultado[0]["producto"]["nombre"] == "Leche"
        assert resultado[0]["estado"] == "Saludable"
        assert resultado[0]["ubicacion"] == "Almacén A"

    def test_salta_inventario_sin_producto(self):
        inventarios = [{"producto_id": 99, "cantidad": 25}]
        productos = [{"id": 1, "nombre": "Leche", "stock_maximo": 50}]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        
        assert len(resultado) == 0

    def test_calcula_estado_agotado(self):
        inventarios = [{"producto_id": 1, "cantidad": 0}]
        productos = [{"id": 1, "nombre": "Leche", "stock_maximo": 50}]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        
        assert resultado[0]["estado"] == "Agotado"


class TestValidarStock:
    """Tests para validar_stock"""

    def test_stock_valido(self):
        resultado = validar_stock(25, 5, 50)
        assert resultado["valido"] is True
        assert len(resultado["errores"]) == 0
        assert resultado["alerta"] is False

    def test_stock_negativo_es_invalido(self):
        resultado = validar_stock(-5, 5, 50)
        assert resultado["valido"] is False
        assert "negativo" in resultado["errores"][0].lower()

    def test_stock_sobre_pasa_maximo(self):
        resultado = validar_stock(60, 5, 50)
        assert resultado["valido"] is False
        assert "excede" in resultado["errores"][0].lower()

    def test_stock_en_minimo_es_alerta(self):
        resultado = validar_stock(5, 5, 50)
        assert resultado["alerta"] is True

    def test_stock_cero_es_alerta(self):
        resultado = validar_stock(0, 5, 50)
        assert resultado["alerta"] is True