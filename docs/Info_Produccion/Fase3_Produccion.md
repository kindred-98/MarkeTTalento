# Fase 3 — Dashboard, Monitoreo y CI/CD

> **Objetivo:** Añadir login al dashboard Streamlit, health check avanzado, métricas Prometheus y pipeline de CI/CD para completar el sistema listo para producción.

---

## Tabla de Contenidos

1. [Resumen](#resumen)
2. [Login/Logout en Streamlit](#loginlogout-en-streamlit)
3. [Health Check Avanzado](#health-check-avanzado)
4. [Métricas Prometheus](#metricas-prometheus)
5. [CI/CD con GitHub Actions](#cicd-con-github-actions)
6. [Archivos Modificados/Creados](#archivos-modificadoscreados)

---

## Resumen

En esta fase se cerró el ciclo de producción: el dashboard ahora requiere autenticación JWT, la API expone endpoints de monitoreo (health + métricas), y un pipeline de GitHub Actions automatiza tests y build de Docker en cada push.

---

## Login/Logout en Streamlit

### Flujo de autenticación

El dashboard ahora tiene un flujo de login completo antes de mostrar cualquier funcionalidad:

```
Usuario abre Streamlit
        |
        v
  ¿auth_token en session_state?
        |
   NO --+--> Pantalla de login
        |      |
        |      v
        |   Introduce credenciales
        |      |
        |      v
        |   POST /api/v1/auth/login
        |      |
        |      v
        |   Guarda token en session_state
        |   Recarga la página
        |
   SI --+--> Muestra app completa
              |
              +-- Sidebar con info de usuario
              +-- Botón "Cerrar Sesión"
```

### Pantalla de login

**Archivo:** `app/views/login.py`

- Diseño centrado con gradiente cian/violeta
- Campos: usuario y contraseña
- Mensajes de error específicos (401, connection error, etc.)
- Spinner durante autenticación
- Hint con usuario por defecto (`admin` / `admin123`)

### Sidebar con info de usuario

**Archivo:** `app/components/sidebar.py`

Muestra:
- 👤 Nombre de usuario logueado
- 🛡️ Rol (`admin` o `cajero`)
- 🔗 Enlace a API Docs (abre en nueva pestaña)
- 🚪 Botón **"Cerrar Sesión"** — Limpia `session_state` y recarga

### Integración con API

**Archivo:** `app/utils/api.py`

Todas las funciones de petición a la API (`api_get`, `api_post`, etc.) ahora incluyen automáticamente:
```python
headers = {"Authorization": f"Bearer {st.session_state['auth_token']}"}
```

Si la API responde 401 (token expirado), el frontend limpia la sesión y redirige al login.

### Routing condicional

**Archivo:** `app/main.py`

```python
# Verificar autenticación
if not st.session_state.get("auth_token"):
    login.render()
    return

# Usuario autenticado
menu = render_sidebar()
# ... router de páginas
```

---

## Health Check Avanzado

**Endpoint:** `GET /api/v1/health`

### Respuesta

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00+00:00",
  "checks": {
    "api": {
      "status": "ok",
      "response_time_ms": 0
    },
    "database": {
      "status": "ok",
      "response_time_ms": 2.34
    },
    "embeddings": {
      "status": "ok"
    },
    "yolo_model": {
      "status": "ok"
    }
  }
}
```

### Checks realizados

| Check | Qué verifica | Estado error |
|-------|--------------|--------------|
| `api` | El propio endpoint responde | Nunca falla |
| `database` | `SELECT 1` en SQLite + tiempo de respuesta | `error` + mensaje |
| `embeddings` | Existe `data/embeddings_productos.pkl` | `missing` |
| `yolo_model` | Existe `yolov8n.pt` | `missing` |

### Estados globales

- `healthy` — Todos los checks son `ok`
- `degraded` — Algún check falla

### Uso

```bash
curl http://localhost:8002/api/v1/health
```

Ideal para:
- Balanceadores de carga (solo rutear si `healthy`)
- Monitoreo con UptimeRobot/Pingdom
- Scripts de deploy que esperan a que todo esté listo

---

## Métricas Prometheus

**Endpoint:** `GET /api/v1/metrics`

### Métricas expuestas

```
# HELP markettalento_productos_total Total de productos activos
# TYPE markettalento_productos_total gauge
markettalento_productos_total 21

# HELP markettalento_tickets_total Total de tickets
# TYPE markettalento_tickets_total gauge
markettalento_tickets_total 199

# HELP markettalento_usuarios_total Total de usuarios
# TYPE markettalento_usuarios_total gauge
markettalento_usuarios_total 10

# HELP markettalento_stock_total Unidades totales en inventario
# TYPE markettalento_stock_total gauge
markettalento_stock_total 532
```

### Integración con Prometheus + Grafana

1. **Configurar scrape en `prometheus.yml`:**

```yaml
scrape_configs:
  - job_name: 'markettalento'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/api/v1/metrics'
    scrape_interval: 30s
```

2. **Crear dashboard en Grafana:**
   - Panel de productos activos
   - Gráfico de tickets totales
   - Alerta cuando stock_total < umbral
   - Usuarios registrados

---

## CI/CD con GitHub Actions

**Archivo:** `.github/workflows/ci.yml`

### Pipeline

```
Push/PR a main o master
        |
        v
   +----+----+
   |  TEST   |  <-- Corre en paralelo Python 3.11 y 3.12
   +----+----+
        |
        v
   +----+----+
   |  BUILD  |  <-- Solo si TEST pasa y es push a main
   |  DOCKER |
   +---------+
```

### Job: `test`

| Paso | Descripción |
|------|-------------|
| Checkout | Clona el repositorio |
| Setup Python | Python 3.11 y 3.12 en matriz |
| Instalar dependencias | `pip install -r requirements.txt` |
| Crear directorios | `data`, `logs`, `backups` |
| Ejecutar tests | `pytest tests -v --tb=short` |
| Cobertura | `pytest --cov=src --cov=app --cov-report=xml` |
| Subir a Codecov | Solo en Python 3.12 |

### Job: `build-docker`

| Condición | `needs: test` + push a `main`/`master` |
|-----------|----------------------------------------|
| Setup Buildx | Docker Buildx para builds eficientes |
| Build imagen | `docker build -t markettalento:latest .` |
| Verificar | `docker images | grep markettalento` |

### Extensión futura: Push a registro

Para publicar la imagen en Docker Hub o GHCR, añadir:

```yaml
- name: Login to Docker Hub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKER_USERNAME }}
    password: ${{ secrets.DOCKER_PASSWORD }}

- name: Push image
  run: |
    docker tag markettalento:latest ${{ secrets.DOCKER_USERNAME }}/markettalento:${{ github.sha }}
    docker push ${{ secrets.DOCKER_USERNAME }}/markettalento:${{ github.sha }}
```

---

## Archivos Modificados/Creados

| Archivo | Descripción |
|---------|-------------|
| `app/views/login.py` | Nuevo — Pantalla de login Streamlit |
| `app/main.py` | Modificado — Routing condicional (login → app) |
| `app/utils/api.py` | Modificado — Todas las peticiones llevan Bearer token |
| `app/components/sidebar.py` | Modificado — Info de usuario + botón logout |
| `src/api/sistema.py` | Nuevo — Health check avanzado + métricas |
| `.github/workflows/ci.yml` | Nuevo — Pipeline CI/CD |
| `docs/Produccion.md` | Nuevo — Guía completa de producción |

---

## Checklist Fase 3

- [x] Login/Logout en Streamlit con JWT
- [x] Todas las peticiones del frontend llevan token automáticamente
- [x] Health check avanzado con 4 checks (API, BD, embeddings, YOLO)
- [x] Métricas Prometheus expuestas en `/metrics`
- [x] CI/CD con GitHub Actions (test matrix + build Docker)
- [x] Documentación de producción completa
- [x] Tests de integración actualizados y pasando (20/20)

---

## Evolución del Sistema

| Fase | Enfoque | Estado |
|------|---------|--------|
| **Fase 1** | Seguridad + Contenerización | ✅ Completa |
| **Fase 2** | Robustez + Operaciones | ✅ Completa |
| **Fase 3** | Dashboard + Monitoreo + CI/CD | ✅ Completa |

**Resultado:** Sistema listo para desplegar en producción.
