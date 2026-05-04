"""
Tests para la lógica de negocio de inventario.
Ejecutar con: python -m pytest tests/test_inventario_logic.py -v
"""
import pytest
from app.logic.inventario import (
    calcular_estado_stock,
    get_estado_info,
    filtrar_por_estado,
    ordenar_inventario,
    calcular_nuevo_stock,
    preparar_datos_inventario,
)


class TestCalcularEstadoStock:
    """Tests para calcular_estado_stock."""
    
    def test_stock_agotado(self):
        """Stock <= 0 debe retornar 'Agotado'."""
        assert calcular_estado_stock(0, 100) == "Agotado"
        assert calcular_estado_stock(-5, 100) == "Agotado"
    
    def test_stock_critico_25_porciento(self):
        """Stock <= 25% del máximo debe retornar 'Crítico'."""
        assert calcular_estado_stock(25, 100) == "Crítico"
        assert calcular_estado_stock(10, 100) == "Crítico"
    
    def test_stock_bajo_59_porciento(self):
        """Stock entre 26% y 59% debe retornar 'Bajo'."""
        assert calcular_estado_stock(26, 100) == "Bajo"
        assert calcular_estado_stock(50, 100) == "Bajo"
        assert calcular_estado_stock(59, 100) == "Bajo"
    
    def test_stock_saludable(self):
        """Stock >= 60% debe retornar 'Saludable'."""
        assert calcular_estado_stock(60, 100) == "Saludable"
        assert calcular_estado_stock(100, 100) == "Saludable"
    
    def test_stock_maximo_cero(self):
        """Stock máximo 0 debe retornar 'Saludable' si hay stock."""
        assert calcular_estado_stock(10, 0) == "Saludable"
    
    def test_stock_exacto_limites(self):
        """Probar límites exactos."""
        # 25% exacto = Crítico
        assert calcular_estado_stock(25, 100) == "Crítico"
        # 26% = Bajo
        assert calcular_estado_stock(26, 100) == "Bajo"
        # 59% = Bajo
        assert calcular_estado_stock(59, 100) == "Bajo"
        # 60% = Saludable
        assert calcular_estado_stock(60, 100) == "Saludable"


class TestGetEstadoInfo:
    """Tests para get_estado_info."""
    
    def test_estado_existente(self):
        """Debe retornar info de estado existente."""
        info = get_estado_info("Saludable")
        assert isinstance(info, dict)
        assert "color" in info or "icono" in info or len(info) > 0
    
    def test_estado_no_existente(self):
        """Estado inexistente debe retornar info de 'Saludable' por defecto."""
        info = get_estado_info("EstadoInexistente")
        assert isinstance(info, dict)


class TestFiltrarPorEstado:
    """Tests para filtrar_por_estado."""
    
    def test_filtro_todos(self):
        """Filtro 'Todos' debe retornar todos los datos."""
        datos = [
            {"estado": "Saludable", "nombre": "A"},
            {"estado": "Crítico", "nombre": "B"},
        ]
        resultado = filtrar_por_estado(datos, "Todos")
        assert len(resultado) == 2
    
    def test_filtro_especifico(self):
        """Filtro específico debe retornar solo coincidencias."""
        datos = [
            {"estado": "Saludable", "nombre": "A"},
            {"estado": "Crítico", "nombre": "B"},
            {"estado": "Saludable", "nombre": "C"},
        ]
        resultado = filtrar_por_estado(datos, "Saludable")
        assert len(resultado) == 2
        assert all(d["estado"] == "Saludable" for d in resultado)
    
    def test_filtro_sin_coincidencias(self):
        """Filtro sin coincidencias debe retornar lista vacía."""
        datos = [
            {"estado": "Saludable", "nombre": "A"},
        ]
        resultado = filtrar_por_estado(datos, "Agotado")
        assert len(resultado) == 0
    
    def test_filtro_lista_vacia(self):
        """Filtro en lista vacía debe retornar lista vacía."""
        resultado = filtrar_por_estado([], "Saludable")
        assert len(resultado) == 0


class TestOrdenarInventario:
    """Tests para ordenar_inventario."""
    
    def test_ordenar_por_nombre(self):
        """Ordenar por nombre A-Z."""
        datos = [
            {"producto": {"nombre": "Zanahoria"}, "stock": 10},
            {"producto": {"nombre": "Agua"}, "stock": 5},
            {"producto": {"nombre": "Manzana"}, "stock": 8},
        ]
        resultado = ordenar_inventario(datos, "Producto (A-Z)")
        assert resultado[0]["producto"]["nombre"] == "Agua"
        assert resultado[1]["producto"]["nombre"] == "Manzana"
        assert resultado[2]["producto"]["nombre"] == "Zanahoria"
    
    def test_ordenar_por_stock_mayor(self):
        """Ordenar por stock de mayor a menor."""
        datos = [
            {"producto": {"nombre": "A"}, "stock": 10},
            {"producto": {"nombre": "B"}, "stock": 50},
            {"producto": {"nombre": "C"}, "stock": 30},
        ]
        resultado = ordenar_inventario(datos, "Stock (mayor)")
        assert resultado[0]["stock"] == 50
        assert resultado[1]["stock"] == 30
        assert resultado[2]["stock"] == 10
    
    def test_ordenar_por_stock_menor(self):
        """Ordenar por stock de menor a mayor."""
        datos = [
            {"producto": {"nombre": "A"}, "stock": 50},
            {"producto": {"nombre": "B"}, "stock": 10},
            {"producto": {"nombre": "C"}, "stock": 30},
        ]
        resultado = ordenar_inventario(datos, "Stock (menor)")
        assert resultado[0]["stock"] == 10
        assert resultado[1]["stock"] == 30
        assert resultado[2]["stock"] == 50
    
    def test_ordenar_criterio_invalido(self):
        """Criterio inválido debe retornar datos sin ordenar."""
        datos = [
            {"producto": {"nombre": "B"}, "stock": 10},
            {"producto": {"nombre": "A"}, "stock": 5},
        ]
        resultado = ordenar_inventario(datos, "Criterio Invalido")
        assert resultado[0]["producto"]["nombre"] == "B"
        assert resultado[1]["producto"]["nombre"] == "A"
    
    def test_ordenar_nombre_vacio(self):
        """Productos sin nombre deben ordenarse correctamente."""
        datos = [
            {"producto": {"nombre": "Z"}, "stock": 10},
            {"producto": {}, "stock": 5},  # Sin nombre
            {"producto": {"nombre": ""}, "stock": 8},  # Nombre vacío
            {"producto": {"nombre": "A"}, "stock": 3},
        ]
        resultado = ordenar_inventario(datos, "Producto (A-Z)")
        # Los vacíos van primero (orden lexicográfico)
        assert resultado[0]["producto"].get("nombre", "") == ""


class TestCalcularNuevoStock:
    """Tests para calcular_nuevo_stock."""
    
    def test_ingreso_positivo(self):
        """Ingreso positivo debe sumar al stock."""
        assert calcular_nuevo_stock(100, 50) == 150
        assert calcular_nuevo_stock(0, 10) == 10
    
    def test_ingreso_cero(self):
        """Ingreso cero no debe cambiar el stock."""
        assert calcular_nuevo_stock(100, 0) == 100
    
    def test_ingreso_negativo(self):
        """Ingreso negativo (retiro) debe restar del stock."""
        assert calcular_nuevo_stock(100, -30) == 70
    
    def test_stock_negativo_resultante(self):
        """Si el retiro es mayor al stock, resultado puede ser negativo."""
        assert calcular_nuevo_stock(20, -50) == -30


class TestPrepararDatosInventario:
    """Tests para preparar_datos_inventario."""
    
    def test_preparar_datos_basicos(self):
        """Preparación básica de datos."""
        inventarios = [
            {"producto_id": 1, "cantidad": 50, "ubicacion": "Almacén A"}
        ]
        productos = [
            {
                "id": 1,
                "nombre": "Producto Test",
                "sku": "TEST001",
                "stock_maximo": 100,
                "stock_minimo": 10,
                "precio_coste": 10.0,
                "precio_venta": 15.0,
            }
        ]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        
        assert len(resultado) == 1
        assert resultado[0]["stock"] == 50
        assert resultado[0]["max_s"] == 100
        assert resultado[0]["estado"] == "Bajo"  # 50% = Bajo
        assert resultado[0]["ganancia"] == 5.0
        assert resultado[0]["margen"] == 50.0
    
    def test_preparar_datos_sin_producto(self):
        """Inventario sin producto correspondiente debe ignorarse."""
        inventarios = [
            {"producto_id": 999, "cantidad": 50, "ubicacion": "Almacén A"}
        ]
        productos = [
            {"id": 1, "nombre": "Otro Producto"}
        ]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        assert len(resultado) == 0
    
    def test_preparar_datos_stock_maximo_none(self):
        """Stock máximo None debe usar valor por defecto 100."""
        inventarios = [
            {"producto_id": 1, "cantidad": 50, "ubicacion": "Almacén A"}
        ]
        productos = [
            {
                "id": 1,
                "nombre": "Producto",
                "stock_maximo": None,
                "precio_coste": 10.0,
                "precio_venta": 15.0,
            }
        ]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        assert resultado[0]["max_s"] == 100
    
    def test_preparar_datos_precio_coste_none(self):
        """Precio coste None debe tratarse como 0."""
        inventarios = [
            {"producto_id": 1, "cantidad": 50, "ubicacion": "Almacén A"}
        ]
        productos = [
            {
                "id": 1,
                "nombre": "Producto",
                "stock_maximo": 100,
                "precio_coste": None,
                "precio_venta": 15.0,
            }
        ]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        assert resultado[0]["precio_coste"] == 0
        assert resultado[0]["ganancia"] == 15.0
        assert resultado[0]["margen"] == 0  # División por cero evitada
    
    def test_preparar_datos_multiples_items(self):
        """Preparar múltiples items de inventario."""
        inventarios = [
            {"producto_id": 1, "cantidad": 10, "ubicacion": "Almacén A"},
            {"producto_id": 2, "cantidad": 80, "ubicacion": "Almacén B"},
        ]
        productos = [
            {"id": 1, "nombre": "Prod1", "stock_maximo": 100, "precio_coste": 10, "precio_venta": 15},
            {"id": 2, "nombre": "Prod2", "stock_maximo": 100, "precio_coste": 20, "precio_venta": 25},
        ]
        
        resultado = preparar_datos_inventario(inventarios, productos)
        
        assert len(resultado) == 2
        assert resultado[0]["estado"] == "Crítico"  # 10%
        assert resultado[1]["estado"] == "Saludable"  # 80%
    
    def test_preparar_datos_listas_vacias(self):
        """Listas vacías deben retornar lista vacía."""
        resultado = preparar_datos_inventario([], [])
        assert resultado == []


if __name__ == "__main__":
    print("=" * 60)
    print("TESTS DE LÓGICA DE INVENTARIO")
    print("=" * 60)
    print("\nEjecutar con: python -m pytest tests/test_inventario_logic.py -v")
    print("=" * 60)
