# Migración a PostgreSQL + Render.com

> **Fecha:** 2024  
> **Objetivo:** Convertir MarkeTTalento de SQLite-only a dual-database (SQLite dev / PostgreSQL prod) y preparar despliegue gratuito en Render.com.

---

## Resumen de Cambios

| Aspecto | Antes | Después |
|---------|-------|---------|
| Base de datos | SQLite único | SQLite (dev) + PostgreSQL (prod) |
| Docker Compose | Solo API + Streamlit | API + Streamlit + PostgreSQL 16 |
| Inicialización de datos | `crear_admin.py` (solo usuarios) | `init_db.py` (tablas + usuarios + categorías + proveedores + productos + tickets) |
| Backup | Copia de archivo `.db` | Auto-detecta: `cp` (SQLite) o `pg_dump` (PostgreSQL) |
| Deploy en cloud | No soportado | Blueprint `render.yaml` para Render.com |
| Dockerfile | Sin postgres client | Con `postgresql-client` para backups |

---

## Cambios Técnicos Detallados

### 1. Base de Datos Dual

**Archivo:** `src/core/database/database.py`

```python
if URL_DATABASE.startswith("postgresql"):
    engine = create_engine(URL_DATABASE, pool_pre_ping=True, echo=False)
elif URL_DATABASE.startswith("sqlite"):
    engine = create_engine(URL_DATABASE, connect_args={"check_same_thread": False})
```

- **PostgreSQL:** Usa `pool_pre_ping=True` para verificar conexiones antes de usarlas (evita errores de conexión cerrada).
- **SQLite:** Mantiene `check_same_thread=False` para compatibilidad con FastAPI.

### 2. Inicialización de Base de Datos

**Archivo:** `scripts/init_db.py` (nuevo)

Reemplaza a `crear_admin.py` como script de inicialización completo. Crea:

1. **Tablas** — Mediante `Base.metadata.create_all()`
2. **10 usuarios** — 1 admin (`admin`/`admin123`) + 9 cajeros
3. **10 categorías** — Bebidas, Lácteos, Panadería, Frutas, Verduras, Carnes, Pescados, Dulces, Snacks, Congelados
4. **5 proveedores** — Con contacto, teléfono y email
5. **21 productos** — Con barcode, SKU, precio, categoría, proveedor
6. **Inventario** — Stock inicial aleatorio (10-50 unidades) para cada producto
7. **~180 tickets de demo** — Distribuidos en 180 días con patrón estacional (más tickets en fines de semana)

**Uso:**
```bash
# Local (SQLite)
python scripts/init_db.py

# Docker (PostgreSQL)
docker-compose exec api python scripts/init_db.py

# Render.com (ejecutado automáticamente en start command)
```

### 3. Backup Multi-DB

**Archivo:** `scripts/backup_db.py` (actualizado)

Detecta automáticamente el tipo de base de datos:

**SQLite:**
```bash
python scripts/backup_db.py
# Crea: backups/markettalento_YYYYMMDD_HHMMSS.db
```

**PostgreSQL:**
```bash
python scripts/backup_db.py
# Crea: backups/markettalento_YYYYMMDD_HHMMSS.sql (formato custom pg_dump)
```

**Restaurar PostgreSQL:**
```bash
pg_restore -d "postgresql://user:pass@host:5432/db" backups/markettalento_YYYYMMDD_HHMMSS.sql
```

### 4. Docker Compose con PostgreSQL

**Archivo:** `docker-compose.yml` (actualizado)

Ahora incluye 3 servicios:

| Servicio | Imagen | Puerto | Descripción |
|----------|--------|--------|-------------|
| `postgres` | `postgres:16-alpine` | 5432 | Base de datos persistente |
| `api` | Build Dockerfile | 8002 | FastAPI + inicialización |
| `streamlit` | Build Dockerfile | 8501 | Dashboard |

**Orden de arranque:**
1. Postgres pasa healthcheck (`pg_isready`)
2. API ejecuta `init_db.py` y arranca uvicorn
3. Streamlit arranca y se conecta a la API

**Volumen persistente:**
```yaml
volumes:
  postgres_data:
```

Los datos de PostgreSQL sobreviven a `docker-compose down`.

### 5. Dockerfile Actualizado

**Archivo:** `Dockerfile`

Añadido `postgresql-client` al contenedor:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
```

Esto permite ejecutar `pg_dump` dentro del contenedor para backups.

### 6. Blueprint para Render.com

**Archivo:** `render.yaml` (nuevo)

Define la infraestructura completa para Render.com:

```yaml
services:
  - type: web
    name: markettalento-api
    runtime: docker
    plan: free
    # ...
  
  - type: web
    name: markettalento-dashboard
    runtime: docker
    plan: free
    # ...

databases:
  - name: markettalento-db
    plan: free
```

**Variables de entorno automáticas:**
- `DATABASE_URL` — Render inyecta automáticamente la URL de conexión a PostgreSQL
- `API_URL` — El dashboard recibe automáticamente la URL pública de la API

### 7. Variables de Entorno Actualizadas

**Archivo:** `.env.example`

```env
# SQLite (desarrollo local):
DATABASE_URL=sqlite:///data/markettalento.db
# PostgreSQL (produccion / Render.com):
# DATABASE_URL=postgresql://user:password@host:5432/markettalento

# Seguridad JWT (cambiar en produccion! Minimo 32 caracteres)
SECRET_KEY=cambia-esto-por-una-clave-secreta-larga-y-aleatoria

# CORS (origenes separados por coma)
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
```

---

## Guía de Despliegue en Render.com

### Paso 1: Preparar el Repositorio

Asegúrate de que estos archivos están en Git:
- `Dockerfile`
- `docker-compose.yml`
- `render.yaml`
- `requirements.txt`
- Todo el código fuente (`src/`, `app/`, `scripts/`)

**NO deben estar en Git:**
- `.env`
- `data/*.db`
- `logs/`
- `backups/`
- `__pycache__/`

### Paso 2: Crear Cuenta en Render.com

1. Ve a [render.com](https://render.com)
2. Regístrate con tu cuenta de GitHub
3. Conecta tu repositorio de MarkeTTalento

### Paso 3: Crear Base de Datos PostgreSQL

1. En el dashboard, clic en **New** → **PostgreSQL**
2. **Name:** `markettalento-db`
3. **Plan:** Free
4. **Database:** `markettalento`
5. **User:** `markettalento`
6. Clic en **Create Database**
7. Espera a que el estado sea `Available`
8. Copia la **Internal Database URL** (se usará automáticamente)

### Paso 4: Crear Web Service (API)

1. **New** → **Web Service**
2. Selecciona tu repositorio de GitHub
3. Configuración:
   - **Name:** `markettalento-api`
   - **Runtime:** Docker
   - **Plan:** Free
   - **Branch:** `main`
4. **Start Command:**
   ```bash
   sh -c "python scripts/init_db.py && uvicorn main:app --host 0.0.0.0 --port 8002"
   ```
5. **Environment Variables:**
   | Variable | Valor |
   |----------|-------|
   | `SECRET_KEY` | Genera con: `openssl rand -hex 32` |
   | `API_HOST` | `0.0.0.0` |
   | `API_PORT` | `8002` |
   | `LOG_LEVEL` | `INFO` |
   | `DATABASE_URL` | Dejar vacío — Render inyecta automáticamente desde la BD |
6. Clic en **Create Web Service**

### Paso 5: Crear Web Service (Dashboard)

1. **New** → **Web Service**
2. Mismo repositorio
3. Configuración:
   - **Name:** `markettalento-dashboard`
   - **Runtime:** Docker
   - **Plan:** Free
   - **Branch:** `main`
4. **Start Command:**
   ```bash
   streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0
   ```
5. **Environment Variables:**
   | Variable | Valor |
   |----------|-------|
   | `API_URL` | URL pública de `markettalento-api` (ej: `https://markettalento-api.onrender.com`) |
6. Clic en **Create Web Service**

### Paso 6: Verificar Despliegue

Espera a que ambos servicios muestren estado `Live`.

```bash
# Health check
curl https://markettalento-api.onrender.com/api/v1/health

# Dashboard
# Abre en navegador: https://markettalento-dashboard.onrender.com
```

### Paso 7: Evitar que se Duerma (Opcional)

Los servicios gratuitos se "duermen" tras 15 min de inactividad. Para evitarlo:

1. Regístrate en [UptimeRobot](https://uptimerobot.com) (gratis)
2. Crea un monitor:
   - **Type:** HTTP(s)
   - **URL:** `https://markettalento-api.onrender.com/api/v1/health`
   - **Interval:** 5 minutos
3. Guarda

Esto mantiene la API activa 24/7.

---

## Limitaciones del Tier Gratuito de Render.com

| Recurso | Límite | Nota |
|---------|--------|------|
| CPU/RAM | Compartida | Rendimiento variable |
| Sleep | 15 min inactividad | Primer request tras despertar: ~30s |
| PostgreSQL | 1 GB almacenamiento | Suficiente para ~1 año de datos |
| PostgreSQL | 90 días sin actividad | Se suspende (reactivable manualmente) |
| Banda ancha | 100 GB/mes | Suficiente para uso moderado |

---

## Checklist de Migración

- [x] `psycopg2-binary` en `requirements.txt`
- [x] `src/core/database/database.py` soporta PostgreSQL
- [x] `scripts/init_db.py` crea datos completos en cualquier BD
- [x] `scripts/backup_db.py` detecta SQLite vs PostgreSQL
- [x] `docker-compose.yml` incluye servicio PostgreSQL
- [x] `Dockerfile` incluye `postgresql-client`
- [x] `render.yaml` define infraestructura completa
- [x] `.env.example` documenta ambas configuraciones
- [x] Documentación actualizada en `docs/Produccion.md`
- [x] Tests pasan (20/20)

---

## Archivos Nuevos/Modificados

| Archivo | Tipo | Descripción |
|---------|------|-------------|
| `src/core/database/database.py` | Modificado | Soporte dual SQLite/PostgreSQL |
| `scripts/init_db.py` | Nuevo | Inicialización completa de BD |
| `scripts/backup_db.py` | Modificado | Auto-detecta tipo de BD |
| `docker-compose.yml` | Modificado | Añade servicio PostgreSQL |
| `Dockerfile` | Modificado | Añade `postgresql-client` |
| `render.yaml` | Nuevo | Blueprint Render.com |
| `.env.example` | Modificado | Variables para ambas BDs |
| `docs/Produccion.md` | Modificado | Guía Render.com añadida |
| `docs/Produccion/Fase1_Produccion.md` | Modificado | Notas sobre dual DB |
| `docs/Produccion/Fase2_Produccion.md` | Modificado | Notas sobre backup multi-DB |
| `docs/Migracion_PostgreSQL_Render.md` | Nuevo | Este documento |

---

## Próximos Pasos

1. **Verificar** que todo el proyecto está correcto (tests, validaciones, seguridad)
2. **Subir** el código a GitHub
3. **Desplegar** en Render.com siguiendo la guía anterior
4. **Configurar** UptimeRobot para evitar sleep
5. **Cambiar** contraseña de `admin` inmediatamente tras el primer login
