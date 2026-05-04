"""
Tests básicos para el módulo de validaciones.
Ejecutar con: python -m pytest tests/test_validators.py -v
"""
import pytest
from app.utils.validators import (
    validar_sku,
    validar_email_proveedor,
    validar_proveedor_nuevo,
    calcular_margen_ganancia,
    validar_stock
)


class TestValidarSKU:
    """Tests para la función validar_sku."""
    
    def test_sku_vacio(self):
        """SKU vacío debe retornar error."""
        errores = validar_sku("", [])
        assert "SKU obligatorio" in errores
    
    def test_sku_muy_corto(self):
        """SKU con menos de 4 caracteres debe retornar error."""
        errores = validar_sku("ABC", [])
        assert "Mínimo 4 caracteres" in errores
    
    def test_sku_muy_largo(self):
        """SKU con más de 20 caracteres debe retornar error."""
        errores = validar_sku("A" * 21, [])
        assert "Máximo 20 caracteres" in errores
    
    def test_sku_duplicado(self):
        """SKU duplicado debe retornar error."""
        productos = [{"id": 1, "sku": "PROD001"}, {"id": 2, "sku": "PROD002"}]
        errores = validar_sku("PROD001", productos)
        assert "SKU duplicado" in errores
    
    def test_sku_valido(self):
        """SKU válido no debe retornar errores."""
        productos = [{"id": 1, "sku": "PROD001"}]
        errores = validar_sku("PROD002", productos)
        assert len(errores) == 0
    
    def test_sku_editando_mismo_producto(self):
        """Al editar, el SKU actual del producto no debe considerarse duplicado."""
        productos = [{"id": 1, "sku": "PROD001"}, {"id": 2, "sku": "PROD002"}]
        errores = validar_sku("PROD001", productos, producto_actual_id=1)
        assert len(errores) == 0
    
    def test_sku_case_insensitive(self):
        """La validación de SKU duplicado debe ser case insensitive."""
        productos = [{"id": 1, "sku": "PROD001"}]
        errores = validar_sku("prod001", productos)
        assert "SKU duplicado" in errores


class TestValidarEmailProveedor:
    """Tests para la función validar_email_proveedor."""
    
    def test_email_vacio(self):
        """Email vacío debe ser inválido."""
        valido, error = validar_email_proveedor("", [])
        assert not valido
        assert "Email obligatorio" in error
    
    def test_email_duplicado(self):
        """Email duplicado debe ser inválido."""
        proveedores = [{"id": 1, "email": "test@test.com"}]
        valido, error = validar_email_proveedor("test@test.com", proveedores)
        assert not valido
        assert "Email ya existe" in error
    
    def test_email_valido(self):
        """Email nuevo debe ser válido."""
        proveedores = [{"id": 1, "email": "test@test.com"}]
        valido, error = validar_email_proveedor("nuevo@test.com", proveedores)
        assert valido
        assert error is None
    
    def test_email_case_insensitive(self):
        """La validación de email debe ser case insensitive."""
        proveedores = [{"id": 1, "email": "Test@Test.COM"}]
        valido, error = validar_email_proveedor("test@test.com", proveedores)
        assert not valido
        assert "Email ya existe" in error


class TestValidarProveedorNuevo:
    """Tests para la función validar_proveedor_nuevo."""
    
    def test_nombre_vacio(self):
        """Nombre vacío debe retornar error."""
        errores = validar_proveedor_nuevo("", "email@test.com", "123456")
        assert "Nombre obligatorio" in errores
    
    def test_nombre_muy_corto(self):
        """Nombre muy corto debe retornar error."""
        errores = validar_proveedor_nuevo("A", "email@test.com", "123456")
        assert "Nombre muy corto" in errores
    
    def test_email_vacio(self):
        """Email vacío debe retornar error."""
        errores = validar_proveedor_nuevo("Proveedor", "", "123456")
        assert "Email obligatorio" in errores
    
    def test_email_invalido(self):
        """Email sin @ o . debe retornar error."""
        errores = validar_proveedor_nuevo("Proveedor", "emailinvalido", "123456")
        assert "Email inválido" in errores
    
    def test_proveedor_valido(self):
        """Datos válidos no deben retornar errores."""
        errores = validar_proveedor_nuevo("Proveedor Test", "test@test.com", "123456789")
        assert len(errores) == 0


class TestCalcularMargenGanancia:
    """Tests para la función calcular_margen_ganancia."""
    
    def test_margen_basico(self):
        """Margen básico: coste 10, venta 15 = 50% margen."""
        margen = calcular_margen_ganancia(15.0, 10.0)
        assert margen == 50.0
    
    def test_margen_cero(self):
        """Sin ganancia: coste 10, venta 10 = 0% margen."""
        margen = calcular_margen_ganancia(10.0, 10.0)
        assert margen == 0.0
    
    def test_margen_negativo(self):
        """Pérdida: coste 10, venta 8 = -20% margen."""
        margen = calcular_margen_ganancia(8.0, 10.0)
        assert margen == -20.0
    
    def test_coste_cero(self):
        """Coste cero debe retornar 0 para evitar división por cero."""
        margen = calcular_margen_ganancia(10.0, 0.0)
        assert margen == 0.0
    
    def test_precio_venta_cero(self):
        """Venta cero con coste positivo = -100% margen (pérdida total)."""
        margen = calcular_margen_ganancia(0.0, 10.0)
        assert margen == -100.0


class TestValidarStock:
    """Tests para la función validar_stock."""
    
    def test_stock_valido(self):
        """Stock dentro de límites debe ser válido."""
        resultado = validar_stock(50, 10, 100)
        assert resultado["valido"] is True
        assert len(resultado["errores"]) == 0
        assert resultado["alerta"] is False
    
    def test_stock_negativo(self):
        """Stock negativo debe ser inválido."""
        resultado = validar_stock(-5, 10, 100)
        assert resultado["valido"] is False
        assert "negativo" in resultado["errores"][0]
    
    def test_stock_excede_maximo(self):
        """Stock mayor al máximo debe ser inválido."""
        resultado = validar_stock(150, 10, 100)
        assert resultado["valido"] is False
        assert "excede" in resultado["errores"][0].lower()
    
    def test_stock_bajo_alerta(self):
        """Stock igual o menor al mínimo debe activar alerta."""
        resultado = validar_stock(5, 10, 100)
        assert resultado["valido"] is True
        assert resultado["alerta"] is True
    
    def test_stock_sobre_minimo(self):
        """Stock mayor al mínimo no debe activar alerta."""
        resultado = validar_stock(15, 10, 100)
        assert resultado["valido"] is True
        assert resultado["alerta"] is False
    
    def test_sin_stock_minimo(self):
        """Sin stock mínimo definido no debe activar alerta."""
        resultado = validar_stock(5, 0, 100)
        assert resultado["alerta"] is False


# Si se ejecuta directamente, mostrar resumen
if __name__ == "__main__":
    print("=" * 60)
    print("TESTS DE VALIDACIÓN - INVENTARIO")
    print("=" * 60)
    print("\nPara ejecutar los tests:")
    print("  python -m pytest tests/test_validators.py -v")
    print("\nPara ejecutar con cobertura:")
    print("  python -m pytest tests/test_validators.py -v --cov=app.utils.validators")
    print("\n" + "=" * 60)
