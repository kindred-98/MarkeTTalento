# MarkeTTalento - Sistema de Inventario Inteligente

## 📋 Resumen

Sistema de gestión de inventario con **Visión Artificial** y **Machine Learning** para prediction de demanda en retail.

---

## ✅ Lo que está funcionando

| Componente | Estado | Descripción |
|------------|--------|-------------|
| **API REST** | ✅ | FastAPI con 20+ endpoints |
| **Base de Datos** | ✅ | SQLite en `data/markettalento.db` |
| **Dashboard** | ✅ | Streamlit con gráficos Plotly |
| **Entidades BD** | ✅ | 5 tablas (productos, categorias, ventas, inventario, proveedores) |
| **YOLOv8** | ✅ | Detección de objetos en imágenes (modelo genérico COCO) |
| **Datos Ejemplo** | ✅ | 11 productos cargados |

---

## 🚧 Lo que falta

| Componente | Prioridad | Estado |
|------------|----------|--------|
| **Modelo Retail** | Alta | Solo genérico COCO (80 clases) |
| **Mapear productos detectados → BD** | Alta | No implementado |
| **Predicciones ML** | Media | Básico (promedio simple) |
| **Autenticación** | Media | No |
| **Tests** | Baja | No |
| **Docker** | Baja | No |

---

## 📂 Estructura del Proyecto

```
MarkeTTalento/
├── main.py              # API FastAPI
├── streamlit_app.py     # Dashboard
├── .env                 # Configuración
├── requirements.txt     # Dependencias
├── data/                # SQLite
│   └── markettalento.db
├── models/             # Modelos ML (vacío)
├── scripts/            # Utilidades
│   ├── crear_datos.py
│   └── probar_vision.py
└── src/                # Código fuente
    ├── core/           # Config, BD
    ├── dominio/        # Entidades, Repositorios
    ├── aplicacion/     # Servicios, Schemas
    └── infraestructura/ # API, Implementaciones
```

---

## 🎯 Cómo usar

### 1. Iniciar API
```bash
python main.py
```
API: http://localhost:8002

### 2. Iniciar Dashboard
```bash
streamlit run streamlit_app.py
```
Dashboard: http://localhost:8501

### 3. Detectar productos en imagen
```bash
python scripts/probar_vision.py
```

---

## 📊 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/api/v1/salud` | Estado del sistema |
| GET | `/api/v1/productos` | Listar productos |
| POST | `/api/v1/productos` | Crear producto |
| POST | `/api/v1/ventas` | Registrar venta |
| GET | `/api/v1/inventario/resumen` | Resumen inventario |
| GET | `/api/v1/prediccion/todos` | Predicciones demanda |
| POST | `/api/v1/vision/detectar` | Detectar en imagen |

---

## 🔮 Visión Artificial

**Modelo actual**: YOLOv8n (COCO - 80 clases)

**Qué detecta**: bottle, cup, food, fruit, person, etc.

**Limitación**: No detecta productos específicos de supermarket (papitas, galletas, refrescos, etc.)

### Para mejorar:
1. **Entrenar modelo propio** con fotos de tus productos
2. **Usar modelo pre-entrenado de retail** (requiere configuración adicional)

---

## 📈 Estado del Proyecto

```
███████████████░░░░  70% Completado
```

- ✅ Core funcional (API + BD + Dashboard)
- ⚠️ Visión básica (detecta objetos genéricos)
- ❌ Mapping productos → inventario
- ❌ ML avanzado

---

## 👤 Autor

Proyecto sviluppado como parte del curso de MarkeTTalento

---

## 📝 Notas

- Base de datos en `data/markettalento.db`
- Puerto API: 8002 (configurable en .env)
- Puerto Dashboard: 8501
- Configuración en `.env`