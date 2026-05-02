"""
Tests para lógica de ventas
"""
import pytest
from app.logic.venta import (
    calcular_total_venta,
    validar_venta,
    preparar_venta_data,
    formatear_fecha_venta,
    preparar_datos_ventas,
    calcular_totales_ventas,
)


class TestCalcularTotalVenta:
    """Tests para calcular_total_venta"""

    def test_calculo_basico(self):
        assert calcular_total_venta(5, 2.00) == 10.00

    def test_calculo_con_decimales(self):
        assert calcular_total_venta(3, 1.50) == 4.50

    def test_cantidad_cero_devuelve_cero(self):
        assert calcular_total_venta(0, 10.00) == 0

    def test_precio_cero_devuelve_cero(self):
        assert calcular_total_venta(5, 0) == 0


class TestValidarVenta:
    """Tests para validar_venta"""

    def test_venta_valida(self):
        resultado = validar_venta(producto_id=1, cantidad=5, stock_actual=20)
        assert resultado["valido"] is True
        assert len(resultado["errores"]) == 0

    def test_cantidad_cero_invalida(self):
        resultado = validar_venta(producto_id=1, cantidad=0, stock_actual=20)
        assert resultado["valido"] is False
        assert any("mayor a 0" in e for e in resultado["errores"])

    def test_cantidad_negativa_invalida(self):
        resultado = validar_venta(producto_id=1, cantidad=-3, stock_actual=20)
        assert resultado["valido"] is False

    def test_cantidad_excede_stock(self):
        resultado = validar_venta(producto_id=1, cantidad=25, stock_actual=20)
        assert resultado["valido"] is False
        assert any("insuficiente" in e.lower() for e in resultado["errores"])

    def test_cantidad_igual_al_stock_es_valida(self):
        resultado = validar_venta(producto_id=1, cantidad=20, stock_actual=20)
        assert resultado["valido"] is True


class TestPrepararVentaData:
    """Tests para preparar_venta_data"""

    def test_prepara_data_correctamente(self):
        data = preparar_venta_data(producto_id=1, cantidad=5, precio_unitario=2.00)
        
        assert data["producto_id"] == 1
        assert data["cantidad"] == 5
        assert data["precio_unitario"] == 2.00

    def test_data_lista_para_api(self):
        data = preparar_venta_data(producto_id=42, cantidad=10, precio_unitario=1.50)
        
        assert len(data) == 3
        assert "producto_id" in data
        assert "cantidad" in data
        assert "precio_unitario" in data


class TestFormatearFechaVenta:
    """Tests para formatear_fecha_venta"""

    def test_formato_fecha_iso(self):
        resultado = formatear_fecha_venta("2024-04-15T10:30:00")
        assert "15" in resultado
        assert "2024" in resultado

    def test_fecha_con_z(self):
        resultado = formatear_fecha_venta("2024-04-15T10:30:00Z")
        assert "15" in resultado

    def test_fecha_invalida_devuelve_default(self):
        resultado = formatear_fecha_venta("fecha-invalida")
        assert "desconocida" in resultado.lower()


class TestPrepararDatosVentas:
    """Tests para preparar_datos_ventas"""

    def test_prepara_ventas_con_productos(self):
        ventas = [
            {"id": 1, "producto_id": 1, "cantidad": 5, "precio_unitario": 2.00, "fecha": "2024-04-15T10:00:00"},
        ]
        productos = [{"id": 1, "nombre": "Leche Entera"}]
        
        resultado = preparar_datos_ventas(ventas, productos)
        
        assert len(resultado) == 1
        assert resultado[0]["producto_nombre"] == "Leche Entera"
        assert resultado[0]["total"] == 10.00

    def test_calcula_total_correctamente(self):
        ventas = [
            {"id": 1, "producto_id": 1, "cantidad": 3, "precio_unitario": 5.00, "fecha": "2024-04-15T10:00:00"},
        ]
        productos = [{"id": 1, "nombre": "Queso"}]
        
        resultado = preparar_datos_ventas(ventas, productos)
        
        assert resultado[0]["total"] == 15.00


class TestCalcularTotalesVentas:
    """Tests para calcular_totales_ventas"""

    def test_calcula_totales_correctamente(self):
        ventas = [
            {"cantidad": 5, "total": 10.00},
            {"cantidad": 3, "total": 15.00},
            {"cantidad": 2, "total": 8.00},
        ]
        
        resultado = calcular_totales_ventas(ventas)
        
        assert resultado["total_ventas"] == 3
        assert resultado["total_unidades"] == 10
        assert resultado["total_ingresos"] == 33.00

    def test_ventas_vacias(self):
        resultado = calcular_totales_ventas([])
        
        assert resultado["total_ventas"] == 0
        assert resultado["total_unidades"] == 0
        assert resultado["total_ingresos"] == 0