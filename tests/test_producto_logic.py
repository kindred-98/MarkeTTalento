"""
Tests para lógica de productos
"""
import pytest
from app.logic.producto import (
    get_categoria_emoji,
    get_descripcion_default,
    validar_producto,
    filtrar_productos,
    preparar_producto_data,
)


"""
Tests para lógica de productos
"""
import pytest
import json
from app.logic.producto import (
    get_categoria_emoji,
    get_descripcion_default,
    validar_producto,
    filtrar_productos,
    preparar_producto_data,
)
from app.views.productos import _export_to_json, _export_to_excel


class TestExportToJson:
    """Tests para export JSON"""

    def test_export_devuelve_json_valido(self):
        productos = [
            {"id": 1, "sku": "SKU001", "nombre": "Leche", "precio_venta": 1.50,
             "precio_coste": 1.00, "unidad": "litro", "stock_maximo": 50,
             "categoria_id": 1, "proveedor_id": 1, "descripcion": "Leche entera",
             "codigo_barras": None, "tiempo_reposicion": 3}
        ]
        inventarios = [{"producto_id": 1, "cantidad": 10}]
        categorias = [{"id": 1, "nombre": "Lacteos"}]
        proveedores = [{"id": 1, "nombre": "Proveedor A"}]
        
        resultado = _export_to_json(productos, inventarios, categorias, proveedores)
        data = json.loads(resultado)
        
        assert len(data) == 1
        assert data[0]["sku"] == "SKU001"
        assert data[0]["nombre"] == "Leche"
        assert data[0]["precio_venta"] == 1.50
        assert data[0]["stock"] == 10
        assert data[0]["categoria"] == "Lacteos"
        assert data[0]["proveedor"] == "Proveedor A"

    def test_export_sin_proveedor_devuelve_default(self):
        productos = [
            {"id": 1, "sku": "SKU001", "nombre": "Leche", "precio_venta": 1.50,
             "precio_coste": None, "unidad": "litro", "stock_maximo": 50,
             "categoria_id": 1, "proveedor_id": None, "descripcion": "Leche",
             "codigo_barras": None, "tiempo_reposicion": 3}
        ]
        inventarios = [{"producto_id": 1, "cantidad": 10}]
        categorias = [{"id": 1, "nombre": "Lacteos"}]
        proveedores = []
        
        resultado = _export_to_json(productos, inventarios, categorias, proveedores)
        data = json.loads(resultado)
        
        assert data[0]["proveedor"] == "Sin proveedor"

    def test_export_con_codigo_barras(self):
        productos = [
            {"id": 1, "sku": "SKU001", "nombre": "Leche", "precio_venta": 1.50,
             "precio_coste": 1.00, "unidad": "litro", "stock_maximo": 50,
             "categoria_id": 1, "proveedor_id": None, "descripcion": "Leche",
             "codigo_barras": "123456789", "tiempo_reposicion": 3}
        ]
        inventarios = [{"producto_id": 1, "cantidad": 10}]
        categorias = [{"id": 1, "nombre": "Lacteos"}]
        proveedores = []
        
        resultado = _export_to_json(productos, inventarios, categorias, proveedores)
        data = json.loads(resultado)
        
        assert data[0]["codigo_barras"] == "123456789"


class TestExportToExcel:
    """Tests para export Excel"""

    def test_export_devuelve_bytes(self):
        productos = [
            {"id": 1, "sku": "SKU001", "nombre": "Leche", "precio_venta": 1.50,
             "precio_coste": 1.00, "unidad": "litro", "stock_maximo": 50,
             "categoria_id": 1, "proveedor_id": 1, "descripcion": "Leche",
             "codigo_barras": None, "tiempo_reposicion": 3}
        ]
        inventarios = [{"producto_id": 1, "cantidad": 10}]
        categorias = [{"id": 1, "nombre": "Lácteos"}]
        proveedores = [{"id": 1, "nombre": "Proveedor A"}]
        
        resultado = _export_to_excel(productos, inventarios, categorias, proveedores)
        
        assert isinstance(resultado, bytes)
        assert len(resultado) > 0

    def test_export_lista_vacia_devuelve_bytes_vacios(self):
        resultado = _export_to_excel([], [], [], [])
        
        assert isinstance(resultado, bytes)
        assert len(resultado) == 0


class TestGetCategoriaEmoji:
    """Tests para get_categoria_emoji"""

    def test_lacteos_devuelve_emoji_correcto(self):
        assert get_categoria_emoji("Lácteos") == "🥛"

    def test_carnes_devuelve_emoji_correcto(self):
        assert get_categoria_emoji("Carnes") == "🥩"

    def test_categoria_desconocida_devuelve_caja(self):
        assert get_categoria_emoji("Cualquiera") == "📦"


class TestGetDescripcionDefault:
    """Tests para get_descripcion_default"""

    def test_leche_devuelve_descripcion_lacteos(self):
        desc = get_descripcion_default("Leche Entera")
        assert "frescura" in desc.lower() or "leche" in desc.lower()

    def test_yogur_devuelve_descripcion_lacteos(self):
        desc = get_descripcion_default("Yogur Natural")
        assert "frescura" in desc.lower() or "lácteo" in desc.lower()

    def test_producto_desconocido_devuelve_default(self):
        desc = get_descripcion_default("xyz123")
        assert len(desc) > 0


class TestValidarProducto:
    """Tests para validar_producto"""

    def test_producto_valido(self):
        data = {
            "sku": "SKU001",
            "nombre": "Leche Entera",
            "precio_venta": 1.50,
            "unidad": "litro",
            "stock_maximo": 50,
            "categoria_id": 1,
        }
        productos_existentes = []
        resultado = validar_producto(data, productos_existentes)
        assert resultado["valido"] is True
        assert len(resultado["errores"]) == 0

    def test_sku_obligatorio(self):
        data = {
            "nombre": "Leche Entera",
            "precio_venta": 1.50,
            "unidad": "litro",
            "stock_maximo": 50,
            "categoria_id": 1,
        }
        resultado = validar_producto(data, [])
        assert resultado["valido"] is False
        assert any("SKU" in e for e in resultado["errores"])

    def test_nombre_obligatorio(self):
        data = {
            "sku": "SKU001",
            "precio_venta": 1.50,
            "unidad": "litro",
            "stock_maximo": 50,
            "categoria_id": 1,
        }
        resultado = validar_producto(data, [])
        assert resultado["valido"] is False
        assert any("nombre" in e.lower() for e in resultado["errores"])

    def test_precio_cero_es_invalido(self):
        data = {
            "sku": "SKU001",
            "nombre": "Leche Entera",
            "precio_venta": 0,
            "unidad": "litro",
            "stock_maximo": 50,
            "categoria_id": 1,
        }
        resultado = validar_producto(data, [])
        assert resultado["valido"] is False
        assert any("precio" in e.lower() for e in resultado["errores"])

    def test_stock_maximo_cero_es_invalido(self):
        data = {
            "sku": "SKU001",
            "nombre": "Leche Entera",
            "precio_venta": 1.50,
            "unidad": "litro",
            "stock_maximo": 0,
            "categoria_id": 1,
        }
        resultado = validar_producto(data, [])
        assert resultado["valido"] is False
        assert any("stock" in e.lower() for e in resultado["errores"])

    def test_nombre_duplicado_es_invalido(self):
        data = {
            "sku": "SKU001",
            "nombre": "Leche Entera",
            "precio_venta": 1.50,
            "unidad": "litro",
            "stock_maximo": 50,
            "categoria_id": 1,
        }
        productos_existentes = [{"nombre": "leche entera"}]
        resultado = validar_producto(data, productos_existentes)
        assert resultado["valido"] is False
        assert any("existe" in e.lower() for e in resultado["errores"])


class TestFiltrarProductos:
    """Tests para filtrar_productos"""

    def test_sin_filtros_devuelve_todos(self):
        productos = [
            {"id": 1, "nombre": "Leche", "sku": "A"},
            {"id": 2, "nombre": "Yogur", "sku": "B"},
        ]
        resultado = filtrar_productos(productos)
        assert len(resultado) == 2

    def test_filtro_busqueda_por_nombre(self):
        productos = [
            {"id": 1, "nombre": "Leche Entera", "sku": "A"},
            {"id": 2, "nombre": "Yogur Natural", "sku": "B"},
            {"id": 3, "nombre": "Queso", "sku": "C"},
        ]
        resultado = filtrar_productos(productos, busqueda="leche")
        assert len(resultado) == 1
        assert resultado[0]["nombre"] == "Leche Entera"

    def test_filtro_busqueda_por_sku(self):
        productos = [
            {"id": 1, "nombre": "Leche Entera", "sku": "ABC123"},
            {"id": 2, "nombre": "Yogur Natural", "sku": "DEF456"},
        ]
        resultado = filtrar_productos(productos, busqueda="ABC123")
        assert len(resultado) == 1
        assert resultado[0]["nombre"] == "Leche Entera"

    def test_filtro_por_categoria(self):
        productos = [
            {"id": 1, "nombre": "Leche", "categoria_id": 1},
            {"id": 2, "nombre": "Yogur", "categoria_id": 2},
            {"id": 3, "nombre": "Queso", "categoria_id": 1},
        ]
        resultado = filtrar_productos(productos, categoria_id=1)
        assert len(resultado) == 2
        assert all(p["categoria_id"] == 1 for p in resultado)

    def test_busqueda_case_insensitive(self):
        productos = [
            {"id": 1, "nombre": "LECHE Entera", "sku": "A"},
        ]
        resultado = filtrar_productos(productos, busqueda="leche")
        assert len(resultado) == 1


class TestPrepararProductoData:
    """Tests para preparar_producto_data"""

    def test_prepara_data_basica(self):
        data = preparar_producto_data(
            sku="SKU001",
            nombre="Leche Entera",
            precio_venta=1.50,
            unidad="litro",
            stock_maximo=50,
            categoria_id=1,
        )
        
        assert data["sku"] == "SKU001"
        assert data["nombre"] == "Leche Entera"
        assert data["precio_venta"] == 1.50
        assert data["unidad"] == "litro"
        assert data["stock_maximo"] == 50
        assert data["categoria_id"] == 1

    def test_incluye_campos_opcionales(self):
        data = preparar_producto_data(
            sku="SKU001",
            nombre="Leche Entera",
            precio_venta=1.50,
            unidad="litro",
            stock_maximo=50,
            categoria_id=1,
            stock_minimo=5,
            proveedor_id=2,
            descripcion="Descripción custom",
        )
        
        assert data["stock_minimo"] == 5
        assert data["proveedor_id"] == 2
        assert data["descripcion"] == "Descripción custom"

    def test_proveedor_opcional_no_se_envia_si_cero(self):
        data = preparar_producto_data(
            sku="SKU001",
            nombre="Leche Entera",
            precio_venta=1.50,
            unidad="litro",
            stock_maximo=50,
            categoria_id=1,
            precio_coste=0,
        )
        
        assert "precio_coste" not in data