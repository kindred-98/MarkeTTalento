# Documentación de MarkeTTalento

## Índice de Documentos

### Guías de Producción (3 Fases)

| Documento | Descripción |
|-----------|-------------|
| [`Produccion.md`](Produccion.md) | **Guía completa** para desplegar en producción (paso a paso) |
| [`Produccion/Fase1_Produccion.md`](Produccion/Fase1_Produccion.md) | Fase 1: Auth JWT, Docker, Alembic, variables de entorno |
| [`Produccion/Fase2_Produccion.md`](Produccion/Fase2_Produccion.md) | Fase 2: Backup, tests, rate limiting, logging, CORS |
| [`Produccion/Fase3_Produccion.md`](Produccion/Fase3_Produccion.md) | Fase 3: Login Streamlit, health check, métricas, CI/CD |

### Módulos del Sistema

| Documento | Descripción |
|-----------|-------------|
| [`arquitectura.md`](arquitectura.md) | Arquitectura general del sistema (Clean Architecture) |
| [`TPV.md`](TPV.md) | Terminal Punto de Venta — Tickets, cobros, dashboard |
| [`PrediccionesML.md`](PrediccionesML.md) | Motor de Machine Learning — Demanda, ABC, alertas, precios |
| [`VisionAI.md`](VisionAI.md) | Visión por Computador — Detección YOLO + similitud visual |
| [`Inspector.md`](Inspector.md) | Inspector de Producto — Búsqueda por barcode/SKU/nombre |

---

## Checklist de Despliegue Rápido

```bash
# 1. Clonar
git clone <repo>
cd MarkeTTalento

# 2. Configurar
openssl rand -hex 32 > .env.tmp
# Editar .env con SECRET_KEY, DATABASE_URL, etc.

# 3. Desplegar con Docker
docker-compose up -d --build

# 4. Crear usuarios
docker-compose exec api python scripts/crear_admin.py

# 5. Verificar
curl http://localhost:8002/api/v1/health
```

**Acceso:**
- Dashboard: `http://localhost:8501` → Login: `admin` / `admin123`
- API Docs: `http://localhost:8002/docs`
- Health: `http://localhost:8002/api/v1/health`
- Métricas: `http://localhost:8002/api/v1/metrics`

---

## Estado del Sistema

| Componente | Estado |
|------------|--------|
| Tests de integración | **20/20 ✅** |
| Docker build | **✅** |
| CI/CD GitHub Actions | **✅** |
| Health check | **✅** |
| Métricas Prometheus | **✅** |

**Listo para producción.**
