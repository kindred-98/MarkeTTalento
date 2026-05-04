# Tests del Proyecto

## Estadísticas de Tests

- **Tests de Validaciones**: 27 tests
- **Tests de Lógica de Inventario**: 27 tests
- **Tests de API**: 24 tests (nuevos)
- **Tests existentes (ventas, productos, helpers)**: 67 tests
- **TOTAL**: **145 tests automatizados** ✅

## Ejecutar Tests

### Todos los tests
```bash
python run_tests.py
```

### Con cobertura
```bash
python run_tests.py --cov
```

### Por categoría

#### Validaciones
```bash
python -m pytest tests/test_validators.py -v
```

#### Lógica de Inventario
```bash
python -m pytest tests/test_inventario_logic.py -v
```

#### API (HTTP)
```bash
python -m pytest tests/test_api.py -v
```

#### Todos los tests de inventario
```bash
python -m pytest tests/test_validators.py tests/test_inventario_logic.py tests/test_api.py -v
```

### Un test específico
```bash
python -m pytest tests/test_api.py::TestApiPost::test_post_exitoso -v
```

## Estructura de Tests

### `test_validators.py` - Validaciones (27 tests)
- **TestValidarSKU**: 7 tests
- **TestValidarEmailProveedor**: 4 tests
- **TestValidarProveedorNuevo**: 5 tests
- **TestCalcularMargenGanancia**: 5 tests
- **TestValidarStock**: 6 tests

### `test_inventario_logic.py` - Lógica de Inventario (27 tests)
- **TestCalcularEstadoStock**: 7 tests (Agotado, Crítico, Bajo, Saludable)
- **TestGetEstadoInfo**: 2 tests
- **TestFiltrarPorEstado**: 4 tests
- **TestOrdenarInventario**: 5 tests
- **TestCalcularNuevoStock**: 4 tests
- **TestPrepararDatosInventario**: 5 tests

### `test_api.py` - API HTTP (24 tests) ⭐ NUEVO
- **TestApiGet**: 5 tests (exitoso, 404, timeout, error conexión, sin caché)
- **TestApiPost**: 5 tests (exitoso, 400, 500, timeout, excepción)
- **TestApiPut**: 4 tests (exitoso, 404, error mensaje, timeout)
- **TestApiDelete**: 3 tests (exitoso, 404, excepción)
- **TestCacheInvalidation**: 1 test
- **TestVerificarApi**: 3 tests (disponible, no disponible, excepción)
- **TestEsperarApi**: 3 tests (exitoso, falla, eventual éxito)

### Tests existentes (67 tests)
- `test_venta_logic.py` - Lógica de ventas
- `test_producto_logic.py` - Lógica de productos
- `test_helpers.py` - Utilidades

## Cobertura de API

Los tests de API cubren:
- ✅ **Éxitos**: 200, 201, 204
- ✅ **Errores cliente**: 400, 404
- ✅ **Errores servidor**: 500
- ✅ **Errores de red**: Timeout, ConnectionError
- ✅ **Excepciones**: Errores inesperados
- ✅ **Caché**: Invalidación correcta
- ✅ **Verificación**: API disponible/no disponible
- ✅ **Reintentos**: Esperar API con múltiples intentos

## Técnicas de Testing

### Mocking
Usamos `unittest.mock` para simular:
- Peticiones HTTP sin hacer llamadas reales
- Respuestas de la API con códigos específicos
- Excepciones de red (timeout, conexión)
- Funciones de caché

### Ejemplo de Test con Mock
```python
@patch('app.utils.api.requests.get')
def test_get_exitoso(self, mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1}]
    mock_get.return_value = mock_response
    
    resultado = api_get("/api/v1/productos")
    
    assert resultado == [{"id": 1}]
```

## Agregar Nuevos Tests

1. Crear archivo `test_nombre_modulo.py` en esta carpeta
2. Importar las funciones a testear
3. Usar `@patch` para mockear dependencias externas
4. Nombrar métodos con prefijo `test_`
5. Usar asserts para verificar resultados

## Reporte de Cobertura

Para ver cobertura detallada:
```bash
# Cobertura general
python -m pytest tests/ --cov=app --cov-report=term

# Reporte HTML
python -m pytest tests/ --cov=app --cov-report=html
# Abrir: htmlcov/index.html

# Cobertura por módulo
python -m pytest tests/test_api.py --cov=app.utils.api --cov-report=term-missing
```
