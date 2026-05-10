"""
Rate limiting middleware para FastAPI.
Limita peticiones por IP en ventanas de tiempo.
"""
import time
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Configuracion
RATE_LIMIT_WINDOW = 60  # segundos
RATE_LIMIT_MAX_REQUESTS = 120  # peticiones por ventana

# Almacenamiento en memoria: {ip: [(timestamp1), (timestamp2), ...]}
_request_log: Dict[str, list] = {}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware que limita peticiones por IP."""

    async def dispatch(self, request: Request, call_next):
        # Obtener IP real (considerando proxies)
        client_ip = request.headers.get("x-forwarded-for", request.client.host)
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()

        now = time.time()

        # Limpiar entradas antiguas y contar peticiones recientes
        if client_ip in _request_log:
            _request_log[client_ip] = [
                ts for ts in _request_log[client_ip]
                if now - ts < RATE_LIMIT_WINDOW
            ]
        else:
            _request_log[client_ip] = []

        # Verificar limite
        if len(_request_log[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail=f"Demasiadas peticiones. Limite: {RATE_LIMIT_MAX_REQUESTS} peticiones cada {RATE_LIMIT_WINDOW}s"
            )

        # Registrar peticion actual
        _request_log[client_ip].append(now)

        # Continuar
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_MAX_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(max(0, RATE_LIMIT_MAX_REQUESTS - len(_request_log[client_ip])))
        return response
