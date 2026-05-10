"""
Utilidades para comunicación con la API
Incluye token JWT de autenticación en cada petición.
"""
import streamlit as st
import requests
from typing import Any, Dict, List, Optional
from functools import wraps
from app.config import API_URL


def _get_auth_headers() -> dict:
    """Obtiene el header Authorization si hay token en session_state."""
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# Cache para peticiones GET (10 segundos de TTL)
@st.cache_data(ttl=10, show_spinner=False)
def _cached_api_get(endpoint: str, timeout: int = 5) -> tuple:
    """Versión cacheada de petición GET - retorna tupla (status, data)."""
    try:
        # Nota: no podemos acceder a session_state desde cache, 
        # asi que el cache no usa auth. Para datos publicos está OK.
        r = requests.get(f"{API_URL}{endpoint}", timeout=timeout)
        if r.status_code == 200:
            return ("success", r.json())
        return ("error", [])
    except Exception as e:
        return ("exception", [])


def api_get(endpoint: str, timeout: int = 5, use_cache: bool = True, authenticated: bool = True) -> List[Dict[str, Any]]:
    """Realiza una petición GET a la API con caching opcional.
    
    Args:
        endpoint: Endpoint de la API
        timeout: Tiempo de espera en segundos
        use_cache: Si True, usa cache (ttl=300s). Si False, fuerza petición fresca.
        authenticated: Si True, incluye token JWT.
    """
    headers = _get_auth_headers() if authenticated else {}
    
    if use_cache and not authenticated:
        status, data = _cached_api_get(endpoint, timeout)
        return data
    else:
        # Petición sin cache (o autenticada)
        try:
            r = requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=timeout)
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []


def api_post(endpoint: str, data: Dict[str, Any], timeout: int = 5, authenticated: bool = True) -> Optional[Dict[str, Any]]:
    """Realiza una petición POST a la API (no cacheada por ser mutación)."""
    headers = _get_auth_headers() if authenticated else {}
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=data, headers=headers, timeout=timeout)
        if r.status_code in [200, 201]:
            _invalidate_cache_for_endpoint(endpoint)
            return r.json()
        else:
            print(f"API Error: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"API Exception: {e}")
        return None


def api_post_form(endpoint: str, data: dict, files: dict = None, timeout: int = 30, authenticated: bool = True) -> Optional[Dict[str, Any]]:
    """Realiza una petición POST con FormData (para uploads de archivos)."""
    headers = _get_auth_headers() if authenticated else {}
    # No incluir Content-Type para multipart, requests lo pone solo
    if headers and "Authorization" in headers:
        headers = {"Authorization": headers["Authorization"]}
    else:
        headers = {}
    try:
        r = requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=headers, timeout=timeout)
        if r.status_code in [200, 201]:
            return r.json()
        else:
            print(f"API Error: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"API Exception: {e}")
        return None


def api_put(endpoint: str, data: Dict[str, Any], timeout: int = 5, authenticated: bool = True) -> Optional[Dict[str, Any]]:
    """Realiza una petición PUT a la API (no cacheada por ser mutación)."""
    headers = _get_auth_headers() if authenticated else {}
    try:
        r = requests.put(f"{API_URL}{endpoint}", json=data, headers=headers, timeout=timeout)
        if r.status_code in [200, 201]:
            _invalidate_cache_for_endpoint(endpoint)
            return r.json()
        else:
            error_msg = f"API Error: {r.status_code} - {r.text}"
            print(error_msg)
            return {"error": error_msg}
    except Exception as e:
        error_msg = f"API Exception: {e}"
        print(error_msg)
        return {"error": error_msg}


def api_delete(endpoint: str, timeout: int = 5, authenticated: bool = True) -> bool:
    """Realiza una petición DELETE a la API (no cacheada por ser mutación)."""
    headers = _get_auth_headers() if authenticated else {}
    try:
        r = requests.delete(f"{API_URL}{endpoint}", headers=headers, timeout=timeout)
        if r.status_code in [200, 204]:
            _invalidate_cache_for_endpoint(endpoint)
            return True
        return False
    except Exception:
        return False


def _invalidate_cache_for_endpoint(endpoint: str):
    """Invalida cache para endpoints relacionados tras modificación."""
    _cached_api_get.clear()


def verificar_api(use_cache: bool = False) -> bool:
    """Verifica si la API está disponible."""
    try:
        r = requests.get(f"{API_URL}/api/v1/salud", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def esperar_api(intentos: int = 15) -> bool:
    """Espera a que la API esté disponible."""
    import time
    for _ in range(intentos):
        try:
            r = requests.get(f"{API_URL}/api/v1/salud", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False
