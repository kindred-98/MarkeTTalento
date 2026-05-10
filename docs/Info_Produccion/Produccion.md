# Guía de Producción — MarkeTTalento

Documentación completa para desplegar MarkeTTalento en un entorno de producción.

---

## Documentación por Fases

La implementación de producción se divide en 3 fases documentadas:

| Fase | Documento | Enfoque |
|------|-----------|---------|
| **Fase 1** | [`Info_Produccion/Fase1_Produccion.md`](Info_Produccion/Fase1_Produccion.md) | Autenticación JWT, Docker, Alembic, variables de entorno |
| **Fase 2** | [`Info_Produccion/Fase2_Produccion.md`](Info_Produccion/Fase2_Produccion.md) | Backup, tests, rate limiting, logging, CORS |
| **Fase 3** | [`Info_Produccion/Fase3_Produccion.md`](Info_Produccion/Fase3_Produccion.md) | Login Streamlit, health check, métricas, CI/CD |

---

## Tabla de Contenidos

1. [Requisitos Previos](#requisitos-previos)
2. [Configuración de Variables de Entorno](#configuracion-de-variables-de-entorno)
3. [Despliegue con Docker (Recomendado)](#despliegue-con-docker-recomendado)
4. [Despliegue Manual (Windows/Linux)](#despliegue-manual-windowslinux)
5. [Primer Inicio y Usuarios](#primer-inicio-y-usuarios)
6. [Autenticación JWT](#autenticacion-jwt)
7. [Backups de Base de Datos](#backups-de-base-de-datos)
8. [Métricas y Monitoreo](#metricas-y-monitoreo)
9. [Actualización del Sistema](#actualizacion-del-sistema)
10. [Solución de Problemas](#solucion-de-problemas)

---

## Requisitos Previos

| Componente | Versión mínima | Notas |
|------------|----------------|-------|
| Python | 3.11 | Recomendado 3.12 |
| Docker | 24.0 | Solo si usas Docker |
| Docker Compose | 2.20 | Solo si usas Docker |
| PostgreSQL | 16 | Recomendado para producción |
| Git | 2.40 | Para clonar/actualizar |
| Memoria RAM | 2 GB | 4 GB recomendado |
| Disco | 5 GB | Incluye espacio para backups y logs |

---

## Configuración de Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# ==========================================
# CONFIGURACION OBLIGATORIA
# ==========================================

# Clave secreta para JWT (cambiar en produccion! Minimo 32 caracteres)
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria-minimo-32-caracteres

# URL de la base de datos
# SQLite (desarrollo local):
DATABASE_URL=sqlite:///data/markettalento.db
# PostgreSQL (produccion / Render.com / Docker):
# DATABASE_URL=postgresql://user:password@host:5432/markettalento

# Host y puerto de la API
API_HOST=0.0.0.0
API_PORT=8002

# ==========================================
# CONFIGURACION OPCIONAL
# ==========================================

# Nivel de logs (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO

# Puertos del dashboard
STREAMLIT_PORT=8501

# Origenes permitidos para CORS (separados por coma)
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501

# Ruta del modelo YOLO
YOLO_MODEL=yolov8n.pt
```

**IMPORTANTE:** Nunca subas el archivo `.env` a Git. Ya está en `.gitignore` por defecto.

---

## Despliegue con Docker (Recomendado)

### Paso 1: Clonar el repositorio

```bash
git clone <tu-repositorio>
cd MarkeTTalento
```

### Paso 2: Crear el archivo `.env`

```bash
cp .env.example .env
# Editar .env con tus valores
nano .env
```

### Paso 3: Construir y levantar

```bash
docker-compose up -d --build
```

### Paso 4: Verificar que todo funciona

```bash
# Health check
curl http://localhost:8002/api/v1/health

# Documentación de la API
curl http://localhost:8002/docs
```

### Servicios expuestos

| Servicio | URL | Descripción |
|----------|-----|-------------|
| API FastAPI | `http://localhost:8002` | Backend REST |
| API Docs | `http://localhost:8002/docs` | Swagger UI |
| Dashboard | `http://localhost:8501` | Streamlit |
| Health Check | `http://localhost:8002/api/v1/health` | Estado del sistema |
| Métricas | `http://localhost:8002/api/v1/metrics` | Métricas Prometheus |

### Comandos útiles de Docker

```bash
# Ver logs
docker-compose logs -f api
docker-compose logs -f streamlit

# Reiniciar servicios
docker-compose restart

# Detener todo
docker-compose down

# Actualizar tras cambios
docker-compose up -d --build
```

---

## Despliegue en Render.com (Gratuito)

Render.com ofrece un tier gratuito perfecto para desplegar MarkeTTalento con PostgreSQL.

### Paso 1: Subir código a GitHub

Asegúrate de que todo tu código esté en un repositorio de GitHub.

### Paso 2: Crear cuenta en Render.com

Regístrate en [render.com](https://render.com) con tu cuenta de GitHub.

### Paso 3: Crear Base de Datos PostgreSQL

1. En el dashboard de Render, ve a **New** → **PostgreSQL**
2. Nombre: `markettalento-db`
3. Plan: **Free**
4. Clic en **Create Database**
5. Espera a que esté disponible y copia la **Internal Database URL**

### Paso 4: Crear Web Service (API)

1. **New** → **Web Service**
2. Conecta tu repositorio de GitHub
3. Configuración:
   - **Name:** `markettalento-api`
   - **Runtime:** Docker
   - **Plan:** Free
   - **Start Command:** `sh -c "python scripts/init_db.py && uvicorn main:app --host 0.0.0.0 --port 8002"`
4. Añade variables de entorno:
   - `DATABASE_URL` = URL interna de la BD (del paso 3)
   - `SECRET_KEY` = Genera una clave larga (`openssl rand -hex 32`)
   - `API_HOST` = `0.0.0.0`
   - `API_PORT` = `8002`
5. Clic en **Create Web Service**

### Paso 5: Crear Web Service (Dashboard)

1. **New** → **Web Service**
2. Mismo repositorio
3. Configuración:
   - **Name:** `markettalento-dashboard`
   - **Runtime:** Docker
   - **Plan:** Free
   - **Start Command:** `streamlit run app/main.py --server.port=8501 --server.address=0.0.0.0`
4. Añade variable:
   - `API_URL` = URL pública de `markettalento-api` (ej: `https://markettalento-api.onrender.com`)
5. Clic en **Create Web Service**

### Limitaciones del tier gratuito

- **Sleep:** Los servicios se "duermen" tras 15 min de inactividad. El primer request tras despertar tarda ~30s.
- **BD:** 1 GB de almacenamiento, se suspende tras 90 días sin actividad (se puede reactivar).
- **Requests:** Sin límite, pero el sleep afecta la experiencia.

**Consejo:** Usa [UptimeRobot](https://uptimerobot.com) gratis para hacer ping cada 5 min a tu health check y evitar que se duerma.

---

## Despliegue Manual (Windows/Linux)

### Paso 1: Instalar dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 2: Crear directorios necesarios

```bash
mkdir -p data logs backups docs/img_productos
```

### Paso 3: Crear usuarios por defecto

```bash
python scripts/crear_admin.py
```

### Paso 4: Aplicar migraciones (si existen)

```bash
alembic upgrade head
```

### Paso 5: Iniciar servicios

**Windows:**
```bash
deploy.bat
```

**Linux/macOS:**
```bash
# Terminal 1: API
uvicorn main:app --host 0.0.0.0 --port 8002

# Terminal 2: Dashboard
streamlit run app/main.py --server.port 8501 --server.address 0.0.0.0
```

---

## Primer Inicio y Usuarios

Tras el primer despliegue, el script `crear_admin.py` crea automáticamente:

| Usuario | Contraseña | Rol |
|---------|------------|-----|
| `admin` | `admin123` | `admin` |
| `andres` | `andres` | `cajero` |
| `edu` | `edu` | `cajero` |
| `carlos` | `carlos` | `cajero` |
| `alberto` | `alberto` | `cajero` |
| `irrael` | `irrael` | `cajero` |
| `YioQueSe` | `YioQueSe` | `cajero` |
| `fernando` | `fernando` | `cajero` |
| `ernesto` | `ernesto` | `cajero` |
| `raul` | `raul` | `cajero` |

**Cambiar contraseñas inmediatamente tras el primer login.**

---

## Autenticación JWT

El sistema usa OAuth2 + JWT Bearer tokens.

### Flujo de autenticación

1. **Login:** `POST /api/v1/auth/login` con `username` y `password`
2. **Token:** La API devuelve un `access_token` JWT válido por 24 horas
3. **Peticiones:** Incluir el token en el header `Authorization: Bearer <token>`

### Protección de endpoints

| Nivel | Endpoints protegidos |
|-------|---------------------|
| Público | `/salud`, `/estado`, `/health`, `/metrics`, `/docs` |
| Autenticado | Todos los endpoints de negocio (productos, tickets, etc.) |
| Admin | Registro de usuarios, listado de usuarios |

---

## Backups de Base de Datos

El script `scripts/backup_db.py` detecta automáticamente si usas SQLite o PostgreSQL.

### Backup manual

```bash
python scripts/backup_db.py
```

**SQLite:** Crea `backups/markettalento_YYYYMMDD_HHMMSS.db`
**PostgreSQL:** Crea `backups/markettalento_YYYYMMDD_HHMMSS.sql` (formato custom con `pg_dump`)

### Backup automático (Linux - cron)

```bash
# Editar crontab
crontab -e

# Agregar linea para backup diario a las 3:00 AM
0 3 * * * cd /ruta/a/MarkeTTalento && python scripts/backup_db.py >> logs/backup.log 2>&1
```

### Restaurar backup

**SQLite:**
```bash
docker-compose down
cp backups/markettalento_YYYYMMDD_HHMMSS.db data/markettalento.db
docker-compose up -d
```

**PostgreSQL:**
```bash
# Restaurar con pg_restore
pg_restore -d "postgresql://user:pass@host:5432/db" backups/markettalento_YYYYMMDD_HHMMSS.sql
```

---

## Métricas y Monitoreo

### Health Check Avanzado

```bash
curl http://localhost:8002/api/v1/health
```

Verifica:
- Estado de la API
- Conectividad con la base de datos
- Disponibilidad de embeddings de Visión AI
- Presencia del modelo YOLOv8

### Métricas Prometheus

```bash
curl http://localhost:8002/api/v1/metrics
```

Métricas disponibles:
- `markettalento_productos_total` — Productos activos
- `markettalento_tickets_total` — Tickets totales
- `markettalento_usuarios_total` — Usuarios registrados
- `markettalento_stock_total` — Unidades en inventario

### Integración con Prometheus + Grafana

1. Añadir scrape config a `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'markettalento'
    static_configs:
      - targets: ['localhost:8002']
    metrics_path: '/api/v1/metrics'
```

2. Crear dashboard en Grafana con las métricas anteriores.

---

## Actualización del Sistema

### Actualización con Docker

```bash
# 1. Hacer backup
python scripts/backup_db.py

# 2. Obtener ultimo codigo
git pull origin main

# 3. Reconstruir e iniciar
docker-compose down
docker-compose up -d --build

# 4. Aplicar migraciones si existen
docker-compose exec api alembic upgrade head
```

### Actualización manual

```bash
# 1. Backup
python scripts/backup_db.py

# 2. Actualizar codigo
git pull origin main

# 3. Actualizar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
alembic upgrade head

# 5. Reiniciar servicios
# (detener y volver a iniciar uvicorn y streamlit)
```

---

## Solución de Problemas

### Problema: La API no arranca

```bash
# Verificar logs
docker-compose logs api

# Verificar que el puerto no está ocupado
netstat -tlnp | grep 8002

# Probar conexión manual
curl http://localhost:8002/api/v1/salud
```

### Problema: Error 401 en todas las peticiones

El frontend no tiene token JWT. Asegúrate de:
1. Iniciar sesión en el dashboard
2. Que la API y el dashboard usen la misma `SECRET_KEY`

### Problema: La Visión AI no detecta productos

1. Verificar que hay fotos de referencia: `GET /api/v1/vision/referencias`
2. Re-entrenar el modelo: `POST /api/v1/vision/entrenar`
3. Verificar que el archivo `data/embeddings_productos.pkl` existe

### Problema: Base de datos bloqueada (SQLite)

SQLite no permite escrituras concurrentes. Si hay un error de "database is locked":
1. Verificar que solo hay una instancia de la API corriendo
2. Reiniciar el servicio
3. Si persiste, restaurar desde backup

### Problema: Los logs crecen infinitamente

El sistema usa `RotatingFileHandler` con un máximo de 10 MB por archivo y 5 backups. Si necesitas ajustar esto, modifica `src/core/logging.py`.

---

## Arquitectura en Producción

```
Internet
    |
    v
[Nginx / Traefik / Cloudflare]  <- Reverse proxy + SSL
    |
    +---> http://tu-dominio:8501  (Streamlit Dashboard)
    |
    +---> http://tu-dominio:8002  (FastAPI)
            |
            +-- SQLite (data/markettalento.db)
            +-- Embeddings (data/embeddings_productos.pkl)
            +-- Logs (logs/)
            +-- Backups (backups/)
```

**Recomendaciones para escalar:**
- Usar Nginx como reverse proxy con SSL (Let's Encrypt)
- Limitar acceso al puerto 8501/8002 con firewall
- Configurar backup automático diario
- Monitorizar `/api/v1/health` con UptimeRobot o similar

---

## Soporte

Si encuentras problemas:

1. Revisar logs: `logs/markettalento.log`
2. Verificar health check: `curl http://localhost:8002/api/v1/health`
3. Ejecutar tests: `pytest tests/ -v`
4. Abrir un issue en el repositorio con los logs de error
