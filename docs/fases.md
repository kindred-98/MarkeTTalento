# MarkeTTalento - Fases de Desarrollo

## Resumen del Proyecto

Sistema de gestión de inventario inteligente para supermercados, combinando **Visión Artificial** (YOLOv8), **Machine Learning** para predicciones de demanda, y un **Dashboard futurista** con diseño oscuro/cyan.

---

## 📊 Progreso General

```
████████████████████░░░░  85% Completado
```

| Componente | Estado | Progreso |
|------------|--------|----------|
| API REST | ✅ Completo | 100% |
| Base de Datos | ✅ Completo | 100% |
| Dashboard UI | ✅ Completo | 100% |
| Visión Artificial | ✅ Implementado | 80% |
| Predicciones ML | ✅ Implementado | 75% |
| Autenticación | ❌ Pendiente | 0% |
| Tests | ❌ Pendiente | 0% |
| Docker | ❌ Pendiente | 0% |

---

## Fase 1: Fundamentos ✅

### Completado
- [x] Arquitectura Clean Architecture
- [x] API REST con FastAPI
- [x] Base de datos SQLite
- [x] Entidades: Categoria, Proveedor, Producto, Inventario, Venta
- [x] Repositorios con SQLAlchemy
- [x] Schemas Pydantic

### Archivos
```
src/
├── core/
│   ├── config.py        ✅ Configuración central
│   └── database.py     ✅ Conexión BD
├── dominio/
│   ├── entidades.py    ✅ Modelos SQLAlchemy
│   └── repositorios.py ✅ Interfaces
├── aplicacion/
│   ├── schemas.py      ✅ Pydantic models
│   └── servicios/      ✅ Lógica de negocio
└── infraestructura/
    └── repositorios_impl.py ✅ Implementación
```

---

## Fase 2: API REST ✅

### Endpoints Implementados

| Tag | Endpoints | Estado |
|-----|-----------|--------|
| Sistema | `/`, `/salud` | ✅ |
| Categorías | POST, GET | ✅ |
| Proveedores | POST, GET | ✅ |
| Productos | CRUD completo (6 endpoints) | ✅ |
| Inventario | 5 endpoints | ✅ |
| Ventas | 3 endpoints | ✅ |
| Predicciones | 3 endpoints | ✅ |
| Visión Artificial | 2 endpoints | ✅ |
| Análisis | 1 endpoint | ✅ |

**Total: 26+ endpoints**

### Documentación
- Swagger UI: http://localhost:8002/docs
- ReDoc: http://localhost:8002/redoc

---

## Fase 3: Dashboard Streamlit ✅

### Completado

| Sección | Estado | Características |
|---------|--------|-----------------|
| Dashboard | ✅ | Métricas, gráficos donut, alertas |
| Productos | ✅ | Cards visuales, formulario creación |
| Inventario | ✅ | Cards con estado (CRÍTICO/BAJO/OK) |
| Ventas | ✅ | Historial en cards, registro |
| Predicciones | ✅ | Gráfico de barras, estados |
| Visión AI | ✅ | Upload imagen, detección, mapeo |

### Diseño Implementado

- [x] Tema oscuro futurista
- [x] Colores: Cyan, Purple, Green, Red, Orange, Pink, Blue
- [x] Sidebar con navegación por botones
- [x] Cards visuales (no dataframes feos)
- [x] Reloj en tiempo real (HH:MM:SS)
- [x] Fecha completa (día, fecha, mes, año)
- [x] Estado API con indicador verde animado
- [x] Enlaces a Dashboard y API Docs

### Estructura del Sidebar

```
⚡ Menú
─────────────────────────────────
[🏠 Dashboard]
[📦 Productos]
[📊 Inventario]
[💰 Ventas]
[🔮 Predicciones]
[📸 Visión AI]
─────────────────────────────────
[🟢 API Online]
  Puerto: 8002
  14:35:22
  Lunes 28 Abr 2026
─────────────────────────────────
[📊 Dashboard] → nueva pestaña
[📚 API Docs]  → nueva pestaña
─────────────────────────────────
```

---

## Fase 4: Visión Artificial ✅

### Implementado

- [x] Integración con YOLOv8 (Ultralytics)
- [x] Detección de objetos en imágenes
- [x] Mapeo objetos COCO → productos BD
- [x] Actualización automática de inventario
- [x] Endpoint: `/api/v1/vision/detectar`
- [x] Endpoint: `/api/v1/vision/analizar-y-actualizar`

### Modelo Utilizado
- **YOLOv8n** (nano) - Rápido y ligero
- **Dataset**: COCO (80 clases genéricas)

### Clases COCO Disponibles
```
Alimentos: banana, apple, sandwich, orange, broccoli, carrot, 
           hotdog, pizza, donut, cake, bread, carrot
Bebidas:   bottle, wine glass, cup
Objetos:   book, clock, vase, scissors, teddy bear
Personas:  person
```

### Mapeo Implementado

```python
MAPA_YOLO_A_PRODUCTO = {
    "bottle": {"producto_nombre": "Botella de Agua", "cantidad_por_defecto": 1},
    "cup": {"producto_nombre": "Vasos", "cantidad_por_defecto": 2},
    "wine glass": {"producto_nombre": "Copa", "cantidad_por_defecto": 1},
    "banana": {"producto_nombre": "Plátanos", "cantidad_por_defecto": 1},
    "apple": {"producto_nombre": "Manzanas", "cantidad_por_defecto": 1},
    "orange": {"producto_nombre": "Naranjas", "cantidad_por_defecto": 1},
    "broccoli": {"producto_nombre": "Brócoli", "cantidad_por_defecto": 1},
    "carrot": {"producto_nombre": "Zanahorias", "cantidad_por_defecto": 1},
    "hotdog": {"producto_nombre": "Hot Dog", "cantidad_por_defecto": 1},
    "pizza": {"producto_nombre": "Pizza", "cantidad_por_defecto": 1},
    "donut": {"producto_nombre": "Donut", "cantidad_por_defecto": 1},
    "cake": {"producto_nombre": "Pastel", "cantidad_por_defecto": 1},
    "bread": {"producto_nombre": "Pan", "cantidad_por_defecto": 1},
    "sandwich": {"producto_nombre": "Sándwich", "cantidad_por_defecto": 1},
}
```

### Pendiente
- [ ] Modelo YOLO personalizado con fotos reales del supermercado
- [ ] Más mapeos de productos específicos
- [ ] Detección de estanterías completas

---

## Fase 5: Predicciones de Demanda ✅

### Algoritmo Implementado

1. **Recopilación de historial de ventas**
2. **Cálculo de consumo promedio diario**
3. **Predicción de días hasta agotarse**
4. **Clasificación del estado**

### Estados de Predicción

| Estado | Días restantes | Color |
|--------|-----------------|-------|
| CRÍTICO | ≤3 días | 🔴 Rojo |
| BAJO | ≤7 días | 🟠 Naranja |
| MODERADO | ≤14 días | 🔵 Azul |
| ADECUADO | >14 días | 🟢 Verde |

### Fórmula

```
dias_hasta_agotarse = stock_actual / consumo_promedio_diario

consumo_promedio_diario = Σ(cantidades_vendidas) / días_desde_primera_venta
```

### Endpoints

| Endpoint | Descripción |
|----------|-------------|
| `GET /predicccion/{id}` | Predicción individual |
| `GET /prediccion/todos` | Todas las predicciones |
| `GET /prediccion/semanal/{id}` | Pronóstico semanal |

---

## Fase 6: Ejecución y Deployment 🚧

### Launcher Implementado ✅

```bash
python iniciar.py
```

**Funcionalidades:**
- Verifica si la API ya está corriendo
- Inicia FastAPI automáticamente si es necesario
- Inicia Streamlit automáticamente si es necesario
- Abre el navegador con Dashboard y API Docs
- Mantiene procesos activos

### Accesos

| Servicio | URL | Puerto |
|----------|-----|--------|
| Dashboard | http://localhost:8501 | 8501 |
| API Docs | http://localhost:8002/docs | 8002 |
| API Redoc | http://localhost:8002/redoc | 8002 |
| API Base | http://localhost:8002 | 8002 |

---

## 🔄 Cambios Recientes

### 28 Abril 2026

- **Sidebar reformado**: 6 botones de navegación en lugar de selectbox
- **Estado API**: Card con indicador verde animado + reloj en tiempo real
- **Cards visuales**: Productos, Inventario y Ventas ahora usan cards en lugar de dataframes
- **Limpieza de datos**: Fechas legibles, nombres claros, sin código basura
- **Enlaces**: Dashboard y API Docs ahora son links clickeables
- **Documentación actualizada**: `docs/README.md` y `docs/fases.md`

---

## 📋 Pendientes

### Alta Prioridad
- [ ] Modelo YOLO personalizado
- [ ] Más mapeos de productos → objetos detectados

### Media Prioridad
- [ ] Autenticación JWT
- [ ] Tests con pytest
- [ ] Web scraping de proveedores (si es posible)

### Baja Prioridad
- [ ] Docker + docker-compose
- [ ] Migración a PostgreSQL
- [ ] Notificaciones push
- [ ] App móvil

---

## 📁 Estructura Actual del Proyecto

```
MarkeTTalento/
│
├── 📄 main.py                    # API FastAPI (puerto 8002)
├── 📄 streamlit_app.py          # Dashboard (puerto 8501)
├── 📄 iniciar.py                 # Launcher (TODO en uno)
├── 📄 requirements.txt          # Dependencias
├── 📄 .env                      # Variables de entorno
│
├── 📁 src/
│   ├── 📁 core/
│   │   ├── config.py            # Settings
│   │   └── database.py          # SQLAlchemy
│   ├── 📁 dominio/
│   │   ├── entidades.py          # Categoria, Proveedor, Producto, Inventario, Venta
│   │   └── repositorios.py       # Interfaces
│   ├── 📁 aplicacion/
│   │   ├── schemas.py           # Pydantic
│   │   └── servicios/
│   │       ├── producto_servicio.py
│   │       ├── inventario_servicio.py
│   │       ├── prediccion_servicio.py
│   │       ├── vision_servicio.py
│   │       └── inventario_vision.py
│   └── 📁 infraestructura/
│       └── repositorios_impl.py
│
├── 📁 data/
│   └── markettalento.db         # SQLite
│
├── 📁 docs/
│   ├── README.md                # Documentación general
│   └── fases.md                 # Este archivo
│
└── 📁 temp/                     # Archivos temporales YOLO
```

---

## 🎯 Estado por Fase

| Fase | Nombre | Estado | Progreso |
|------|--------|--------|----------|
| 1 | Fundamentos | ✅ | 100% |
| 2 | API REST | ✅ | 100% |
| 3 | Dashboard | ✅ | 100% |
| 4 | Visión Artificial | ✅ | 80% |
| 5 | Predicciones | ✅ | 75% |
| 6 | Deployment | 🚧 | 70% |

---

## 📝 Notas de Desarrollo

### Deprecation Warnings Corregidos
- `datetime.utcnow()` → `datetime.now(timezone.utc)` ✅
- `use_container_width` → `width='stretch'` ✅
- `paper_bgcolor="transparent"` → hex color ✅

### Limitaciones Conocidas
1. YOLOv8 COCO es genérico - no detecta productos específicos de supermercado
2. Sin autenticación - sistema abierto
3. SQLite para desarrollo - PostgreSQL para producción

### Próximos Pasos Recomendados
1. Entrenar modelo YOLO personalizado
2. Implementar autenticación JWT
3. Agregar tests automatizados
4. Configurar Docker
5. Migrar a PostgreSQL

---

*Última actualización: 28 Abril 2026*
*Versión: 1.0.0*
*Progreso: 85%*

![alt text](114031.jpg)

MarkeTTalento/
│
├── run.py                          ← ÚNICO punto de entrada
│   └── Lanza: src/api/main.py (API) + app/main.py (Dashboard) + abre navegador
│
├── src/api/main.py                 ← API FastAPI (movido desde raíz/main.py)
│   └── Endpoints: /api/v1/productos, /api/v1/inventario, /api/v1/ventas, etc.
│
├── app/                            ← NUEVO: Todo el frontend modularizado
│   │
│   ├── __init__.py
│   │
│   ├── main.py                     ← Dashboard Streamlit (era streamlit_app.py)
│   │   ├── Importa y ensambla todo
│   │   ├── Carga CSS global
│   │   ├── Renderiza sidebar
│   │   ├── Router de páginas (if menu == "X": page.render())
│   │   └── Maneja estado global
│   │
│   ├── config.py                   ← Configuración (API_URL, etc.)
│   │
│   ├── styles/                     ← CSS modularizado por funcionalidad
│   │   ├── global.css              ← Variables CSS, tema oscuro, scrollbar, fuentes
│   │   ├── components.css          ← Botones, cards, inputs, tabs, file uploader
│   │   ├── sidebar.css             ← Estilos del menú lateral
│   │   ├── dashboard.css           ← Métricas, gráficos, filtros del dashboard
│   │   ├── productos.css           ← Cards de producto, catálogo, formularios nuevo/edición
│   │   ├── inventario.css          ← Cards de inventario, badges de estado, controles +/-
│   │   ├── ventas.css              ← Cards de ventas, formulario nueva venta
│   │   ├── predicciones.css        ← Gráficos de predicciones ML
│   │   └── vision.css              ← Vista de cámara, preview, resultados
│   │
│   ├── utils/                      ← Utilidades reutilizables (sin UI)
│   │   ├── __init__.py
│   │   ├── api.py                  ← api_get(), api_post(), api_put() - comunicación con backend
│   │   ├── helpers.py              ← to_excel(), formatters, funciones auxiliares
│   │   └── state.py                ← Gestión de session_state, inicialización de variables
│   │
│   ├── logic/                      ← Lógica de negocio pura (sin Streamlit)
│   │   ├── __init__.py
│   │   ├── producto.py             ← Validaciones de producto, cálculos de margen
│   │   ├── inventario.py           ← Cálculo de estados (Crítico/Bajo/Saludable), validaciones stock
│   │   └── venta.py                ← Cálculos de totales, validaciones de ventas
│   │
│   ├── components/                 ← Componentes UI reutilizables (bloques visuales)
│   │   ├── __init__.py
│   │   ├── sidebar.py              ← Menú lateral completo con navegación y estado activo
│   │   ├── header.py               ← Header animado de la aplicación con título y badges
│   │   ├── metric_card.py          ← Cards de métricas para dashboard (4 métricas principales)
│   │   ├── product_card.py         ← Card individual de producto (imagen, nombre, precio, stock)
│   │   ├── inventario_card.py      ← Card de item de inventario con info de stock y ubicación
│   │   ├── stock_badge.py          ← Badge de estado con color (Crítico/Bajo/Saludable/Agotado)
│   │   ├── stock_progress.py       ← Barra de progreso de stock (0-100% con color según estado)
│   │   ├── file_uploader.py        ← Componente de subida de imágenes estilizado (drop zone)
│   │   ├── success_modal.py        ← Modal de éxito con animación (usado al crear producto)
│   │   └── data_table.py           ← Tablas con paginación, filtros y botón exportar Excel
│   │
│   └── pages/                      ← Cada sección del menú como módulo independiente
│       ├── __init__.py
│       ├── dashboard.py            ← Dashboard: métricas, gráfico pastel, tabla stock, alertas
│       ├── productos.py            ← Productos: Catálogo + Nuevo + Edición (3 tabs/sub-secciones)
│       ├── inventario.py           ← Inventario: Lista con filtros, ajuste rápido +/-, exportar
│       ├── ventas.py               ← Ventas: Historial con cards + formulario nueva venta
│       ├── predicciones.py         ← Predicciones: Gráficos ML de demanda por producto
│       ├── vision_ai.py            ← Visión AI: Selector cámara/imagen, detección, resultados
│       └── barcode.py              ← Barcode: Escáner de códigos de barras
│
├── src/                            ← Backend (ya existe, sin cambios en estructura)
│   ├── api/                        ← Aquí va main.py con endpoints
│   ├── core/
│   │   ├── config/
│   │   └── database/
│   ├── dominio/
│   │   ├── entidades/
│   │   └── repositorios/
│   ├── aplicacion/
│   │   ├── servicios/
│   │   └── schemas/
│   └── infraestructura/
│       └── repositorios/
│
├── data/                           ← Base de datos SQLite (markettalento.db)
├── docs/productos/                 ← Imágenes subidas de productos
├── models/                         ← Modelos ML/YOLO
└── requirements.txt

ARCHIVOS QUE SE ELIMINAN:
❌ main.py (raíz) → se mueve a src/api/main.py
❌ streamlit_app.py (raíz) → se divide en app/main.py + app/pages/*.py
❌ iniciar.py (raíz) → reemplazado por run.py

MarkeTTalento/
├── data/                      ✅ Bases de datos (data/ restaurado)
│   ├── markettalento.db
│   └── inventario.db
│
├── src/core/database/         ✅ Código de conexión (database/ restaurado)
│   ├── __init__.py
│   ├── base.py
│   ├── database.py
│   └── multi_database.py      ← Soporte multi-DB
│
├── src/implementaciones/      ✅ (antes infraestructura)
│   └── repositorios_impl.py
│
├── tests/                     ✅ Tests reorganizados
│   └── (vacío - scripts de test movidos/eliminados)
│
├── scripts/
│   └── crear_datos.py         ✅ Script de utilidad
│
└── ... (resto del proyecto)


El usuario quiere que actúe como su "señor tutor" y quiere saber qué le falta a la app para funcionar correctamente. Me dice que hay botones que no hacen nada o hacen las cosas mal, y hay errores en ciertas partes.

Como tutor, debo:

Hacer un diagnóstico honesto del estado actual
Identificar problemas específicos que he visto
Priorizar qué necesita arreglarse
Dar recomendaciones profesionales

Problemas que he detectado o sospecho:

Botones en el sidebar - Los botones del menú pueden no estar funcionando correctamente con el caching
Validaciones - Faltan validaciones en formularios
Testing - No hay tests automatizados reales
Errores de UX - Algunos flujos no son intuitivos
Manejo de errores - Si la API falla, la app puede crashar
Estados de carga - Falta feedback cuando se cargan datos
Paginación - Puede haber bugs en la paginación
Filtros - Los filtros pueden no funcionar correctamente con el cache
Debo ser honesto pero constructivo.