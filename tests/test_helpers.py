"""
Tests para helpers
"""
import pytest
from app.utils.helpers import (
    format_currency,
    format_date,
    truncate_text,
    calcular_porcentaje,
    get_prod_name,
    to_excel,
)
import pandas as pd


class TestFormatCurrency:
    """Tests para format_currency"""

    def test_formato_basico(self):
        assert format_currency(10.00) == "€10.00"

    def test_formato_con_decimales(self):
        assert format_currency(1.50) == "€1.50"

    def test_formato_redondea_dos_decimales(self):
        assert format_currency(1.556) == "€1.56"

    def test_formato_cero(self):
        assert format_currency(0) == "€0.00"


class TestFormatDate:
    """Tests para format_date"""

    def test_fecha_iso_formatea_correctamente(self):
        result = format_date("2024-04-15T10:30:00")
        assert "15" in result
        assert "2024" in result

    def test_fecha_con_z_formatea(self):
        result = format_date("2024-04-15T10:30:00Z")
        assert "15" in result

    def test_fecha_invalida_devuelve_default(self):
        result = format_date("invalid-date")
        assert "desconocida" in result.lower()


class TestTruncateText:
    """Tests para truncate_text"""

    def test_texto_corto_no_se_trunca(self):
        result = truncate_text("Hola mundo", max_words=5)
        assert result == "Hola mundo"

    def test_texto_largo_se_trunca(self):
        result = truncate_text("uno dos tres cuatro cinco seis siete ocho", max_words=3)
        words = result.split()
        assert len(words) == 3

    def test_texto_vacio_devuelve_vacio(self):
        result = truncate_text("", max_words=5)
        assert result == ""

    def test_none_devuelve_vacio(self):
        result = truncate_text(None, max_words=5)
        assert result == ""


class TestCalcularPorcentaje:
    """Tests para calcular_porcentaje"""

    def test_calculo_basico(self):
        assert calcular_porcentaje(50, 100) == 50.0

    def test_25_porciento(self):
        assert calcular_porcentaje(25, 100) == 25.0

    def test_75_porciento(self):
        assert calcular_porcentaje(75, 100) == 75.0

    def test_maximo_cero_devuelve_100_si_hay_stock(self):
        assert calcular_porcentaje(5, 0) == 100

    def test_maximo_cero_devuelve_0_si_stock_cero(self):
        assert calcular_porcentaje(0, 0) == 0

    def test_sobre_pasa_100_se_capsula(self):
        assert calcular_porcentaje(150, 100) == 100


class TestGetProdName:
    """Tests para get_prod_name"""

    def test_encuentra_producto_por_id(self):
        productos = [{"id": 1, "nombre": "Leche Entera"}]
        assert get_prod_name(1, productos) == "Leche Entera"

    def test_producto_no_encontrado_devuelve_default(self):
        productos = [{"id": 1, "nombre": "Leche"}]
        assert get_prod_name(99, productos) == "Producto"

    def test_lista_vacia_devuelve_default(self):
        assert get_prod_name(1, []) == "Producto"

    def test_multiple_productos_encuentra_correcto(self):
        productos = [
            {"id": 1, "nombre": "Leche"},
            {"id": 2, "nombre": "Yogur"},
            {"id": 3, "nombre": "Queso"},
        ]
        assert get_prod_name(3, productos) == "Queso"


class TestToExcel:
    """Tests para to_excel"""

    def test_dataframe_vacio_devuelve_bytes_vacios(self):
        df = pd.DataFrame()
        result = to_excel(df)
        assert result == b""

    def test_dataframe_none_devuelve_bytes_vacios(self):
        result = to_excel(None)
        assert result == b""

    def test_dataframe_con_datos_devuelve_bytes(self):
        df = pd.DataFrame({"Nombre": ["A", "B"], "Valor": [1, 2]})
        result = to_excel(df)
        assert len(result) > 0