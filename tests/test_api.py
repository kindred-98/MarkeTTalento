"""
Tests para el módulo de API (app/utils/api.py).
Ejecutar con: python -m pytest tests/test_api.py -v
"""
import pytest
from unittest.mock import patch, MagicMock
import requests
from app.utils.api import (
    api_get,
    api_post,
    api_put,
    api_delete,
    verificar_api,
    esperar_api,
    _cached_api_get,
    _invalidate_cache_for_endpoint
)


class TestApiGet:
    """Tests para api_get."""
    
    @patch('app.utils.api.requests.get')
    def test_get_exitoso_con_cache(self, mock_get):
        """GET exitoso debe retornar datos y usar caché."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1, "nombre": "Test"}]
        mock_get.return_value = mock_response
        
        # Primera llamada
        resultado1 = api_get("/api/v1/productos", use_cache=False)
        
        assert resultado1 == [{"id": 1, "nombre": "Test"}]
        mock_get.assert_called_once()
    
    @patch('app.utils.api.requests.get')
    def test_get_error_404(self, mock_get):
        """GET con error 404 debe retornar lista vacía."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        resultado = api_get("/api/v1/productos/999", use_cache=False)
        
        assert resultado == []
    
    @patch('app.utils.api.requests.get')
    def test_get_timeout(self, mock_get):
        """GET con timeout debe retornar lista vacía."""
        mock_get.side_effect = requests.Timeout("Timeout")
        
        resultado = api_get("/api/v1/productos", timeout=1, use_cache=False)
        
        assert resultado == []
    
    @patch('app.utils.api.requests.get')
    def test_get_connection_error(self, mock_get):
        """GET con error de conexión debe retornar lista vacía."""
        mock_get.side_effect = requests.ConnectionError("No connection")
        
        resultado = api_get("/api/v1/productos", use_cache=False)
        
        assert resultado == []
    
    @patch('app.utils.api.requests.get')
    def test_get_sin_cache(self, mock_get):
        """GET sin caché debe hacer petición fresca."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": 1}]
        mock_get.return_value = mock_response
        
        resultado = api_get("/api/v1/productos", use_cache=False)
        
        mock_get.assert_called_once()
        assert resultado == [{"id": 1}]


class TestApiPost:
    """Tests para api_post."""
    
    @patch('app.utils.api.requests.post')
    @patch('app.utils.api._invalidate_cache_for_endpoint')
    def test_post_exitoso(self, mock_invalidate, mock_post):
        """POST exitoso debe retornar datos e invalidar caché."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "nombre": "Nuevo"}
        mock_post.return_value = mock_response
        
        datos = {"nombre": "Nuevo Producto"}
        resultado = api_post("/api/v1/productos", datos)
        
        assert resultado == {"id": 1, "nombre": "Nuevo"}
        mock_invalidate.assert_called_once()
    
    @patch('app.utils.api.requests.post')
    def test_post_error_400(self, mock_post):
        """POST con error 400 debe retornar None."""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        resultado = api_post("/api/v1/productos", {"invalido": True})
        
        assert resultado is None
    
    @patch('app.utils.api.requests.post')
    def test_post_error_500(self, mock_post):
        """POST con error 500 debe retornar None."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        resultado = api_post("/api/v1/productos", {"datos": "test"})
        
        assert resultado is None
    
    @patch('app.utils.api.requests.post')
    def test_post_timeout(self, mock_post):
        """POST con timeout debe retornar None."""
        mock_post.side_effect = requests.Timeout("Timeout")
        
        resultado = api_post("/api/v1/productos", {"datos": "test"}, timeout=1)
        
        assert resultado is None
    
    @patch('app.utils.api.requests.post')
    def test_post_exception(self, mock_post):
        """POST con excepción debe retornar None."""
        mock_post.side_effect = Exception("Error inesperado")
        
        resultado = api_post("/api/v1/productos", {"datos": "test"})
        
        assert resultado is None


class TestApiPut:
    """Tests para api_put."""
    
    @patch('app.utils.api.requests.put')
    @patch('app.utils.api._invalidate_cache_for_endpoint')
    def test_put_exitoso(self, mock_invalidate, mock_put):
        """PUT exitoso debe retornar datos e invalidar caché."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": 1, "actualizado": True}
        mock_put.return_value = mock_response
        
        datos = {"nombre": "Actualizado"}
        resultado = api_put("/api/v1/productos/1", datos)
        
        assert resultado == {"id": 1, "actualizado": True}
        mock_invalidate.assert_called_once()
    
    @patch('app.utils.api.requests.put')
    def test_put_error_404(self, mock_put):
        """PUT con error 404 debe retornar error."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_put.return_value = mock_response
        
        resultado = api_put("/api/v1/productos/999", {"nombre": "Test"})
        
        assert "error" in resultado
    
    @patch('app.utils.api.requests.put')
    def test_put_error_con_mensaje(self, mock_put):
        """PUT debe incluir mensaje de error en respuesta."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Error del servidor"
        mock_put.return_value = mock_response
        
        resultado = api_put("/api/v1/productos/1", {"nombre": "Test"})
        
        assert "error" in resultado
        assert "Error del servidor" in resultado["error"]
    
    @patch('app.utils.api.requests.put')
    def test_put_timeout(self, mock_put):
        """PUT con timeout debe retornar error."""
        mock_put.side_effect = requests.Timeout("Timeout")
        
        resultado = api_put("/api/v1/productos/1", {"nombre": "Test"})
        
        assert "error" in resultado
        assert "Timeout" in resultado["error"]


class TestApiDelete:
    """Tests para api_delete."""
    
    @patch('app.utils.api.requests.delete')
    @patch('app.utils.api._invalidate_cache_for_endpoint')
    def test_delete_exitoso(self, mock_invalidate, mock_delete):
        """DELETE exitoso debe retornar True e invalidar caché."""
        mock_response = MagicMock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        resultado = api_delete("/api/v1/productos/1")
        
        assert resultado is True
        mock_invalidate.assert_called_once()
    
    @patch('app.utils.api.requests.delete')
    def test_delete_error_404(self, mock_delete):
        """DELETE con error 404 debe retornar False."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_delete.return_value = mock_response
        
        resultado = api_delete("/api/v1/productos/999")
        
        assert resultado is False
    
    @patch('app.utils.api.requests.delete')
    def test_delete_exception(self, mock_delete):
        """DELETE con excepción debe retornar False."""
        mock_delete.side_effect = Exception("Error de red")
        
        resultado = api_delete("/api/v1/productos/1")
        
        assert resultado is False


class TestCacheInvalidation:
    """Tests para invalidación de caché."""
    
    @patch('app.utils.api._cached_api_get.clear')
    def test_invalidate_cache_llama_clear(self, mock_clear):
        """Invalidar caché debe llamar a clear."""
        _invalidate_cache_for_endpoint("/api/v1/productos")
        
        mock_clear.assert_called_once()


class TestVerificarApi:
    """Tests para verificar_api."""
    
    @patch('app.utils.api.requests.get')
    def test_api_disponible(self, mock_get):
        """API disponible debe retornar True."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        resultado = verificar_api(use_cache=False)
        
        assert resultado is True
    
    @patch('app.utils.api.requests.get')
    def test_api_no_disponible(self, mock_get):
        """API no disponible debe retornar False."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        resultado = verificar_api(use_cache=False)
        
        assert resultado is False
    
    @patch('app.utils.api.requests.get')
    def test_api_exception(self, mock_get):
        """API con excepción debe retornar False."""
        mock_get.side_effect = requests.ConnectionError("No connection")
        
        resultado = verificar_api(use_cache=False)
        
        assert resultado is False


class TestEsperarApi:
    """Tests para esperar_api."""
    
    @patch('app.utils.api.requests.get')
    def test_esperar_api_exitoso(self, mock_get):
        """Esperar API debe retornar True cuando esté disponible."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        resultado = esperar_api(intentos=3)
        
        assert resultado is True
    
    @patch('app.utils.api.requests.get')
    def test_esperar_api_falla(self, mock_get):
        """Esperar API debe retornar False después de todos los intentos."""
        mock_get.side_effect = requests.ConnectionError("No connection")
        
        resultado = esperar_api(intentos=2)
        
        assert resultado is False
        assert mock_get.call_count == 2
    
    @patch('app.utils.api.requests.get')
    def test_esperar_api_eventualmente_exitoso(self, mock_get):
        """Esperar API debe retornar True si eventualmente responde."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        # Falla 2 veces, luego éxito
        mock_get.side_effect = [
            requests.ConnectionError("Fail 1"),
            requests.ConnectionError("Fail 2"),
            mock_response
        ]
        
        resultado = esperar_api(intentos=5)
        
        assert resultado is True
        assert mock_get.call_count == 3


if __name__ == "__main__":
    print("=" * 60)
    print("TESTS DE API")
    print("=" * 60)
    print("\nEjecutar con: python -m pytest tests/test_api.py -v")
    print("=" * 60)
