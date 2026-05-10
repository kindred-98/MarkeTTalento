# Arquitectura del Proyecto MarkeTTalento

## 8.1 — Estructura de docs/

Esta documentación forma parte del proceso de refactorización del código heredado de MarkeTTalento, aplicando el principio SRP (Single Responsibility Principle).

---

## Arquitectura Original (Monolito)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         EndPoint_Api.py / InventarioAlfa.py            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │     BASE     │  │    VISIÓN    │  │   LÓGICA    │                    │
│  │   DE DATOS   │  │  ARTIFICIAL  │  │   DE NEGOCIO│                    │
│  │              │  │              │  │              │                  │
│  │ • product_   │  │ • detect_   │  │ • calculate │                     │
│  │   database   │  │   products()│  │   _inventory│                    │
│  │ • get_prod_  │  │ • escenarios│  │   _metrics()│                    │
│  │   info()     │  │   simulados │  │ • predict_  │                  │
│  │ • get_all_   │  │              │  │   stock_    │                  │
│  │   products() │  │              │  │   outage()  │                  │
│  └──────────────┘  └──────────────┘  └──────────────┘                  │
│         │                  │                  │                         │
│         └──────────────────┼──────────────────┘                        │
│                            ▼                                           │
│                    ┌──────────────┐                                     │
│                    │     API     │                                     │
│                    │   FLASK     │                                     │
│                    │   ROUTES    │                                     │
│                    │              │                                     │
│                    │ • /api/test │                                     │
│                    │ • /api/     │                                     │
│                    │   analizar  │                                     │
│                    │ • /api/     │                                     │
│                    │   productos │                                     │
│                    └──────────────┘                                     │
│                            │                                           │
│                            ▼                                           │
│                    ┌──────────────┐                                     │
│                    │   INTERFAZ   │                                     │
│                    │    HTML     │                                     │
│                    │  EMBEBIDA   │                                     │
│                    │              │                                     │
│                    │ • HTML      │                                     │
│                    │   TEMPLATE  │                                     │
│                    │ • CSS en    │                                     │
│                    │   línea     │                                     │
│                    │ • JS embeb. │                                     │
│                    └──────────────┘                                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

PROBLEMAS DETECTADOS:
❌ Un solo archivo de ~500 líneas hace TODO
❌ Base de datos mezclada con lógica de negocio
❌ Interfaz HTML dentro del código Python
❌ Si cambias la BD, tocas todo el archivo
❌ Imposible testar componentes individualmente
❌ Código spaghetti: difícil de mantener
```

---

## Arquitectura Modular SRP (Resultado Final)

```
markettalento/
├── .github/workflows/ci.yml          ← Pipeline CI/CD (matriz Python 3.9-3.12)
│
├── src/                              ← Código fuente modularizado
│   ├── core/                        ← Configuración centralizada
│   │   ├── config/                 ← Environments, settings
│   │   ├── database/               ← SQLAlchemy, multi-database
│   │   ├── logging.py              ← Sistema de logs
│   │   └── errors.py               ← Manejo de errores
│   │
│   ├── dominio/                    ← Reglas de negocio puras
│   │   ├── entidades/              ← Entidades del dominio
│   │   └── repositorios/            ← Interfaces de repositorios
│   │
│   ├── aplicacion/                  ← Casos de uso y servicios
│   │   ├── servicios/              ← Lógica de aplicación
│   │   │   ├── producto_servicio.py
│   │   │   ├── inventario_servicio.py
│   │   │   ├── vision_servicio.py  ← Visión artificial
│   │   │   ├── prediccion_servicio.py ← Predicción de stock
│   │   │   └── inventario_vision.py
│   │   └── schemas/                ← Schemas de validación (Pydantic)
│   │
│   └── api/                         ← Endpoints HTTP
│       ├── router.py               ← Router principal
│       ├── productos.py            ← CRUD productos
│       ├── inventario.py           ← Gestión inventario
│       ├── ventas.py               ← Control de ventas
│       ├── vision.py               ← Detección de productos
│       └── predicciones.py         ← Predicciones
│
├── app/                             ← Interfaz Streamlit
│   ├── views/                       ← Vistas de la aplicación
│   │   ├── dashboard.py
│   │   ├── productos.py
│   │   ├── inventario.py
│   │   ├── ventas.py
│   │   ├── vision_ai.py
│   │   └── ...
│   ├── logic/                      ← Lógica de presentación
│   │   ├── producto.py
│   │   ├── inventario.py
│   │   └── venta.py
│   ├── components/                 ← Componentes reutilizables
│   ├── utils/                      ← Utilidades (API, validators, helpers)
│   ├── styles/                     ← CSS modularizado
│   └── config.py                   ← Configuración de la app
│
├── tests/                           ← Suite de tests (pytest)
│   ├── test_producto_logic.py
│   ├── test_inventario_logic.py
│   ├── test_venta_logic.py
│   ├── test_validators.py
│   ├── test_helpers.py
│   ├── test_api.py
│   └── conftest.py
│
├── docs/                            ← Documentación
│   ├── arquitectura.md             ← Este archivo
│   ├── Final.md                    ← Memoria final
│   └── Tecnologia_Del_Proyecto.md  ← Tech stack
│
├── requirements.txt                ← Dependencias del proyecto
├── run.py                          ← Punto de entrada
└── main.py                         ← Punto de entrada alternativo
```

---

## Descripción de Módulos y Responsabilidades

### Capa de Datos (`services/database/` o `src/core/database/`)

| Módulo | Única Responsabilidad | Descripción |
|--------|---------------------|-------------|
| `product_db.py` | Almacenar datos de productos | Dict con los 25 productos de MarkeTTalento organizados en 5 categorías (Refrigerados, Conservas, Bebidas, Panadería, Despensa). type hints explícitos. |
| `db_reader.py` | Leer datos de la base de datos | Funciones puras: `get_product_info()`, `get_all_products()`, `get_sales_history()`. No contiene lógica de negocio. |

**Por qué no se mezcla:** Separar la persistencia permite cambiar la fuente de datos (JSON, SQLite, PostgreSQL) sin tocar la lógica de negocio. Facilita los tests con datos mock.

---

### Capa de Visión Artificial (`services/vision/` o `src/aplicacion/servicios/vision_servicio.py`)

| Módulo | Única Responsabilidad | Descripción |
|--------|---------------------|-------------|
| `detector.py` | Detectar productos en imágenes | Función `detect_products()` que usa YOLO (ultralytics) para analizar imágenes. Devuelve lista de productos detectados con cantidad y confianza. |

**Por qué no se mezcla:** La detección de objetos es una responsabilidad distinta al análisis de inventario. Si mañana se cambia de YOLO a otro modelo, solo se modifica este módulo.

---

### Capa de Servicios de Inventario (`services/inventory/` o `src/aplicacion/servicios/`)

| Módulo | Única Responsabilidad | Descripción |
|--------|---------------------|-------------|
| `recommender.py` | Generar recomendaciones de reposición | Funciones: `calculate_inventory_metrics()`, `generate_recommendations()`, `calculate_inventory_value()`. Analiza el stock y genera alertas. |
| `stock_predictor.py` | Predecir cuándo se agotará el stock | Función `predict_stock_outage()` que usa el historial de ventas para estimar días hasta agotamiento y cantidad recomendada. |

**Por qué no se mezcla:** "Calcular métricas" y "Predecir demanda" son responsabilidades diferentes. El primero analiza el presente; el segundo proyecta el futuro. Cada uno evoluciona independientemente.

---

### Capa de Interfaz (`interface/` o `app/`)

| Módulo | Única Responsabilidad | Descripción |
|--------|---------------------|-------------|
| `demoStreamlit.py` | Presentar datos al usuario | Dashboard interactivo con Streamlit. Importa exclusivamente de `services/`. No contiene lógica de negocio. Secciones: Métricas (st.metric), Tabla (st.dataframe), Recomendaciones, Valor del Inventario. |

**Por qué no se mezcla:** La interfaz es solo una capa de presentación. No debe contener lógica de negocio. Si demain se reemplaza Streamlit por FastAPI + React, solo cambia esta capa.

---

### Pipeline CI/CD (`.github/workflows/ci.yml`)

| Módulo | Única Responsabilidad | Descripción |
|--------|---------------------|-------------|
| `ci.yml` | Validar el código en múltiples versiones | Ejecución de tests en Python 3.9, 3.10, 3.11, 3.12 usando `strategy.matrix`. `fail-fast: false` para ver resultados completos. |

---

## Beneficios de la Arquitectura SRP

1. **Mantenibilidad:** Cada módulo se puede modificar independientemente.
2. **Testabilidad:** Cada componente se testa de forma aislada con mocks.
3. **Reusabilidad:** Los servicios se pueden importar en diferentes interfaces (Flask, Streamlit, API REST).
4. **Legibilidad:** Archivos pequeños (30-50 líneas) son más fáciles de entender que uno de 500.
5. **Colaboración:** Diferentes desarrolladores pueden trabajar en módulos distintos sin conflictos.