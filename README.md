# MarkeTTalento - Sistema de Inventario Inteligente

Sistema de análisis de inventario con **Visión Artificial** y **Machine Learning** para prediction de demanda en retail.

## Stack Tecnológico

| Capa | Tecnología |
|------|------------|
| Backend | FastAPI (Python 3.10+) |
| Frontend | Streamlit |
| Base de Datos | PostgreSQL |
| Visión Artificial | YOLOv8 (Ultralytics) |
| ML | Scikit-learn |

## Estructura del Proyecto

```
MarkeTTalento/
├── src/
│   ├── core/                      # Configuración centralizada
│   │   ├── config/                # Variables de entorno, settings
│   │   ├── database/              # Conexión a PostgreSQL, sesiones
│   │   └── utils/                 # Utilidades comunes
│   │
│   ├── dominio/                   # Negocio puro (sin dependencias)
│   │   ├── entidades/             # Modelos de dominio (Producto, Venta, etc)
│   │   └── repositorios/          # Interfaces abstractas de acceso a datos
│   │
│   ├── aplicacion/                # Casos de uso
│   │   ├── servicios/             # Lógica de negocio
│   │   └── schemas/               # DTOs/pydantic models
│   │
│   └── infraestructura/           # Implementaciones concretas
│       ├── api/                   # Endpoints FastAPI
│       ├── vision/                # YOLOv8 integration
│       └── ml/                    # Modelos de ML
│
├── tests/
│   ├── unitarios/                 # Tests de funciones unitarias
│   └── integracion/               # Tests de integración API
│
├── notebooks/                     # Jupyter notebooks (exploración ML)
├── dokumentacion/                 # Documentación del proyecto
└── resources/
    ├── modelos/                   # Modelos YOLOv8 descargados
    └── imagenes/                  # Imágenes de prueba
```

## Arquitectura (Clean Architecture)

```
                    ┌────────────────────────┐
                    │   presentation         │
                    │   (FastAPI + Streamlit)│
                    └──────────┬─────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   aplicacion        │
                    │   (servicios)       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │   dominio           │
                    │   (entidades)       │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  infraestructura    │
                    │  (BD, Vision, ML)   │
                    └─────────────────────┘
```

## Primeros Pasos

### 1. Crear entorno virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno
Crear archivo `.env`:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/inventario
YOLO_MODEL=scratch  # o ruta a modelo entrenado
LOG_LEVEL=INFO
```

### 4. Ejecutar
```bash
# Backend API
uvicorn src.infraestructura.api.main:app --reload

# Frontend Streamlit
streamlit run src/infraestructura/api/streamlit_app.py
```

## Endpoints API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/salud` | Estado del sistema |
| GET | `/api/v1/productos` | Listar productos |
| POST | `/api/v1/productos` | Crear producto |
| POST | `/api/v1/analisis/imagen` | Analizar imagen de estantería |
| GET | `/api/v1/pronostico/{producto_id}` | Pronóstico de demanda |

## Licencia

MIT