"""
Utilidades para comunicación con la API
"""
import requests
from typing import Any, Dict, List, Optional
from app.config import API_URL


def api_get(endpoint: str, timeout: int = 5) -> List[Dict[str, Any]]:
    """Realiza una petición GET a la API."""
    try:
        r = requests.get(f"{API_URL}{endpoint}", timeout=timeout)
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []


def api_post(endpoint: str, data: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Realiza una petición POST a la API."""
    try:
        r = requests.post(f"{API_URL}{endpoint}", json=data, timeout=timeout)
        if r.status_code in [200, 201]:
            return r.json()
        else:
            print(f"API Error: {r.status_code} - {r.text}")
            return None
    except Exception as e:
        print(f"API Exception: {e}")
        return None


def api_put(endpoint: str, data: Dict[str, Any], timeout: int = 5) -> Optional[Dict[str, Any]]:
    """Realiza una petición PUT a la API."""
    try:
        r = requests.put(f"{API_URL}{endpoint}", json=data, timeout=timeout)
        if r.status_code in [200, 201]:
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
    """Realiza una petición DELETE a la API."""
    try:
        r = requests.delete(f"{API_URL}{endpoint}", timeout=timeout)
        return r.status_code in [200, 204]
    except Exception:
        return False


def verificar_api() -> bool:
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
