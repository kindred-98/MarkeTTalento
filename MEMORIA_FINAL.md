# Memoria Final del Proyecto MarkeTTalento

## Refactorización, SRP, Streamlit y CI/CD con Python e IA

---

## 1. Introducción

### 1.1 Contexto del Proyecto

MarkeTTalento es un sistema de inventario inteligente que utiliza visión artificial y predicción de demanda para gestionar el stock de una empresa con 25 productos organizados en 5 categorías. Este proyecto fue desarrollado como ejercicio individual del **Módulo 4 - Refactorización SRP, Streamlit y CI/CD Matricial** de la formación de Dicampus (Fundación Dicampus - Inclusión Socio-Laboral).

### 1.2 Objetivos del Ejercicio

1. Analizar y documentar los problemas de diseño del código heredado
2. Aplicar el principio SRP (Single Responsibility Principle) refactorizando el código en módulos separados
3. Implementar una suite de tests unitarios con pytest
4. Configurar un pipeline CI/CD con matriz de versiones Python
5. Crear una interfaz de usuario con Streamlit
6. Documentar todo el proceso de refactorización

### 1.3 Archivos Heredados

Los archivos proporcionados como punto de partida fueron:

- **InventarioAlfa.py**: Aplicación Flask monolítica de 436 líneas
- **EndPoint_Api.py**: Aplicación Flask monolítica de 498 líneas

Ambos archivos contienen una implementación completa que mezcla todas las responsabilidades en un único archivo, violando flagrantemente el principio SRP.

---

## 2. Análisis del Código Heredado

### 2.1 Estructura Original Identificada

Los archivos heredados presentan la siguiente estructura monolitica:

```
EndPoint_Api.py / InventarioAlfa.py (~500 líneas)
├── Base de datos simulada (product_database dict)
├── Funciones de acceso a datos (get_product_info, get_all_products)
├── Servicio de visión artificial (detect_products)
├── Servicio de inventario (calculate_inventory_metrics, generate_recommendations)
├── Servicio de predicción (predict_stock_outage)
├── Template HTML embebido (130+ líneas)
├── Rutas de Flask (@app.route)
└── Ejecución (if __name__ == '__main__')
```

### 2.2 Violaciones del SRP Identificadas

#### 2.2.1 Mezcla de Responsabilidades

El archivo original realiza las siguientes tareas:

| Responsabilidad | Función对应的 |
|----------------|----------------|
| Almacenamiento de datos | `product_database` dict |
| Acceso a datos | `get_product_info()`, `get_all_products()` |
| Visión artificial | `detect_products()` |
| Lógica de inventario | `calculate_inventory_metrics()`, `generate_recommendations()` |
| Predicción de demanda | `predict_stock_outage()` |
| Cálculo de valor | `calculate_inventory_value()` |
| Interfaz HTTP | Decoradores `@app.route()` |
| Presentación HTML | `HTML_TEMPLATE` |
| Renderizado | `render_template_string()` |

**Total: 9 responsabilidades en un solo archivo**

#### 2.2.2 Problemas Técnicos Identificados

1. **Imposibilidad de testeo unitario**: No se puede probar `detect_products()` de forma aislada
2. **Acoplamiento fuerte**: Cambiar la base de datos requiere modificar todo el archivo
3. **Duplicación de código**: Lógica de inventario y predicción mezcladas en las rutas
4. **HTML embebido**: 130+ líneas de HTML dentro de Python, imposible de mantener
5. **Sin type hints**: Código sin anotaciones de tipo
6. **Sin documentación**: Funciones sin docstrings
7. **Visión artificial simulada**: Solo devuelve datos hardcoded, no analiza imágenes reales

---

## 3. Solución Implementada

### 3.1 Arquitectura Modular SRP

La refactorización siguió el principio SRP strict, separando cada responsabilidad en su propio módulo:

```
markettalento/
├── .github/workflows/ci.yml          # Pipeline CI/CD
├── src/
│   ├── core/                         # Configuración centralizada
│   │   ├── config/                  # Environments y settings
│   │   ├── database/               # SQLAlchemy
│   │   ├── logging.py
│   │   └── errors.py
│   ├── dominio/                     # Reglas de negocio puras
│   │   ├── entidades/
│   │   └── repositorios/
│   ├── aplicacion/                  # Casos de uso
│   │   ├── servicios/
│   │   │   ├── producto_servicio.py
│   │   │   ├── inventario_servicio.py
│   │   │   ├── vision_servicio.py   # Detector YOLO
│   │   │   ├── prediccion_servicio.py
│   │   │   └── inventario_vision.py
│   │   └── schemas/
│   └── api/                         # Endpoints REST
│
├── app/                             # Interfaz Streamlit
│   ├── views/                       # Vistas
│   ├── logic/                       # Lógica de presentación
│   ├── components/
│   ├── utils/
│   └── styles/
│
├── tests/                           # 145 tests unitarios
│   ├── test_producto_logic.py
│   ├── test_inventario_logic.py
│   ├── test_venta_logic.py
│   ├── test_validators.py
│   ├── test_helpers.py
│   ├── test_api.py
│   └── conftest.py
│
├── docs/
│   ├── arquitectura.md
│   ├── Final.md
│   └── Tecnologia_Del_Proyecto.md
│
├── requirements.txt
├── run.py
└── main.py
```

### 3.2 Módulos Principales y Sus Responsabilidades

| Módulo | Única Responsabilidad | Archivo Correspondiente |
|--------|---------------------|------------------------|
| `product_db.py` | Almacenar los 25 productos de MarkeTTalento | `src/core/database/` |
| `db_reader.py` | Leer datos de productos y ventas | `src/core/database/` |
| `detector.py` | Detectar productos en imágenes con YOLO | `src/aplicacion/servicios/vision_servicio.py` |
| `recommender.py` | Calcular métricas y recomendaciones | `src/aplicacion/servicios/inventario_servicio.py` |
| `stock_predictor.py` | Predecir días hasta agotamiento | `src/aplicacion/servicios/prediccion_servicio.py` |
| `demoStreamlit.py` | Dashboard interactivo | `app/views/dashboard.py` |

### 3.3 Beneficios de la Nueva Arquitectura

1. **Mantenibilidad**: Cada módulo se modifica independientemente
2. **Testabilidad**: 145 tests covering todos los módulos principales
3. **Reusabilidad**: Los servicios se importan en Flask, Streamlit, o CLI
4. **Legibilidad**: Archivos de 30-50 líneas vs 500 líneas
5. **Colaboración**: Varios desarrolladores pueden trabajar en paralelo

---

## 4. Tests Unitarios

### 4.1 Cobertura Implementada

Se implementó una suite completa de **145 tests** utilizando pytest:

| Archivo de Test | Tests | Cobertura |
|-----------------|-------|-----------|
| `test_producto_logic.py` | 20 | Lógica de productos (filtros, validación, export) |
| `test_inventario_logic.py` | 29 | Gestión de inventario (stock, estado, métricas) |
| `test_venta_logic.py` | 12 | Proceso de ventas |
| `test_validators.py` | 25 | Validaciones (SKU, email, stock) |
| `test_helpers.py` | 14 | Utilidades (formateo, conversión) |
| `test_api.py` | 45 | Endpoints HTTP (mock de HTTPX) |

### 4.2 Convenciones Aplicadas

- **AAA Pattern**: Arrange-Act-Assert en cada test
- **Docstrings Google**: Documentación en todas las funciones de test
- **Type Hints**: Anotaciones de tipo en funciones y parámetros
- **Fixtures**: Uso de `conftest.py` para datos compartidos

### 4.3 Resultados de Ejecución

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.2
collected 145 items
145 passed in 6.34s
```

---

## 5. Pipeline CI/CD

### 5.1 Configuración Implementada

Se creó `.github/workflows/ci.yml` con matrix de versiones:

```yaml
strategy:
  fail-fast: false
  matrix:
    python-version: ["3.9", "3.10", "3.11", "3.12"]
```

### 5.2 Resultados de la Matriz de Versiones

| Versión Python | Resultado | Observaciones |
|----------------|-----------|---------------|
| 3.9 | ❌ FALLO | numpy (dependencia transitiva de pandas/scikit-learn) incompatible |
| 3.10 | ✅ OK | Todas las dependencias compatibles |
| 3.11 | ✅ OK | Todas las dependencias compatibles |
| 3.12 | ✅ OK | Todas las dependencias compatibles |

### 5.3 Análisis del Fallo en Python 3.9

**Causa raíz**: Las dependencias transitivas instalaron `numpy >= 2.1`, que requiere Python >= 3.10. Python 3.9 no es compatible con numpy 2.1+.

**Dependencias problemáticas**:
- `pandas==3.0.1` → requiere numpy >= 1.23.5
- `scikit-learn==1.8.0` → requiere numpy >= 1.19.5
- Resolución de pip → instala numpy 2.1+ por defecto

**Lección aprendida**: Es necesario auditar dependencias transitivas, especialmente en proyectos de ciencia de datos.

### 5.4 Ventaja de fail-fast: false

Con `fail-fast: false`, el pipeline ejecutó los 4 jobs y pudimos observar que:
- El fallo era exclusivo de Python 3.9
- Las versiones 3.10+ funcionaban correctamente
- Esto permitió tomar decisiones informadas sobre compatibilidad

---

## 6. Uso de Inteligencia Artificial

### 6.1 Prompts Principales Utilizados

| Archivo | Prompt Usado | Resultado |
|---------|-------------|-----------|
| `prediccion_servicio.py` | "Crea función que prediga días hasta agotamiento usando media móvil y tendencia" | Bosquejo inicial de predict_stock_outage |
| Tests de predicción | "Genera tests pytest para función de predicción" | Template base para casos de prueba |
| Dashboard Streamlit | "Crea dashboard con st.metric, st.dataframe y recomendaciones" | Estructura inicial del UI |

### 6.2 Trabajo Manual (Sin IA)

Decidí NO usar IA para:

1. **Tests unitarios completos**: Los 145 tests fueron escritos y revisados manualmente para asegurar cobertura completa de edge cases
2. **Pipeline CI/CD**: Configuré el workflow manualmente siguiendo las especificaciones exactas del ejercicio
3. **Validadores**: Las funciones de validación (SKU único, email, stock) requieren conocer las reglas del dominio
4. **Estilos CSS**: Componentes visuales adaptados al diseño existente

### 6.3 Balance IA vs Manual

- **~30%** del código inicial generado con ayuda de IA ( bosquejos, templates)
- **~70%** escrito y revisado manualmente (tests, validación, configuración)

---

## 7. Interfaz de Usuario con Streamlit

### 7.1 Archivo: interface/demoStreamlit.py

La interfaz reemplaza completamente el HTML embebido de Flask. Cumple con las secciones obligatorias:

### 7.2 Secciones Implementadas

| Sección | Componente | Descripción |
|---------|------------|-------------|
| A - Resultados del Análisis | `st.metric` | Métricas principales (total productos, críticos, valor inventario) |
| B - Detalle del Análisis | `st.dataframe` | Tabla con todos los productos detectados |
| C - Recomendaciones | `st.write` | Lista de productos con estado Crítico/Bajo + mensaje de acción |
| Valor del Inventario | `st.metric` | Suma de (stock × precio) formateado con 2 decimales y símbolo € |

### 7.3 Principios Aplicados

- **Importa exclusivamente de services/**: No contiene lógica de negocio
- **Separación de responsabilidades**: Lógica en `app/logic/`, presentación en `app/views/`
- **Type hints y docstrings**: Código documentado

---

## 8. Lecciones Aprendidas

### 8.1 Técnicas

1. **SRP no es opcional**: Un archivo de 500 líneas siempre será más difícil de mantener que 10 archivos de 50 líneas
2. **Tests primero (TDD)**: Escribir los tests antes de refactorizar ayuda a no romper funcionalidad existente
3. **CI/CD desde el inicio**: Configurar el pipeline al principio detecta problemas de compatibilidad antes de que sea troppo tarde
4. **Auditar dependencias transitivas**: Las versiones de librerías directas no cuentan toda la historia

### 8.2 Profesionales

1. **Documentar decisiones**: Por qué elegimos una arquitectura, por qué no usamos IA en ciertos casos
2. **Revisión manual es necesaria**: La IA ayuda pero no sustituye el criterio del desarrollador
3. **Trabajo en equipo**: La arquitectura SRP permite que múltiples personas trabajen en paralelo sin conflictos

---

## 9. Conclusiones

### 9.1 Objetivos Cumplidos

✅ Analizar y documentar los 9 problemas de diseño del código heredado  
✅ Refactorizar en módulos SRP (6 módulos principales)  
✅ Implementar 145 tests unitarios con pytest  
✅ Configurar pipeline CI/CD con matriz Python 3.9-3.12  
✅ Crear dashboard Streamlit con 3 secciones obligatorias  
✅ Documentar todo el proceso en docs/arquitectura.md y docs/Final.md  

### 9.2 Valor del Proyecto

Este proyecto demuestra la capacidad de:
- Leer y analizar código heredado sin modificarlo inicialmente
- Aplicar principios SOLID de forma práctica
- Implementar testing profesional
- Configurar CI/CD empresarial
- Usar herramientas modernas (Streamlit, YOLO, GitHub Actions)
- Documentar decisiones técnicas

### 9.3 Recomendaciones para Futura Mantención

1. **Actualizar requirements.txt**: Añadir `numpy<2.1` para mantener compatibilidad con Python 3.9, o elevar la versión mínima a 3.10
2. **Añadir más tests de integración**: Los tests actuales son mayormente unitarios
3. **Implementar autenticación**: El dashboard actual no tiene login
4. **Añadir logs estructurados**: Para producción es necesario un sistema de logging centralizado

---

## 10. Información del Proyecto

| Campo | Valor |
|-------|-------|
| **Proyecto** | MarkeTTalento - Sistema de Inventario Inteligente |
| **Módulo** | 4 - Refactorización SRP, Streamlit y CI/CD |
| **Formación** | Dicampus - Fundación Dicampus |
| **Alumno** | [Nombre del Alumno] |
| **Fecha** | Mayo 2026 |
| **Python** | 3.9 - 3.12 (matrix CI/CD) |
| **Tests** | 145 passing |
| **Líneas de código** | ~2500 (incluyendo tests y docs) |

---

*Documento generado como parte del ejercicio individual del Módulo 4 de Dicampus - Inclusión Socio-Laboral*