<div align="center">

# MarkeTTalento - Sistema de Inventario Inteligente


  <img src="https://img.shields.io/python/3.10+-blue?style=for-the-badge" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/FastAPI-0.100+-00a859?style=for-the-badge" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge" alt="Streamlit">
  <img src="https://img.shields.io/badge/YOLOv8-8.0+-9cf?style=for-the-badge" alt="YOLOv8">
  <img src="https://img.shields.io/badge/SQLite-003b27?style=for-the-badge" alt="SQLite">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License MIT">
</div>

---

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
11. [Inventario](#inventario)
12. [Ejecución del Proyecto](#ejecución-del-proyecto)
13. [Estado Actual](#estado-actual)

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
┌──────────────────────────────────────────────────────────────────┐
│                        MarkeTTalento                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐      │
│  │   Usuario    │     │   Usuario    │     │   Sistema    │      │
│  │  (Dashboard) │     │   (API)      │     │  Externo     │      │
│  │  :8501       │     │  :8002/docs  │     │  (YOLOv8)    │      │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘      │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              │                                   │
│                    ┌─────────▼─────────┐                         │
│                    │   API REST       │                          │
│                    │   FastAPI        │                          │
│                    │   Puerto 8002    │                          │
│                    └─────────┬─────────┘                         │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐              │
│         │                    │                    │              │
│  ┌──────▼───────┐     ┌──────▼───────┐     ┌──────▼───────┐      │
│  │  Inventario  │     │   Predicción │     │    Visión    │      │
│  │  Servicio    │     │   Servicio   │     │   Servicio   │      │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘      │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              │                                   │
│                    ┌─────────▼─────────┐                         │
│                    │   Repositorios  │                           │
│                    │   (SQLAlchemy)  │                           │
│                    └─────────┬─────────┘                         │
│                              │                                   │
│                    ┌─────────▼─────────┐                         │
│                    │   SQLite DB       │                         │
│                    │   (Desarrollo)    │                         │
│                    └───────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘
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
├── main.py                           # Aplicación FastAPI (API REST)
├── run.py                            # Launcher - Inicia todo el sistema
│ 
├── src/
│   ├── api/                          # Endpoints de la API
│   │   ├── productos.py
│   │   ├── inventario.py
│   │   ├── ventas.py
│   │   ├── categorias.py
│   │   ├── proveedores.py
│   │   ├── predicciones.py
│   │   ├── vision.py
│   │   ├── sistema.py
│   │   └── router.py
│   │
│   ├── core/                         # Configuración central
│   │   ���─�� config.py
│   │   └── errors.py
│   │
│   ├── implementaciones/             # Implementaciones concretas
│   │   └── repositorios_impl.py
│   │
├── app/
│   ├── main.py                       # Dashboard Streamlit
│   └── styles/                       # Estilos CSS
│
├── data/
│   └── markettalento.db              # Base de datos SQLite
│
├── docs/   
│   └── productos/                    # Imágenes de productos
│
├── tests/                            # Tests automatizados
│   ├── test_validators.py
│   ├── test_inventario_logic.py
│   ├── test_api.py
│   ├── test_producto_logic.py
│   ├── test_venta_logic.py
│   └── test_helpers.py
│
├── logs/                              # Logs de aplicación
├── scripts/                           # Scripts auxiliares
│
├── .env                               # Variables de entorno
├── requirements.txt                   # Dependencias Python
└── README.md                          # Documentación
``` 

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

#### Sistema
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Página principal |
| GET | `/api/v1/salud` | Estado de salud del sistema |

#### Categorías
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/categorias` | Crear categoría |
| GET | `/api/v1/categorias` | Listar todas las categorías |
| GET | `/api/v1/categorias/{id}` | Obtener categoría por ID |
| PUT | `/api/v1/categorias/{id}` | Actualizar categoría |
| DELETE | `/api/v1/categorias/{id}` | Eliminar categoría |

#### Proveedores
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/proveedores` | Crear proveedor |
| GET | `/api/v1/proveedores` | Listar proveedores |
| GET | `/api/v1/proveedores/{id}` | Obtener proveedor por ID |
| PUT | `/api/v1/proveedores/{id}` | Actualizar proveedor |
| DELETE | `/api/v1/proveedores/{id}` | Eliminar proveedor |

#### Productos
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/productos` | Crear producto |
| GET | `/api/v1/productos` | Listar productos |
| GET | `/api/v1/productos/{id}` | Obtener producto por ID |
| GET | `/api/v1/productos/sku/{sku}` | Obtener por SKU |
| PUT | `/api/v1/productos/{id}` | Actualizar producto |
| DELETE | `/api/v1/productos/{id}` | Eliminar (soft delete) |

#### Inventario
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/inventario/{producto_id}` | Crear/actualizar stock |
| GET | `/api/v1/inventario` | Listar todo el inventario |
| GET | `/api/v1/inventario/bajo-stock` | Productos con stock bajo |
| GET | `/api/v1/inventario/resumen` | Resumen del inventario |
| GET | `/api/v1/inventario/recomendaciones` | Recomendaciones de reposición |

#### Ventas
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/ventas` | Registrar venta |
| GET | `/api/v1/ventas` | Listar ventas |
| GET | `/api/v1/ventas/producto/{id}` | Ventas por producto |

#### Predicciones
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/predicccion/{producto_id}` | Predicción para un producto |
| GET | `/api/v1/prediccion/todos` | Predicciones para todos |
| GET | `/api/v1/prediccion/semanal/{id}` | Pronóstico semanal |

#### Visión Artificial
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/api/v1/vision/detectar` | Detectar objetos en imagen |
| POST | `/api/v1/vision/analizar-y-actualizar` | Detectar + actualizar stock |

#### Análisis
| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/analisis/completo` | Análisis completo del sistema |

---

## Dashboard - Streamlit

### Información General

| Atributo | Valor |
|----------|-------|
| Puerto | 8501 |
| URL Local | http://localhost:8501 |
| Tema | Futurista Oscuro |

### Sidebar - Navegación

El sidebar contiene:
- 🕐 Reloj en tiempo real
- 🔌 Estado de conexión con la API
- 🔗 Enlaces rápidos a Dashboard y API Docs

### Secciones del Dashboard

| Sección | Estado | Descripción |
|---------|--------|-------------|
| 🏠 Dashboard | ✅ LISTO | Métricas, gráficos, alertas, recomendaciones |
| 📦 Productos | ✅ LISTO | Catálogo, creación, edición de productos |
| 📊 Inventario | ✅ LISTO | Stock, alertas, filtros, exportación |
| 💰 Ventas | 🔄 EN PROCESO | Registro de ventas - en desarrollo |
| 🔮 Predicciones | 🔄 EN PROCESO | Predicción de demanda - en pruebas |
| 📸 Visión AI | 🔄 EN PROCESO | Detección YOLOv8 - en pruebas |

---

## Visión Artificial - YOLOv8

### Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Imagen de     │    │   YOLOv8        │    │   Resultados    │
│   Estantería    │───▶│   (COCO/Retail) │───▶│   Detección     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
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
    sku: str
    nombre: str
    descripcion: str
    precio_venta: float
    precio_coste: float
    unidad: str
    stock_minimo: int
    stock_maximo: int
    tiempo_reposicion: int
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
    tipo_operacion: str
    fecha: datetime
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

---

## Inventario

### Funcionalidades Completadas

El módulo de inventario está **100% completo** con las siguientes características:

- ✅ 4 tarjetas por fila con información completa del producto
- ✅ Barra de progreso visual del stock (colores según nivel)
- ✅ Precios destacados (coste, venta, ganancia)
- ✅ Paginación (8 productos por página)
- ✅ Filtros por búsqueda, estado y ordenamiento
- ✅ Exportación a Excel y JSON con todos los campos
- ✅ Edición inline de SKU y Proveedor
- ✅ Validaciones en tiempo real (longitud, duplicados)
- ✅ Creación de nuevos proveedores (con validación de email)
- ✅ Confirmación explícita antes de guardar cambios
- ✅ Mensajes de error claros y amigables
- ✅ Auto-scroll al formulario de edición
- ✅ Indicador visual de tarjeta en edición
- ✅ Spinner de carga durante operaciones
- ✅ Botón "Volver arriba" para navegación fácil
- ✅ 145 tests automatizados implementados

### Tests de Cobertura

| Área | Tests Implementados | Estado |
|------|---------------------|--------|
| **Validaciones** | 27 ✅ | **COMPLETO** |
| **Lógica inventario** | 27 ✅ | **COMPLETO** |
| **API HTTP** | 24 ✅ | **COMPLETO** |
| **Integración** | 67 ✅ | **YA EXISTÍAN** |
| **TOTAL** | **145 tests** | 🎉 **100% COMPLETO** |

---

## Ejecución del Proyecto

### Launcher (Recomendado)

```bash
python run.py
```

Esto automáticamente:
1. Verifica si la API está corriendo
2. Inicia FastAPI en puerto 8002
3. Inicia Streamlit en puerto 8501
4. Abre el navegador con ambas interfaces

### Acceso a Interfaces

| Servicio | URL | Descripción |
|----------|-----|-------------|
| Dashboard | http://localhost:8501 | Interfaz web principal |
| API Docs | http://localhost:8002/docs | Documentación Swagger |
| API Redoc | http://localhost:8002/redoc | Documentación ReDoc |
| API Base | http://localhost:8002 | Raíz de la API |

---

## Estado Actual

### ✅ Completado (Producción)

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| 🏠 Dashboard | ✅ LISTO | Métricas, gráficos, alertas, recomendaciones |
| 📦 Productos | ✅ LISTO | CRUD completo, CRUD categorías y proveedores |
| 📊 Inventario | ✅ LISTO | Control stock, alertas, paginación, filtros, 145 tests |

### 🔄 En Desarrollo (No listo para producción)

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| 💰 Ventas | 🔄 EN PROCESO | Registro de ventas - en proceso de ajustes |
| 🔮 Predicciones | 🔄 EN PROCESO | Algoritmo base implementado - necesita refinamiento |
| 📸 Visión AI | 🔄 EN PROCESO | Integración YOLOv8 - en etapa de pruebas |

### 📋 Pendientes

| Módulo | Descripción |
|--------|-------------|
| 📱 App Móvil | Aplicación móvil paraAndroid/iOS |
| 🔐 Autenticación | Sistema de login y usuarios |
| 🐳 Docker | Contenedores para despliegue |
| 📊 PostgreSQL | Migración a base de datos producción |
| 📢 Notificaciones | Alertas push |
| 🧾 Facturación | Módulo de facturación |
| 📦 Cajas | Control de cajas y movimientos |

---

## Licencia

Este proyecto es de código abierto y está disponible para uso educativo y comercial.

---

## Contacto y Soporte

Para reportar problemas o solicitar mejoras, crear un issue en el repositorio del proyecto.

---

*Documentación actualizada: Mayo 2026*
*Versión: 1.0.0*