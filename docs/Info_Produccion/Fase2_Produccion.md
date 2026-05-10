# Fase 2 — Robustez y Operaciones

> **Objetivo:** Añadir mecanismos de backup, testing, rate limiting, logging profesional y CORS para hacer el sistema robusto y seguro en producción.

---

## Tabla de Contenidos

1. [Resumen](#resumen)
2. [Backup Automático de Base de Datos](#backup-automatico-de-base-de-datos)
3. [Tests de Integración](#tests-de-integracion)
4. [Rate Limiting](#rate-limiting)
5. [Logging con Rotación](#logging-con-rotacion)
6. [CORS Restringido](#cors-restringido)
7. [Script de Deploy (Windows)](#script-de-deploy-windows)
8. [Archivos Modificados/Creados](#archivos-modificadoscreados)

---

## Resumen

En esta fase se añadieron las herramientas necesarias para operar el sistema en producción de forma segura: backups automáticos con retención, tests de integración que validan toda la API, rate limiting para prevenir abusos, sistema de logs con rotación automática, y CORS restringido a orígenes explícitos.

---

## Backup Automático de Base de Datos

**Archivo:** `scripts/backup_db.py`

### Funcionalidad

Crea copias de seguridad de la base de datos SQLite con timestamp automático y mantiene una retención de los últimos 7 días.

### Proceso

1. **Crear backup:** Copia `data/markettalento.db` → `backups/markettalento_YYYYMMDD_HHMMSS.db`
2. **Limpiar antiguos:** Elimina backups con más de 7 días de antigüedad

### Uso manual

```bash
python scripts/backup_db.py
```

### Automatización con cron (Linux)

```bash
# Editar crontab
crontab -e

# Backup diario a las 3:00 AM
0 3 * * * cd /ruta/a/MarkeTTalento && python scripts/backup_db.py >> logs/backup.log 2>&1
```

### Restaurar desde backup

```bash
# 1. Detener la API
docker-compose down

# 2. Restaurar backup deseado
cp backups/markettalento_YYYYMMDD_HHMMSS.db data/markettalento.db

# 3. Reiniciar
docker-compose up -d
```

---

## Tests de Integración

**Archivo:** `tests/test_api_integration.py`

### Cobertura

Suite de **20 tests** que validan los endpoints principales de la API:

| Test | Endpoint | Qué valida |
|------|----------|------------|
| `test_salud` | `GET /salud` | Health check básico |
| `test_login_exitoso` | `POST /auth/login` | Autenticación correcta |
| `test_login_fallido` | `POST /auth/login` | Rechazo de credenciales inválidas |
| `test_get_me` | `GET /auth/me` | Info del usuario autenticado |
| `test_listar_productos` | `GET /productos` | Listado paginado |
| `test_obtener_producto_por_id` | `GET /productos/{id}` | Obtener producto existente |
| `test_obtener_producto_por_sku` | `GET /productos/sku/{sku}` | Búsqueda por SKU |
| `test_obtener_producto_por_barcode_no_existe` | `GET /productos/barcode/{codigo}` | Manejo de 404 |
| `test_obtener_inventario_producto` | `GET /inventario/{id}` | Stock de un producto |
| `test_historial_producto` | `GET /tickets/historial/{id}` | Historial de ventas |
| `test_resumen_inventario` | `GET /inventario/resumen` | Resumen global |
| `test_listar_categorias` | `GET /categorias` | Listado de categorías |
| `test_listar_tickets` | `GET /tickets` | Listado de tickets |
| `test_crear_ticket` | `POST /tickets` | Crear ticket con descuento de stock |
| `test_listar_referencias` | `GET /vision/referencias` | Galería de referencia |
| `test_analisis_abc` | `GET /predicciones/abc` | Análisis ABC |
| `test_prediccion_producto` | `GET /predicciones/producto/{id}` | Predicción ML |
| `test_dashboard_predictivo` | `GET /predicciones/dashboard` | Dashboard predictivo |
| `test_mapa_calor_ventas` | `GET /predicciones/mapa-calor` | Mapa de calor |
| `test_alertas_reposicion` | `GET /predicciones/alertas` | Alertas de stock bajo |

### Ejecución

```bash
# Todos los tests
pytest tests/test_api_integration.py -v

# Con cobertura
pytest tests/ --cov=src --cov=app --cov-report=html
```

**Estado:** 20/20 tests pasan ✅

---

## Rate Limiting

**Archivo:** `src/core/middleware/rate_limit.py`

### Funcionalidad

Middleware que limita el número de peticiones por IP para prevenir abusos y ataques de fuerza bruta.

### Configuración

| Parámetro | Valor | Descripción |
|-----------|-------|-------------|
| `RATE_LIMIT_WINDOW` | 60 segundos | Ventana de tiempo |
| `RATE_LIMIT_MAX_REQUESTS` | 120 | Peticiones máximas por ventana |

### Headers de respuesta

Cada respuesta incluye:
- `X-RateLimit-Limit: 120` — Límite total
- `X-RateLimit-Remaining: N` — Peticiones restantes

### Comportamiento

Si se excede el límite, la API responde:
```json
{
  "detail": "Demasiadas peticiones. Limite: 120 peticiones cada 60s"
}
```
Con código HTTP **429 Too Many Requests**.

### Detección de IP real

El middleware detecta correctamente la IP original incluso detrás de proxies:
- Lee header `X-Forwarded-For`
- Si hay múltiples IPs (proxy chain), toma la primera

### Uso en FastAPI

Registrado en `main.py`:
```python
from src.core.middleware.rate_limit import RateLimitMiddleware
app.add_middleware(RateLimitMiddleware)
```

---

## Logging con Rotación

**Archivo:** `src/core/logging.py`

### Características

- **Formato unificado:** `YYYY-MM-DD HH:MM:SS | NIVEL | modulo | mensaje`
- **Rotación automática:** 10 MB máximo por archivo, 5 backups
- **Salida dual:** Consola + archivo
- **Loggers especializados:** Un logger por módulo (`api`, `database`, `ml`, `vision`)

### Configuración

```python
MAX_LOG_SIZE_MB = 10      # Tamaño máximo antes de rotar
MAX_BACKUP_FILES = 5      # Número de backups a mantener
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
```

### Uso en código

```python
from src.core.logging import get_logger

logger = get_logger("markettalento.api")
logger.info("Operación completada")
logger.error("Error al procesar ticket", exc_info=True)
```

### Archivos generados

```
logs/
  markettalento.log          # Log actual
  markettalento.log.1        # Backup más reciente
  markettalento.log.2
  ...
  markettalento.log.5        # Backup más antiguo
```

**Nota:** Los backups antiguos se pierden tras 5 rotaciones. Para retención más larga, usar `TimedRotatingFileHandler`.

---

## CORS Restringido

**Archivo:** Configurado en `main.py`

### Funcionalidad

El CORS (Cross-Origin Resource Sharing) está configurado para solo permitir peticiones desde orígenes explícitamente autorizados, evitando que sitios web de terceros consuman la API.

### Configuración por defecto

```python
origins = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
]

# Se puede extender con variable de entorno:
# CORS_ORIGINS=http://localhost:8501,https://midominio.com
```

### En producción

```env
CORS_ORIGINS=https://tudominio.com,https://app.tudominio.com
```

---

## Script de Deploy (Windows)

**Archivo:** `deploy.bat`

Automatiza el despliegue manual en Windows:

1. Crea directorios necesarios (`data`, `logs`, `backups`)
2. Instala/actualiza dependencias
3. Crea usuarios por defecto
4. Inicia la API en segundo plano
5. Inicia el dashboard Streamlit

### Uso

```cmd
deploy.bat
```

### Requisitos

- Python 3.11+ instalado
- Variables de entorno configuradas o `.env` presente

---

## Archivos Modificados/Creados

| Archivo | Descripción |
|---------|-------------|
| `scripts/backup_db.py` | Nuevo — Backup automático con retención de 7 días (SQLite + PostgreSQL)
| `tests/test_api_integration.py` | Nuevo — 20 tests de integración |
| `src/core/middleware/rate_limit.py` | Nuevo — Rate limiting por IP |
| `src/core/logging.py` | Nuevo — Sistema de logging con rotación |
| `src/core/middleware/__init__.py` | Nuevo — Paquete de middlewares |
| `deploy.bat` | Nuevo — Script de deploy para Windows |
| `main.py` | Modificado — Registro de middlewares y CORS |
| `requirements.txt` | Modificado — Añadido `pytest`, `httpx` |

---

## Checklist Fase 2

- [x] Backup automático implementado (SQLite + PostgreSQL)
- [x] Tests de integración creados (20/20 pasan)
- [x] Rate limiting configurado (120 req/min)
- [x] Logging con rotación automática (10MB / 5 backups)
- [x] CORS restringido a orígenes explícitos
- [x] Script de deploy para Windows
- [x] Documentación de troubleshooting
