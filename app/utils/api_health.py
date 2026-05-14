"""
Comprobación de disponibilidad de la API FastAPI (HTTP real).
El dashboard usa SQLite directo; Inspector, predicciones vía HTTP, etc. dependen de la API.
"""
from __future__ import annotations

import time
from typing import Any

import requests

from app.config import API_URL

SALUD_PATH = "/api/v1/salud"
DEFAULT_INTERVAL_S = 25.0


def salud_url() -> str:
    return f"{API_URL.rstrip('/')}{SALUD_PATH}"


def ping_api_salud(timeout: float = 2.5) -> tuple[bool, str | None, dict[str, Any] | None, int | None]:
    """
    Llama al health check público de la API.

    Returns:
        (ok, mensaje_error_o_None, json_body_o_None, latencia_ms_o_None)
    """
    url = salud_url()
    t0 = time.perf_counter()
    try:
        r = requests.get(url, timeout=timeout)
        ms = int((time.perf_counter() - t0) * 1000)
        body: dict[str, Any] | None = None
        try:
            if r.content:
                body = r.json()
        except ValueError:
            body = None
        if r.status_code == 200:
            return True, None, body, ms
        return False, f"HTTP {r.status_code}", body, ms
    except requests.exceptions.Timeout:
        return False, "Tiempo de espera agotado", None, None
    except requests.exceptions.ConnectionError:
        return False, "Sin conexión (¿API en marcha?)", None, None
    except Exception as e:
        return False, str(e), None, None


def refresh_api_health_cache(force: bool = False, interval_s: float = DEFAULT_INTERVAL_S) -> dict[str, Any]:
    """
    Actualiza `st.session_state['_api_health_cache']` si toca o si `force`.

    Returns:
        dict con keys: ok, error, checked_at, latency_ms, url
    """
    import streamlit as st

    now = time.time()
    cache = st.session_state.get("_api_health_cache")
    if cache is None:
        cache = {"ok": False, "error": None, "checked_at": 0.0, "latency_ms": None}
        st.session_state["_api_health_cache"] = cache

    if not force and (now - cache.get("checked_at", 0)) < interval_s:
        cache["url"] = salud_url()
        return cache

    ok, err, _body, ms = ping_api_salud()
    cache["ok"] = ok
    cache["error"] = err
    cache["checked_at"] = now
    cache["latency_ms"] = ms
    cache["url"] = salud_url()
    st.session_state["api_conectada"] = ok
    return cache
