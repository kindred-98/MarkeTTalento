"""
Manejo de Errores Global para la API
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger("markettalento.api.errors")


class APIException(Exception):
    """Excepción base para errores de la API."""
    def __init__(self, message: str, status_code: int = 400, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(APIException):
    """Recurso no encontrado."""
    def __init__(self, resource: str, resource_id=None):
        message = f"{resource} no encontrado"
        if resource_id:
            message += f" (ID: {resource_id})"
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class ValidationException(APIException):
    """Error de validación."""
    def __init__(self, message: str, field: str = None):
        details = {"field": field} if field else {}
        super().__init__(message, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, details=details)


class ConflictException(APIException):
    """Conflicto (ej: recurso duplicado)."""
    def __init__(self, message: str):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


def setup_error_handlers(app):
    """Configura los manejadores de errores para la aplicación FastAPI."""
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        """Maneja excepciones personalizadas de la API."""
        logger.warning(f"APIException: {exc.message} - Path: {request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "details": exc.details,
                "status_code": exc.status_code
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Maneja errores de validación de Pydantic."""
        logger.warning(f"ValidationError: {exc.errors()} - Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "message": "Error de validación en los datos enviados",
                "details": exc.errors(),
                "status_code": 422
            }
        )
    
    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        """Maneja errores de base de datos."""
        logger.error(f"DatabaseError: {str(exc)} - Path: {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Error en la base de datos",
                "details": {"error": str(exc)},
                "status_code": 500
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Maneja cualquier otra excepción no capturada."""
        logger.error(f"UnhandledException: {str(exc)} - Path: {request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Error interno del servidor",
                "details": {"error": str(exc)},
                "status_code": 500
            }
        )
    
    logger.info("Manejadores de errores configurados")
