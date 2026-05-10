# Fase 1 — Fundamentos de Producción

> **Objetivo:** Establecer la base de seguridad, contenerización y configuración para desplegar MarkeTTalento en producción.

---

## Tabla de Contenidos

1. [Resumen](#resumen)
2. [Autenticación JWT](#autenticacion-jwt)
3. [Tabla de Usuarios](#tabla-de-usuarios)
4. [Docker y Docker Compose](#docker-y-docker-compose)
5. [Alembic — Migraciones de BD](#alembic--migraciones-de-bd)
6. [Variables de Entorno](#variables-de-entorno)
7. [Script de Usuarios por Defecto](#script-de-usuarios-por-defecto)
8. [Archivos Modificados/Creados](#archivos-modificadoscreados)

---

## Resumen

En esta fase se implementó el sistema de autenticación completo con JWT, se dockerizó la aplicación, se configuraron migraciones de base de datos con Alembic, y se añadieron variables de entorno para evitar hardcodear configuraciones sensibles.

---

## Autenticación JWT

El sistema utiliza **OAuth2 + JWT Bearer tokens** para proteger todos los endpoints de negocio.

### Flujo de autenticación

1. **Login:** `POST /api/v1/auth/login` con `username` y `password`
2. **Token:** La API devuelve un `access_token` JWT válido por **24 horas**
3. **Peticiones:** Incluir el token en el header `Authorization: Bearer <token>`

### Endpoints de autenticación

| Endpoint | Método | Descripción | Protección |
|----------|--------|-------------|------------|
| `/api/v1/auth/login` | POST | Autentica usuario y devuelve token | Público |
| `/api/v1/auth/register` | POST | Registra nuevo usuario | Admin |
| `/api/v1/auth/me` | GET | Devuelve info del usuario logueado | Autenticado |
| `/api/v1/auth/usuarios` | GET | Lista todos los usuarios | Admin |

### Implementación técnica

**Archivo:** `src/core/security/auth.py`

```python
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'markettalento-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 horas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
```

Funciones principales:
- `verify_password()` — Verifica contraseña contra hash bcrypt
- `get_password_hash()` — Genera hash bcrypt de una contraseña
- `create_access_token()` — Codifica JWT con claims `sub`, `rol`, `username`
- `decode_token()` — Decodifica y valida JWT
- `get_current_user()` — Dependencia FastAPI que extrae usuario del token
- `get_current_active_admin()` — Dependencia que requiere rol `admin`

**Nota de seguridad:** `SECRET_KEY` debe ser cambiada en producción mediante variable de entorno. La clave por defecto solo sirve para desarrollo.

---

## Tabla de Usuarios

Se creó la entidad `Usuario` en el dominio y su tabla correspondiente en SQLite.

**Campos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | Integer (PK) | Identificador único |
| `username` | String (unique) | Nombre de usuario |
| `hashed_password` | String | Hash bcrypt de la contraseña |
| `nombre_completo` | String | Nombre completo del usuario |
| `email` | String | Correo electrónico |
| `rol` | String | `admin` o `cajero` |
| `activo` | Boolean | Si el usuario está habilitado |
| `ultimo_login` | DateTime | Última fecha de acceso |
| `fecha_registro` | DateTime | Fecha de creación |

**Roles:**
- `admin` — Puede registrar usuarios, ver listado completo, acceder a todo
- `cajero` — Solo puede operar el TPV y ver datos de negocio

---

## Docker y Docker Compose

### Dockerfile

Multistage build optimizado:
- Instala dependencias del sistema (`libgl1`, `libglib2.0-0`, etc.)
- Descarga modelo YOLOv8n automáticamente
- Expone puertos `8002` (API) y `8501` (Streamlit)
- Comando por defecto: inicia API con uvicorn

### docker-compose.yml

Dos servicios:

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| `api` | `8002` | FastAPI + uvicorn |
| `streamlit` | `8501` | Dashboard Streamlit |

**Volúmenes persistentes:**
- `./data:/app/data` — Base de datos SQLite
- `./logs:/app/logs` — Logs de la aplicación
- `./backups:/app/backups` — Backups de BD

### Comandos útiles

```bash
# Construir y levantar
docker-compose up -d --build

# Ver logs
docker-compose logs -f api
docker-compose logs -f streamlit

# Detener
docker-compose down

# Reconstruir tras cambios
docker-compose up -d --build
```

---

## Alembic — Migraciones de BD

Configuración completa de Alembic para gestionar cambios en el esquema de la base de datos.

**Archivos:**
- `alembic.ini` — Configuración principal
- `alembic/env.py` — Contexto de migración con metadata de modelos
- `alembic/versions/` — Scripts de migración generados

### Comandos principales

```bash
# Crear nueva migración (tras cambiar modelos)
alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones pendientes
alembic upgrade head

# Ver historial
alembic history

# Revertir última migración
alembic downgrade -1
```

---

## Variables de Entorno

Toda configuración sensible se externalizó a variables de entorno. El archivo `.env` está en `.gitignore` para evitar filtrar secretos.

**Archivo de ejemplo:** `.env.example`

```env
# OBLIGATORIO
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria-minimo-32-caracteres
DATABASE_URL=sqlite:///data/markettalento.db
API_HOST=0.0.0.0
API_PORT=8002

# OPCIONAL
LOG_LEVEL=INFO
STREAMLIT_PORT=8501
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501
YOLO_MODEL=yolov8n.pt
```

**Configuración en código:** `src/core/config/config.py` usa `BaseSettings` de Pydantic para cargar automáticamente variables de entorno.

---

## Script de Usuarios por Defecto

**Archivo:** `scripts/crear_admin.py`

Crea automáticamente 10 usuarios al ejecutarse:

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

**Uso:**
```bash
python scripts/crear_admin.py
```

**IMPORTANTE:** Cambiar contraseñas inmediatamente tras el primer despliegue en producción.

---

## Archivos Modificados/Creados

| Archivo | Descripción |
|---------|-------------|
| `src/core/security/auth.py` | Nuevo — JWT, bcrypt, dependencias de seguridad |
| `src/api/auth.py` | Nuevo — Endpoints de autenticación |
| `src/dominio/entidades/entidades.py` | Modificado — Añadida entidad `Usuario` |
| `src/core/config/config.py` | Modificado — Carga variables de entorno |
| `Dockerfile` | Nuevo — Imagen Docker multistage |
| `docker-compose.yml` | Nuevo — Orquestación de servicios |
| `alembic.ini` + `alembic/` | Nuevo — Migraciones de BD |
| `.env.example` | Nuevo — Plantilla de variables de entorno |
| `scripts/crear_admin.py` | Nuevo — Creación de usuarios por defecto |
| `scripts/init_db.py` | Nuevo — Inicializa BD completa (tablas + datos demo) |
| `src/core/database/database.py` | Modificado — Soporte SQLite y PostgreSQL |
| `.gitignore` | Modificado — Excluye `.env`, `data/*.db`, `logs/`, `backups/` |
| `requirements.txt` | Modificado — Añadido `passlib[bcrypt]`, `python-jose[cryptography]` |

---

## Checklist Fase 1

- [x] Autenticación JWT implementada
- [x] Tabla `usuarios` en base de datos
- [x] Docker + docker-compose configurados
- [x] Alembic migraciones funcionando
- [x] Variables de entorno externalizadas
- [x] Script de usuarios por defecto
- [x] Script de inicialización completa de BD (`init_db.py`)
- [x] Soporte dual: SQLite (dev) y PostgreSQL (prod)
- [x] `.db` y `.env` excluidos de Git
- [x] Contraseñas hasheadas con bcrypt
