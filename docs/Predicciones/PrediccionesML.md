# Predicciones ML & Inteligencia de Negocio

## Resumen Ejecutivo

El módulo de **Predicciones ML** transforma el histórico de tickets del TPV en decisiones de negocio accionables. Utiliza **scikit-learn** (`LinearRegression`) para pronosticar demanda, clasifica productos por método **ABC (Pareto 80/20)**, genera **alertas de reposición** inteligentes, sugiere **ajustes de precio** basados en rotación y analiza **patrones estacionales** comparando meses.

Todo funciona sobre la nueva arquitectura `Ticket`/`TicketLinea` con ~200 tickets de demo generados con patrones estacionales realistas (verano=+bebidas frías, invierno=+café, fines de semana=+alcohol).

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend Streamlit (app/views/predicciones.py)              │
│  ├─ Tab Demanda     → /prediccion/producto/{id}             │
│  ├─ Tab Inteligencia→ /prediccion/abc, /precios, /estac     │
│  └─ Tab Alertas     → /prediccion/alertas                   │
├─────────────────────────────────────────────────────────────┤
│  API FastAPI (src/api/predicciones.py)                       │
│  ├─ GET /producto/{id}      → PrediccionServicioML          │
│  ├─ GET /categoria/{id}     → PrediccionServicioML          │
│  ├─ GET /alertas            → Alertas reposición            │
│  ├─ GET /abc                → Clasificación ABC             │
│  ├─ GET /precios            → Sugerencias precio            │
│  ├─ GET /estacionalidad     → Comparativa mes vs mes        │
│  └─ GET /dashboard          → Resumen global                │
├─────────────────────────────────────────────────────────────┤
│  Servicio ML (src/aplicacion/servicios/prediccion_ml.py)     │
│  ├─ Modelo 1: Demanda (LinearRegression + fallback)         │
│  ├─ Modelo 2: Alertas reposición                            │
│  ├─ Modelo 3: Análisis ABC                                  │
│  ├─ Modelo 4: Sugerencias precio                            │
│  └─ Modelo 5: Estacionalidad                                │
├─────────────────────────────────────────────────────────────┤
│  Repositorios (src/implementaciones/repositorios_impl.py)    │
│  └─ SQLAlchemyTicketRepositorio (joinedload eager)          │
├─────────────────────────────────────────────────────────────┤
│  Base de datos (SQLite) → tabla tickets + ticket_lineas     │
│  └─ 199 tickets (13 reales + 186 demo, 6 meses)             │
└─────────────────────────────────────────────────────────────┘
```

---

## Modelos de Machine Learning

### Modelo 1: Predicción de Demanda
**Algoritmo:** `LinearRegression` de scikit-learn (con fallback estadístico si sklearn no está disponible).

**Features:**
- Día de la semana (0=Lunes)
- Día del mes
- Mes

**Proceso:**
1. Extrae líneas de tickets del producto/categoría de los últimos N días.
2. Agrupa por día, rellena días sin ventas con 0.
3. Entrena `LinearRegression(X=[weekday, day, month], y=cantidad)`.
4. Genera pronóstico para los próximos 7/14/30 días.
5. Calcula consumo promedio diario y tendencia (ALZA/BAJA/ESTABLE).
6. Cruza con stock actual para calcular días hasta agotarse.

**Estados de stock:**
| Días restantes | Estado |
|----------------|--------|
| ≤ 2 | CRITICO |
| ≤ 7 | BAJO |
| ≤ 14 | MODERADO |
| > 14 | ADECUADO |

### Modelo 2: Alertas de Reposición
**Lógica:** Para cada producto activo, calcula `dias_restantes = stock_actual / consumo_promedio_diario`.

| Nivel | Condición | Cantidad recomendada |
|-------|-----------|----------------------|
| **URGENTE** | ≤ 2 días | Consumo × 21 días |
| **ATENCION** | ≤ 7 días | Consumo × 14 días |
| **OPORTUNIDAD** | ≤ 14 días | Consumo × 14 días |

Ordenadas por urgencia descendente.

### Modelo 3: Análisis ABC (Pareto 80/20)
**Lógica:**
1. Suma ingresos (`subtotal`) y unidades vendidas por producto en tickets completados.
2. Ordena por ingresos descendente.
3. Clasifica por acumulado:
   - **Clase A**: acumulado ≤ 80% de ingresos totales
   - **Clase B**: acumulado ≤ 95%
   - **Clase C**: resto

El frontend muestra un gráfico de barras tipo Pareto con badges de color verde/amarillo/gris.

### Modelo 4: Sugerencias de Precio Óptimo
**Lógica:** Cruza demanda diaria + stock actual + precio actual.

| Rotación | Stock | Sugerencia | Ajuste |
|----------|-------|------------|--------|
| ALTA | < 10 | SUBIR | +8% |
| ALTA | > 50 | MANTENER | 0% |
| BAJA | > 30 | BAJAR | -10% |
| MEDIA | < 5 | SUBIR | +5% |

**Impacto estimado:** Calcula diferencia de ingresos mensuales tras el ajuste (asume +15% ventas al bajar precio).

### Modelo 5: Estacionalidad
**Lógica:** Compara métricas del mes actual vs mes anterior:
- Ingresos totales
- Número de tickets
- Unidades vendidas

Calcula variación porcentual y determina tendencia general (ALZA/BAJA/ESTABLE).

---

## API Endpoints

| Endpoint | Descripción | Parámetros |
|----------|-------------|------------|
| `GET /api/v1/prediccion/producto/{id}` | Pronóstico de demanda para un producto | `dias_historia` (default 90), `dias_futuro` (default 30) |
| `GET /api/v1/prediccion/categoria/{id}` | Pronóstico agregado por categoría | `dias_historia`, `dias_futuro` |
| `GET /api/v1/prediccion/alertas` | Alertas de reposición | `dias_seguridad` (default 14) |
| `GET /api/v1/prediccion/abc` | Clasificación ABC | `dias` (default 90) |
| `GET /api/v1/prediccion/precios` | Sugerencias de precio | `dias` (default 60) |
| `GET /api/v1/prediccion/estacionalidad` | Comparativa mes actual vs anterior | — |
| `GET /api/v1/prediccion/dashboard` | Resumen global de métricas | — |

---

## Frontend: 3 Tabs

### Tab 1: 📈 Demanda
- **Selector**: Producto individual o categoría agregada.
- **Gráfico**: Línea azul (histórico 90 días) + línea morada discontinua (pronóstico ML).
- **Métricas**: Consumo promedio/día, días hasta agotarse, tendencia, stock actual.
- **Badge estado**: CRITICO (rojo), BAJO (naranja), MODERADO (azul), ADECUADO (verde).

### Tab 2: 🧠 Inteligencia
Tres sub-tabs:
- **ABC**: Gráfico de barras Pareto (top 15) + tabla detallada con badges A/B/C.
- **Precio Óptimo**: Tarjetas con sugerencia SUBIR/BAJAR/MANTENER, ajuste % e impacto estimado €/mes.
- **Estacionalidad**: Comparativa mes actual vs anterior con métricas e indicador de tendencia.

### Tab 3: 🚨 Alertas
- **Resumen superior**: Total alertas, urgentes, atención, oportunidad.
- **Filtro**: Multiselect por nivel.
- **Tarjetas**: Producto, nivel con badge de color, stock actual, días hasta agotarse, cantidad recomendada.

---

## Datos Demo

**Script:** `scripts/generar_datos_demo.py`

**Patrones estacionales inyectados:**
- **Bebidas frías / cerveza / refrescos**: +50% peso en meses cálidos (marzo–septiembre).
- **Café / caliente**: +100% peso en invierno (octubre–febrero).
- **Leche / pan / desayuno**: base alta todo el año, +20% en invierno.
- **Vino / alcohol**: +50% en fines de semana (viernes–domingo).
- **Fines de semana**: +25% probabilidad de ticket.
- **Navidad/Enero**: +20% probabilidad base.

**Resultado:** 186 tickets adicionales sobre 6 meses, distribuidos de forma realista para que el ML produzca predicciones coherentes desde el primer arranque.

---

## Estructura de Archivos

```
src/
  dominio/repositorios/repositorios.py          → ITicketRepositorio (interfaz)
  implementaciones/repositorios_impl.py          → SQLAlchemyTicketRepositorio (impl)
  aplicacion/servicios/prediccion_ml.py          → Motor ML (5 modelos)
  api/predicciones.py                            → Router FastAPI (7 endpoints)
app/
  views/predicciones.py                          → Frontend Streamlit (3 tabs)
scripts/
  generar_datos_demo.py                          → Generador de datos demo (200 tickets)
docs/
  PrediccionesML.md                              → Este documento
```

---

## Guía de Uso Rápido

### 1. Arrancar API
```bash
cd D:\ADEV\ProyectosVScode\MarkeTTalento
uvicorn main:app --host 0.0.0.0 --port 8002
```

### 2. Arrancar Dashboard
```bash
streamlit run app/main.py
```

### 3. Navegar
- En el sidebar, seleccionar **🔮 Predicciones**.
- **Tab Demanda**: elegir un producto (ej. "Leche Asturiana") y pulsar *Generar Pronóstico*.
- **Tab Inteligencia → ABC**: ver el gráfico Pareto con productos estrella.
- **Tab Alertas**: revisar productos en riesgo de agotamiento.

### 4. Probar API directamente
```bash
curl http://localhost:8002/api/v1/prediccion/dashboard
```
O abrir `http://localhost:8002/docs` para la documentación interactiva Swagger.

---

## Decisiones Técnicas Clave

1. **Nueva arquitectura Ticket/TicketLinea**: Se descartó la tabla `Venta` legacy porque no tenía relaciones a productos reales y el antiguo servicio de predicciones tenía un bucle infinito (`predecir_todos` llamaba recursivamente a `predecir_demanda` sin romper).
2. **Eager loading (`joinedload`)**: Todos los queries del `TicketRepositorio` usan `joinedload(TicketLinea.ticket)` y `joinedload(TicketLinea.producto).joinedload(Producto.categoria)` para evitar `DetachedInstanceError` al acceder a relaciones fuera de la sesión SQLAlchemy.
3. **Fallback sin sklearn**: Si `scikit-learn` no está disponible, el pronóstico usa un modelo estadístico simple con factor de tendencia y variación por día de semana.
4. **Consumo promedio sobre 30 días (con ceros)**: Se usa la media de todo el período (incluyendo días sin ventas) para evitar sobrestimación artificial. Esto hace que las alertas sean más conservadoras y realistas.

---

## Métricas de referencia (con datos demo)

| Métrica | Valor |
|---------|-------|
| Tickets totales | 199 |
| Productos analizados | 21 |
| Alertas activas | ~3–8 (depende de stock actual) |
| Productos Clase A | ~11 (52%) |
| Sugerencias de precio | ~6–12 |
| Tiempo de entrenamiento | < 50 ms por producto |
