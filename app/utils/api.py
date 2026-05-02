"""
Utilidades para comunicación con la API
"""
import streamlit as st
import requests
from typing import Any, Dict, List, Optional
from functools import wraps
from app.config import API_URL


# Cache para peticiones GET (10 segundos de TTL)
@st.cache_data(ttl=10, show_spinner=False)
def _cached_api_get(endpoint: str, timeout: int = 5) -> tuple:
    """Versión cacheada de petición GET - retorna tupla (status, data)."""
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=timeout)
        if r.status_code == 200:
            return ("success", r.json())
        return ("error", [])
    except Exception as e:
        return ("exception", [])


def api_get(endpoint: str, timeout: int = 5, use_cache: bool = True) -> List[Dict[str, Any]]:
    """Realiza una petición GET a la API con caching opcional.
    
    Args:
        endpoint: Endpoint de la API
        timeout: Tiempo de espera en segundos
        use_cache: Si True, usa cache (ttl=300s). Si False, fuerza petición fresca.
    """
    if use_cache:
        status, data = _cached_api_get(endpoint, timeout)
        return data
    else:
        # Petición sin cache
        try:
            r = requests.get(f"{API_URL}{endpoint}", timeout=timeout)
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []


def api_post(endpoint: str, data: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Realiza una petición POST a la API (no cacheada por ser mutación)."""
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=timeout)
        if r.status_code in [200, 201]:
            # Invalidar cache relevante después de modificación
            _invalidate_cache_for_endpoint(endpoint)
            return r.json()
        else:
            print(f"API Error: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"API Exception: {e}")
        return None


def api_put(endpoint: str, data: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Realiza una petición PUT a la API (no cacheada por ser mutación)."""
    try:
        r = requests.put(f"{API_URL}{endpoint}", json=data, timeout=timeout)
        if r.status_code in [200, 201]:
            # Invalidar cache relevante después de modificación
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


def api_delete(endpoint: str, timeout: int = 5) -> bool:
    """Realiza una petición DELETE a la API (no cacheada por ser mutación)."""
    try:
        r = requests.delete(f"{API_URL}{endpoint}", timeout=timeout)
        if r.status_code in [200, 204]:
            # Invalidar cache relevante después de modificación
            _invalidate_cache_for_endpoint(endpoint)
            return True
        return False
    except Exception:
        return False


def _invalidate_cache_for_endpoint(endpoint: str):
    """Invalida cache para endpoints relacionados tras modificación."""
    # Limpiar cache de datos afectados por mutaciones
    # Esto fuerza recarga de datos en próximas peticiones GET
    _cached_api_get.clear()


# Cache para verificación de API (30 segundos)
@st.cache_data(ttl=30, show_spinner=False)
def _cached_verificar_api() -> bool:
    """Versión cacheada de verificación de API."""
    try:
        r = requests.get(f"{API_URL}/api/v1/salud", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def verificar_api(use_cache: bool = False) -> bool:
    """Verifica si la API está disponible.
    
    Args:
        use_cache: Si True, usa cache de 30s para reducir peticiones.
    """
    if use_cache:
        return _cached_verificar_api()
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
