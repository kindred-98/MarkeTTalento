# MarkeTTalento - Sistema de Inventario Inteligente

## Tabla de Contenidos

1. [Descripción del Proyecto](#descripción-del-proyecto)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [Tecnologías Utilizadas](#tecnologías-utilizadas)
4. [Estructura del Proyecto](#estructura-del-proyecto)
5. [Instalación y Configuración](#instalación-y-configuración)
6. [API REST - FastAPI](#api-rest---fastapi)
7. [Dashboard - Streamlit](#dashboard---streamlit)
8. [Visión Artificial - YOLOv8](#visión-artificial---yolov8)
9. [Base de Datos](#base-de-datos)
10. [Predicciones de Demanda](#predicciones-de-demanda)
11. [Ejecución del Proyecto](#ejecución-del-proyecto)
12. [Estado Actual](#estado-actual)

---

## Descripción del Proyecto

MarkeTTalento es un **sistema de inventario inteligente** diseñado para supermercados, que combina:

- **Gestión de inventario** en tiempo real
- **Visión artificial** para detección automática de productos (YOLOv8)
- **Predicciones de demanda** basadas en machine learning
- **Dashboard interactivo** con diseño futurista
- **API REST** completa para integración

El sistema permite:
- Registrar productos, categorías y proveedores
- Controlar el stock con alertas de nivel bajo
- Registrar ventas y trackear el historial
- Detectar productos en imágenes de estanterías
- Predecir cuándo se agotarán los productos

---

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────┐
│                        MarkeTTalento                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     │
│  │   Usuario    │     │   Usuario    │     │   Sistema    │     │
│  │  (Dashboard) │     │   (API)      │     │  Externo     │     │
│  │  :8501       │     │  :8002/docs  │     │  (YOLOv8)    │     │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘     │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              │                                   │
│                    ┌─────────▼─────────┐                         │
│                    │   API REST       │                         │
│                    │   FastAPI        │                         │
│                    │   Puerto 8002    │                         │
│                    └─────────┬─────────┘                         │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         │                    │                    │             │
│  ┌──────▼───────┐     ┌──────▼───────┐     ┌──────▼───────┐   │
│  │  Inventario  │     │   Predicción │     │    Visión    │   │
│  │  Servicio    │     │   Servicio   │     │   Servicio   │   │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘   │
│         │                    │                    │             │
│         └────────────────────┼────────────────────┘             │
│                              │                                   │
│                    ┌��────────▼─────────┐                         │
│                    │   Repositorios    │                         │
│                    │   (SQLAlchemy)    │                         │
│                    └─────────┬─────────┘                         │
│                              │                                   │
│                    ┌─────────▼─────────┐                         │
│                    │   SQLite DB       │                         │
│                    │   (Desarrollo)    │                         │
│                    └───────────────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tecnologías Utilizadas

| Componente | Tecnología | Versión | Propósito |
|------------|------------|---------|-----------|
| API REST | FastAPI | 0.100+ | Endpoints REST |
| Dashboard | Streamlit | 1.28+ | Interfaz web |
| Base de Datos | SQLite | - | Almacenamiento (dev) |
| ORM | SQLAlchemy | 2.0+ | Acceso a datos |
| Visión | Ultralytics YOLOv8 | 8.0+ | Detección objetos |
| Gráficos | Plotly | 5.18+ | Visualizaciones |
| Servidor API | Uvicorn | 0.23+ | ASGI server |

### Librerías Python Principales

```python
# Core
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0

# Dashboard
streamlit>=1.28.0
plotly>=5.18.0

# Base de datos
sqlalchemy>=2.0.0
sqlite3 (incluido en Python)

# Visión Artificial
ultralytics>=8.0.0
opencv-python>=4.8.0

# Utilidades
python-multipart>=0.0.6
python-dotenv>=1.0.0
```

---

## Estructura del Proyecto

```
MarkeTTalento/
│
├── 📄 main.py                    # Aplicación FastAPI (API REST)
├── 📄 streamlit_app.py          # Dashboard web (Streamlit)
├── 📄 iniciar.py                 # Launcher - Inicia todo el sistema
│
├── 📁 src/
│   ├── 📁 core/                  # Configuración central
│   │   ├── config.py             # Configuración (settings)
│   │   └── database.py           # Conexión a BD
│   │
│   ├── 📁 dominio/                # Entidades y contratos
│   │   ├── entidades.py          # Modelos de datos
│   │   └── repositorios.py        # Interfaces de repositorios
│   │
│   ├── 📁 aplicacion/             # Lógica de negocio
│   │   ├── schemas.py            # Schemas Pydantic
│   │   └── servicios/
│   │       ├── producto_servicio.py
│   │       ├── inventario_servicio.py
│   │       ├── prediccion_servicio.py
│   │       ├── vision_servicio.py
│   │       └── inventario_vision.py
│   │
│   └── 📁 infraestructura/        # Implementaciones
│       └── repositorios_impl.py  # Implementación SQLAlchemy
│
├── 📁 data/
│   └── markettalento.db          # Base de datos SQLite
│
├── 📁 temp/                       # Archivos temporales (YOLO)
│
├── 📄 .env                       # Variables de entorno
├── 📄 requirements.txt           # Dependencias Python
└── 📄 README.md                  # Documentación general
```

### Descripción de Módulos

#### 1. `main.py` - API REST
- **Responsabilidad**: Exponer todos los endpoints de la API
- **Puerto**: 8002
- **Documentación automática**: `/docs` (Swagger) y `/redoc` (ReDoc)

#### 2. `streamlit_app.py` - Dashboard
- **Responsabilidad**: Interfaz web interactiva
- **Puerto**: 8501
- **Tema**: Diseño futurista oscuro con acentos cyan/purple

#### 3. `iniciar.py` - Launcher
- **Responsabilidad**: Iniciar todos los servicios con un solo comando
- **Funciones**:
  - Verifica si la API ya está corriendo
  - Inicia FastAPI si es necesario
  - Inicia Streamlit si es necesario
  - Abre el navegador automáticamente

#### 4. `src/core/` - Configuración Central
- **config.py**: Settings de la aplicación (puerto, URL de BD)
- **database.py**: Inicialización de SQLAlchemy y sesión de BD

#### 5. `src/dominio/` - Capa de Dominio
- **entidades.py**: Modelos SQLAlchemy (Categoria, Proveedor, Producto, Inventario, Venta)
- **repositorios.py**: Interfaces abstractas para repositorios

#### 6. `src/aplicacion/` - Lógica de Negocio
- **schemas.py**: Modelos Pydantic para request/response
- **servicios/**: Lógica de negocio separada por dominio
  - `producto_servicio.py`: CRUD de productos
  - `inventario_servicio.py`: Control de stock y alertas
  - `prediccion_servicio.py`: Algoritmos de predicción de demanda
  - `vision_servicio.py`: Wrapper para YOLOv8
  - `inventario_vision.py`: Mapeo objetos detectados → productos BD

#### 7. `src/infraestructura/` - Implementación
- **repositorios_impl.py**: Implementación concreta de repositorios usando SQLAlchemy

---

## Instalación y Configuración

### Requisitos Previos

1. **Python 3.10+** instalado
2. **Git** (opcional)
3. **pip** actualizado

### Pasos de Instalación

```bash
# 1. Clonar o navegar al proyecto
cd MarkeTTalento

# 2. Crear entorno virtual (recomendado)
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
# Editar .env si es necesario
```

### Archivo `.env`

```env
DATABASE_URL=sqlite:///data/markettalento.db
API_PORT=8002
API_HOST=127.0.0.1
DEBUG=true
```

### Archivo `requirements.txt`

```
fastapi>=0.100.0
uvicorn>=0.23.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
streamlit>=1.28.0
plotly>=5.18.0
sqlalchemy>=2.0.0
python-multipart>=0.0.6
python-dotenv>=1.0.0
ultralytics>=8.0.0
opencv-python>=4.8.0
```

---

## API REST - FastAPI

### Información General

| Atributo | Valor |
|----------|-------|
| Título | MarkeTTalento API |
| Versión | 1.0.0 |
| Puerto | 8002 |
| Docs | http://localhost:8002/docs |
| ReDoc | http://localhost:8002/redoc |

### Endpoints Organizados por Tags

#### 📡 Sistema
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Página principal |
| GET | `/api/v1/salud` | Estado de salud del sistema |

#### 📁 Categorías
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/categorias` | Crear categoría |
| GET | `/api/v1/categorias` | Listar todas las categorías |

#### 🚚 Proveedores
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/proveedores` | Crear proveedor |
| GET | `/api/v1/proveedores` | Listar proveedores |

#### 📦 Productos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/productos` | Crear producto |
| GET | `/api/v1/productos` | Listar productos |
| GET | `/api/v1/productos/{id}` | Obtener producto por ID |
| GET | `/api/v1/productos/sku/{sku}` | Obtener por SKU |
| PUT | `/api/v1/productos/{id}` | Actualizar producto |
| DELETE | `/api/v1/productos/{id}` | Eliminar (soft delete) |

#### 📊 Inventario
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/inventario/{producto_id}` | Crear/actualizar stock |
| GET | `/api/v1/inventario` | Listar todo el inventario |
| GET | `/api/v1/inventario/bajo-stock` | Productos con stock bajo |
| GET | `/api/v1/inventario/resumen` | Resumen del inventario |
| GET | `/api/v1/inventario/recomendaciones` | Recomendaciones de reposición |

#### 💰 Ventas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/ventas` | Registrar venta |
| GET | `/api/v1/ventas` | Listar ventas |
| GET | `/api/v1/ventas/producto/{id}` | Ventas por producto |

#### 🔮 Predicciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/predicccion/{producto_id}` | Predicción para un producto |
| GET | `/api/v1/prediccion/todos` | Predicciones para todos |
| GET | `/api/v1/prediccion/semanal/{id}` | Pronóstico semanal |

#### 📸 Visión Artificial
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/vision/detectar` | Detectar objetos en imagen |
| POST | `/api/v1/vision/analizar-y-actualizar` | Detectar + actualizar stock |

#### 📈 Análisis
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/analisis/completo` | Análisis completo del sistema |

### Ejemplo de Uso

```bash
# Ver estado del sistema
curl http://localhost:8002/api/v1/salud

# Crear categoría
curl -X POST http://localhost:8002/api/v1/categorias \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Snacks", "descripcion": "Productos de snack"}'

# Listar productos
curl http://localhost:8002/api/v1/productos

# Crear producto
curl -X POST http://localhost:8002/api/v1/productos \
  -H "Content-Type: application/json" \
  -d '{
    "sku": "SNK001",
    "nombre": "Papas Fritas",
    "precio_venta": 2.50,
    "precio_coste": 1.20,
    "unidad": "paquete",
    "stock_minimo": 10,
    "stock_maximo": 50,
    "tiempo_reposicion": 3,
    "categoria_id": 1
  }'
```

---

## Dashboard - Streamlit

### Información General

| Atributo | Valor |
|----------|-------|
| Puerto | 8501 |
| URL Local | http://localhost:8501 |
| Tema | Futurista Oscuro |

### Secciones del Dashboard

#### 🏠 Dashboard
- **Métricas principales**:
  - Total de productos
  - Stock total
  - Productos críticos
  - Valor total del inventario
- **Gráfico donut**: Estado del inventario (crítico/bajo/adecuado)
- **Panel de alertas**: Productos que requieren atención
- **Recomendaciones**: Sugerencias de reposición

#### 📦 Productos
- **Vista de catálogo**: Cards visuales con información de cada producto
- **Formulario de creación**: Alta de nuevos productos
- **Campos**: SKU, nombre, precio, stock mínimo/máximo, categoría

#### 📊 Inventario
- **Vista de stock**: Cards con estado del inventario (CRÍTICO/BAJO/OK)
- **Indicadores visuales**: Color según nivel de stock
- **Formulario de actualización**: Modificar stock y ubicación

#### 💰 Ventas
- **Historial de ventas**: Cards con detalle de cada venta
- **Formulario de registro**: Registrar nueva venta
- **Cálculo automático**: Total basado en cantidad × precio

#### 🔮 Predicciones
- **Gráfico de barras**: Días hasta agotarse por producto
- **Estados**: CRÍTICO, BAJO, MODERADO, ADECUADO
- **Basado en**: Historial de ventas y consumo promedio

#### 📸 Visión AI
- **Subida de imagen**: Cargar foto de estantería
- **Detección YOLOv8**: Identifica objetos en la imagen
- **Mapeo a inventario**: Asigna objetos detectados a productos BD
- **Actualización automática**: Modifica stock según detección

### Diseño del Sidebar

```
┌────────────────────────┐
│     ⚡ Menú            │
├────────────────────────┤
│  ┌──────────────────┐  │
│  │ 🏠 Dashboard     │  │
│  └──────────────────┘  │
│  ┌──────────────��───┐  │
│  │ 📦 Productos      │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │ 📊 Inventario     │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │ 💰 Ventas        │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │ 🔮 Predicciones  │  │
│  └──────────────────┘  │
│  ┌──────────────────┐  │
│  │ 📸 Visión AI    │  │
│  └──────────────────┘  │
├────────────────────────┤
│  ┌──────────────────┐  │
│  │ 🟢 API Online    │  │
│  │    14:35:22      │  │
│  │  Lunes 28 Abr    │  │
│  └──────────────────┘  │
├────────────────────────┤
│  📊 Dashboard          │
│  📚 API Docs           │
├────────────────────────┤
│  ───────────────       │
└────────────────────────┘
```

### Colores del Tema

| Color | Hex | Uso |
|-------|-----|-----|
| Cyan | `#00f0ff` | Acentos principales, Dashboard |
| Purple | `#8b5cf6` | Productos, API Docs |
| Green | `#10b981` | Inventario, OK, éxito |
| Red | `#ef4444` | Crítico, errores |
| Orange | `#f59e0b` | Bajo stock, alertas |
| Pink | `#ec4899` | Predicciones |
| Blue | `#3b82f6` | Visión AI |

---

## Visión Artificial - YOLOv8

### Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Imagen de     │    │   YOLOv8        │    │   Resultados    │
│   Estantería    │───▶│   (COCO/Retail) │───▶│   Detección     │
└─────────���───────┘    └─────────────────┘    └─────────────────┘
                                                    │
                                                    ▼
                                            ┌─────────────────┐
                                            │   Mapeo a       │
                                            │   Productos BD  │
                                            └─────────────────┘
                                                    │
                                                    ▼
                                            ┌─────────────────┐
                                            │   Actualización │
                                            │   Inventario    │
                                            └─────────────────┘
```

### Modelos Soportados

1. **YOLOv8n** (nano) - Más rápido, menos preciso
2. **YOLOv8s** (small) - Equilibrado
3. **YOLOv8m** (medium) - Más preciso
4. **YOLOv8l** (large) - Alta precisión
5. **YOLOv8x** (xlarge) - Máxima precisión

### Clases COCO Detectadas

El modelo COCO detecta 80 clases incluyendo:
- Alimentos: banana, apple, sandwich, orange, broccoli, carrot, hotdog, pizza, donut, cake
- Bebidas: bottle, wine glass, cup, fork, knife, spoon, bowl
- Objetos: book, clock, vase, scissors, teddy bear, hair drier, toothbrush

### Mapeo de Objetos a Productos

```python
MAPA_YOLO_A_PRODUCTO = {
    "banana": {"producto_nombre": "Plátanos", "cantidad_por_defecto": 1},
    "bottle": {"producto_nombre": "Botella de Agua", "cantidad_por_defecto": 1},
    "cup": {"producto_nombre": "Vasos", "cantidad_por_defecto": 2},
    # ... más mapeos
}
```

### Endpoint de Detección

```bash
# Detectar objetos en imagen
curl -X POST http://localhost:8002/api/v1/vision/detectar \
  -F "archivo=@estanteria.jpg" \
  -F "confianza_min=0.15"

# Detectar y actualizar inventario
curl -X POST http://localhost:8002/api/v1/vision/analizar-y-actualizar \
  -F "archivo=@estanteria.jpg" \
  -F "confianza_min=0.15" \
  -F "actualizar_stock=true"
```

### Respuesta de Detección

```json
{
  "deteccion": {
    "total_objetos": 15,
    "objetos": [
      {"nombre": "bottle", "confianza": 0.87, "bbox": [x, y, w, h]},
      {"nombre": "cup", "confianza": 0.92, "bbox": [x, y, w, h]}
    ]
  },
  "mapeo": {
    "mapeados": [
      {"producto_nombre": "Botella de Agua", "cantidad_detectada": 3}
    ],
    "no_encontrados": [
      {"objeto": "orange", "cantidad": 2}
    ]
  },
  "actualizacion": {
    "total": 1,
    "actualizados": [
      {"producto": "Botella de Agua", "stock_anterior": 10, "stock_nuevo": 13}
    ]
  }
}
```

---

## Base de Datos

### Sistema de Gestión

- **Desarrollo**: SQLite (archivo local)
- **Producción**: Listo para PostgreSQL/MySQL

### Entidades

#### Categoria
```python
class Categoria(Base):
    id: int
    nombre: str
    descripcion: str
    activo: bool
    fecha_creacion: datetime
```

#### Proveedor
```python
class Proveedor(Base):
    id: int
    nombre: str
    contacto: str
    email: str
    activo: bool
    fecha_creacion: datetime
```

#### Producto
```python
class Producto(Base):
    id: int
    sku: str  # Código único
    nombre: str
    descripcion: str
    precio_venta: float
    precio_coste: float
    unidad: str  # unidad, kg, litro, paquete, caja, botella
    stock_minimo: int
    stock_maximo: int
    tiempo_reposicion: int  # días
    categoria_id: int
    activo: bool
    fecha_creacion: datetime
```

#### Inventario
```python
class Inventario(Base):
    id: int
    producto_id: int
    cantidad: int
    ubicacion: str
    fecha_ultima_actualizacion: datetime
```

#### Venta
```python
class Venta(Base):
    id: int
    producto_id: int
    cantidad: int
    precio_unitario: float
    tipo_operacion: str  # venta, devolucion
    fecha: datetime
```

### Ubicación de la Base de Datos

```
data/markettalento.db
```

---

## Predicciones de Demanda

### Algoritmo de Predicción

1. **Recopilación de datos**: Historial de ventas del producto
2. **Cálculo de consumo promedio**: Unidades vendidas / días
3. **Predicción de agotamiento**: Stock actual / consumo promedio
4. **Clasificación del estado**:
   - CRÍTICO: ≤3 días
   - BAJO: ≤7 días
   - MODERADO: ≤14 días
   - ADECUADO: >14 días

### Fórmula

```
dias_hasta_agotarse = stock_actual / consumo_promedio_diario

consumo_promedio_diario = suma(cantidades_vendidas) / dias_desde_primera_venta
```

### Consideraciones

- Si no hay historial de ventas, usa tiempo de reposición como estimado
- El stock mínimo se usa como umbral de alerta
- Las predicciones se actualizan en tiempo real con cada venta

---

## Ejecución del Proyecto

### Método 1: Launcher (Recomendado)

```bash
python iniciar.py
```

Esto automáticamente:
1. Verifica si la API está corriendo
2. Inicia FastAPI en puerto 8002
3. Inicia Streamlit en puerto 8501
4. Abre el navegador con ambas interfaces

### Método 2: Manual

```bash
# Terminal 1: API
python main.py

# Terminal 2: Dashboard
streamlit run streamlit_app.py
```

### Acceso a Interfaces

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Dashboard | http://localhost:8501 | Interfaz web principal |
| API Docs | http://localhost:8002/docs | Documentación Swagger |
| API Redoc | http://localhost:8002/redoc | Documentación ReDoc |
| API Base | http://localhost:8002 | Raíz de la API |

### Comprobar Estado

```bash
# Verificar API
curl http://localhost:8002/api/v1/salud

# Verificar respuesta esperada
{
  "estado": "saludable",
  "timestamp": "2026-04-28T...",
  "servicios": ["FastAPI", "SQLite", "YOLOv8"]
}
```

---

## Estado Actual

### ✅ Completado

- [x] Arquitectura Clean Architecture
- [x] API REST con FastAPI (26+ endpoints)
- [x] Dashboard interactivo con Streamlit
- [x] Diseño futurista con tema oscuro
- [x] Integración con YOLOv8 para visión artificial
- [x] Sistema de predicción de demanda
- [x] Base de datos SQLite
- [x] Launcher para ejecución simple
- [x] Documentación de API con tags
- [x] Sidebar con navegación por botones
- [x] Reloj en tiempo real en sidebar
- [x] Estado de API en tiempo real
- [x] Cards visuales para productos, inventario y ventas
- [x] Gráficos con Plotly

### 🔄 En Desarrollo

- [ ] Más mapeos de objetos YOLO → productos
- [ ] Modelo YOLO personalizado entrenado
- [ ] Autenticación de usuarios
- [ ] Tests automatizados
- [ ] Despliegue con Docker

### 📋 Pendientes

- [ ] Integración con PostgreSQL (producción)
- [ ] Notificaciones push
- [ ] App móvil
- [ ] Dashboard de administración

---

## Notas de Desarrollo

### Deprecation Warnings

El código ya incluye correcciones para:
- `datetime.utcnow()` → `datetime.now(timezone.utc)`
- `use_container_width` → `width='stretch'`
- `on_event("startup")` → lifespan handlers (pendiente refactorizar)

### Limitaciones Conocidas

1. **YOLOv8 COCO**: El modelo genérico puede no detectar todos los productos específicos del supermercado
2. **SQLite**: Adecuado para desarrollo, usar PostgreSQL para producción
3. **Sin autenticación**: El sistema está abierto actualmente
4. **Web scraping**: Los sitios como Mercadona pueden bloquear el scraping

### Próximos Pasos Recomendados

1. Entrenar modelo YOLO personalizado con fotos del supermercado
2. Implementar autenticación JWT
3. Configurar Docker para despliegue
4. Agregar tests con pytest
5. Migrar a PostgreSQL para producción

---

## Licencia

Este proyecto es de código abierto y está disponible para uso educativo y comercial.

---

## Contacto y Soporte

Para reportar problemas o solicitar mejoras, crear un issue en el repositorio del proyecto.

---

*Documentación actualizada: Abril 2026*
*Versión: 1.0.0*