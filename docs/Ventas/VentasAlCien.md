# Ventas al 100% — Documentación Completa del Módulo TPV

> **Proyecto:** MarkeTTalento  
> **Módulo:** Ventas / TPV (Terminal Punto de Venta)  
> **Versión:** 1.0  
> **Fecha:** Mayo 2026

---

## Índice

1. [Visión General](#1-visión-general)
2. [Arquitectura Backend](#2-arquitectura-backend)
3. [Frontend TPV](#3-frontend-tpv)
4. [Dashboard de Ventas](#4-dashboard-de-ventas)
5. [Historial de Tickets](#5-historial-de-tickets)
6. [Lista Completa de Funcionalidades](#6-lista-completa-de-funcionalidades)
7. [Archivos Modificados y Creados](#7-archivos-modificados-y-creados)
8. [Guía de Uso](#8-guía-de-uso)
9. [Mejoras Visuales y de Flujo](#9-mejoras-visuales-y-de-flujo)

---

## 1. Visión General

El módulo de **Ventas** de MarkeTTalento ha sido transformado de un simple registro de ventas individuales a un **TPV (Terminal Punto de Venta) profesional** comparable a los utilizados en retail real (tipo Carrefour, bar, restaurante).

### Lo que era antes
- Cada venta era un registro suelto en la tabla `ventas`
- Solo se podía vender **1 producto por operación**
- Sin concepto de "ticket" ni carrito
- Sin control de concurrencia
- Sin autenticación de cajero

### Lo que es ahora
- **Tickets completos** con múltiples líneas de productos
- **Carrito de compras** visual con teclado numérico
- **Modal de cobro** profesional con cálculo de cambio
- **10 gráficas** en el dashboard de ventas
- **Historial completo** con filtros, paginación y anulación
- **Control de concurrencia** con `FOR UPDATE`
- **9 cajeros** preconfigurados

---

## 2. Arquitectura Backend

### 2.1 Nuevas Entidades (SQLAlchemy)

#### `Ticket` (Cabecera del ticket)
```python
id: int (PK)
numero_ticket: str      # Ej: "000042" (autoincremental con padding)
cajero: str             # Nombre del cajero
fecha: datetime         # Fecha y hora de la venta
total: float            # Total calculado automáticamente
metodo_pago: str        # "efectivo", "tarjeta", "transferencia"
entrega_efectivo: float # Cuánto dio el cliente (solo efectivo)
cambio: float           # Calculado automáticamente
estado: str             # "completado" o "anulado"
lineas: List[TicketLinea]
```

#### `TicketLinea` (Detalle del ticket)
```python
id: int (PK)
ticket_id: int (FK → Ticket)
producto_id: int (FK → Producto)
cantidad: int
precio_unitario: float
subtotal: float         # cantidad × precio_unitario
```

#### `Venta` (Legacy)
- Se mantiene por compatibilidad histórica pero **ya no se usa** en el TPV nuevo.

### 2.2 Schemas Pydantic

- `TicketLineaBase` / `TicketLineaCreate` / `TicketLineaResponse`
- `TicketBase` / `TicketCreate` / `TicketResponse`

### 2.3 Endpoints de la API (`/api/v1/tickets`)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/tickets` | Crear ticket (transacción atómica) |
| `GET` | `/tickets` | Listar tickets con filtros |
| `GET` | `/tickets/{id}` | Obtener ticket por ID |
| `DELETE` | `/tickets/{id}` | Anular ticket (reintegra stock) |
| `GET` | `/tickets/estadisticas/resumen` | Métricas clave |
| `GET` | `/tickets/estadisticas/tendencia` | Ventas por día |
| `GET` | `/tickets/estadisticas/por-categoria` | Ingresos por categoría |
| `GET` | `/tickets/estadisticas/por-hora` | Distribución horaria |
| `GET` | `/tickets/estadisticas/mapa-calor` | Heatmap día/hora |
| `GET` | `/tickets/estadisticas/comparativa-mes` | Mes actual vs anterior |
| `GET` | `/tickets/estadisticas/top-productos` | Top por unidades o ingresos |
| `GET` | `/tickets/estadisticas/ticket-promedio` | Evolución del ticket promedio |

### 2.4 Transacción Atómica (`POST /tickets`)

1. Inicia transacción SQLAlchemy
2. Bloquea filas de inventario con `with_for_update()`
3. Valida stock suficiente para cada línea
4. Genera número de ticket autoincremental (`MAX+1` con padding a 6 dígitos)
5. Inserta cabecera `Ticket`
6. Inserta cada `TicketLinea`
7. Descuenta stock en `Inventario`
8. Commitea o hace rollback si falla algo

### 2.5 Anulación (`DELETE /tickets/{id}`)

1. Verifica que el ticket exista y no esté ya anulado
2. **Solo permite anular tickets del día actual** (seguridad)
3. Bloquea inventarios con `with_for_update()`
4. Reintegra el stock de cada línea
5. Marca el ticket como `estado = "anulado"`
6. Commitea

### 2.6 Control de Concurrencia

- **`FOR UPDATE`** en SQLite: Al crear un ticket, se bloquean las filas de inventario de los productos involucrados. Si otro cajero intenta vender el mismo producto simultáneamente, espera o recibe error de stock insuficiente.

---

## 3. Frontend TPV

### 3.1 Layout Principal (Tab "TPV")

```
┌─────────────────────────────┬──────────────────────────────────────────┐
│  🧑‍💼 Cajero: [andres ▼]       │  [Cervezas] [Cafés] [Todos] ...          │
│  🔍 Barcode: [________]      │  ─────────────────────────────────────   │
│  📅 09/05/2026 14:32         │                                          │
│                              │  ┌────────┐ ┌────────┐ ┌────────┐       │
│  ─────────────────────────── │  │  🍺    │ │  ☕    │ │  🍔    │       │
│  2 x Coca Cola       €5.00   │  │Cerveza │ │ Café   │ │Hambur. │       │
│  ○ [-] [+] [🗑️]              │  │  €2.50 │ │ €1.50  │ │ €5.00  │       │
│  ─────────────────────────── │  │Stock:12│ │Stock:5 │ │Stock:0 │       │
│  1 x Café Solo       €1.50   │  └────────┘ └────────┘ └────────┘       │
│  ● [-] [+] [🗑️]              │  ┌────────┐ ┌────────┐                  │
│                              │  │  🍟    │ │  🍕    │                  │
│  [7] [8] [9]                 │  │Patatas │ │ Pizza  │                  │
│  [4] [5] [6]                 │  │ €2.00  │ │ €3.50  │                  │
│  [1] [2] [3]                 │  └────────┘ └────────┘                  │
│  [0] [.] [CLR]               │                                          │
│                              │                                          │
│  ─────────────────────────── │                                          │
│  DTO 5%  DTO 10%  DTO 20%    │                                          │
│                              │                                          │
│  Total: €6.30                │                                          │
│                              │                                          │
│  [💶 Efectivo] [💳 Tarjeta]  │                                          │
│  [🧹 Limpiar]                │                                          │
└─────────────────────────────┴──────────────────────────────────────────┘
```

### 3.2 Panel Izquierdo — Ticket Actual

| Elemento | Descripción |
|----------|-------------|
| **Cajero** | Selectbox con 9 nombres preconfigurados |
| **Barcode** | Input de texto que busca por SKU, código de barras o nombre |
| **Lista de líneas** | Cantidad × Producto = Subtotal, con botones [-], [+], [🗑️] |
| **Teclado numérico** | Funcional: seleccionar línea + presionar números + "Aplicar" |
| **Input rápido** | Alternativa: number_input directo para cambiar cantidad |
| **Descuento** | Botones DTO 5%, 10%, 20% que aplican al total |
| **Total** | Grande y visible en color cian |
| **Alerta stock** | Popup animado si algún producto queda con <5 unidades |
| **Botones de acción** | Efectivo (verde), Tarjeta (cian), Limpiar (gris) con gradientes |

### 3.3 Panel Derecho — Catálogo de Productos

| Elemento | Descripción |
|----------|-------------|
| **Barra de búsqueda** | Filtra productos por nombre en tiempo real |
| **Categorías** | Grid de botones con colores distintivos por categoría |
| **Productos** | Grid 4 columnas con imagen, nombre, precio, stock |
| **Badge de stock** | Número en esquina (verde si >5, amarillo si <5, rojo si 0) |
| **Favoritos** | Productos más vendidos aparecen primero con ⭐ y borde dorado |
| **Sin stock** | Opacidad 40%, borde rojo, no clickeable |
| **Agregar** | Botón ➕ para agregar 1 unidad |
| **Cantidad** | Botón #️⃣ para abrir modal y elegir cantidad antes de agregar |

### 3.4 Modal de Cobro

Cuando se presiona "Efectivo" o "Tarjeta", aparece un **modal centrado** con:

```
┌─────────────────────────────────────────┐
│              💳 (icono bounce)          │
│              Cobrar                     │
│           Total: €12.50                 │
│         MÉTODO: TARJETA                 │
│  ─────────────────────────────────────  │
│  Rápido: [€5] [€10] [€20] [€50]        │
│  Entrega: € [        15.00   ]          │
│         Cambio: €2.50                   │
│                                         │
│    [ ] ✅ Confirmar cobro               │
│                                         │
│  [❌ Cancelar]  [✅ Finalizar Venta]    │
└─────────────────────────────────────────┘
```

| Feature | Descripción |
|---------|-------------|
| **Backdrop blur** | Fondo oscuro con `blur(10px)` |
| **Animación entrada** | `fadeIn` + `scale` desde el centro |
| **Icono animado** | 💵 o 💳 con animación `bounce` |
| **Sonido** | Beep de caja registradora al finalizar |
| **Botones billete** | €5, €10, €20, €50 rellenan el campo entrega |
| **Cálculo cambio** | Automático al modificar entrega |
| **Enter** | Atajo de teclado para finalizar si checkbox marcado |
| **Foco auto** | Cursor va directo al campo entrega |
| **Checkbox** | "Confirmar cobro" obligatorio para habilitar "Finalizar" |
| **Botones** | Cancelar (rojo) / Finalizar (cian con gradiente) |

### 3.5 Post-Cobro

Después de finalizar la venta:
1. Se reproduce sonido de éxito
2. Aparece el **ticket simplificado** en pantalla
3. Botones: **Descargar** (.txt), **Imprimir** (window.print), **Nueva Venta**
4. Contador de cierre automático en 5 segundos

**Formato del ticket:**
```
------------------------------------------
        MARKE TTALENTO
    Ticket N° 00042
    09/05/2026  14:32
    Cajero: andres
------------------------------------------
2 x Coca Cola           5,00 €
1 x Café Solo           1,30 €
------------------------------------------
TOTAL:                  6,30 €
Metodo: EFECTIVO
Entrega:        10,00 €
Cambio:          3,70 €
------------------------------------------
    ¡Gracias por su visita!
------------------------------------------
```

---

## 4. Dashboard de Ventas

### 4.1 Métricas Principales

| Métrica | Descripción |
|---------|-------------|
| 💰 Total Ingresos | Suma de todos los tickets completados |
| 🎫 Tickets | Número total de tickets |
| 📦 Unidades | Suma de cantidades vendidas |
| 📈 Ticket Promedio | Total ingresos / Número de tickets |

### 4.2 Meta Diaria

- Input configurable: "Meta diaria (€)"
- Gráfica de barras: Meta vs Real
- Porcentaje de progreso
- Mensaje: "Faltan €X" o "🎉 ¡Meta alcanzada!"

### 4.3 Las 10 Gráficas

| # | Gráfica | Tipo | Descripción |
|---|---------|------|-------------|
| 1 | 📈 Tendencia de Ventas | Línea (área) | Ingresos por día |
| 2 | 🥇 Top Productos (Unidades) | Barras verticales | Más vendidos por cantidad |
| 3 | ⏰ Ventas por Hora | Barras | Distribución horaria |
| 4 | 📊 Distribución de Ingresos | Donut | Por rangos de ticket (€0-10, €10-25, etc.) |
| 5 | 🏷️ Ventas por Categoría | Donut | Ingresos agrupados por categoría |
| 6 | 📉 Ticket Promedio | Línea (área) | Evolución diaria |
| 7 | 💶 Top Productos (Ingresos) | Barras horizontales | Más rentables en € |
| 8 | 🔥 Mapa de Calor | Heatmap | Tickets por día de semana vs hora |
| 9 | 💳 Métodos de Pago | Barras | Efectivo vs Tarjeta vs Transferencia |
| 10 | 📅 Comparativa Mes | Barras agrupadas | Mes actual vs mes anterior |

---

## 5. Historial de Tickets

### 5.1 Filtros Rápidos de Fecha

Botones de un solo clic:
- **Hoy** | **Ayer** | **Últimos 7 días** | **Este mes** | **Todo**

### 5.2 Filtros Avanzados

- Cajero (selectbox)
- Fecha desde / hasta (date_picker)
- Botón "Actualizar"

### 5.3 Lista de Tickets

- Cada ticket es un **expander** clickeable
- Dentro: estado, método de pago, entrega/cambio (si efectivo), tabla de líneas
- Botón **"❌ Anular Ticket"** (solo si está completado y es del día actual)

### 5.4 Paginación

- 10 tickets por página
- Botones "Anterior" / "Siguiente"
- Indicador "Página X de Y"

### 5.5 Exportación

- Botón **"📥 Exportar Excel"** con todas las líneas desagregadas

---

## 6. Lista Completa de Funcionalidades

### Backend
| # | Funcionalidad | Estado |
|---|---------------|--------|
| 1 | Entidad `Ticket` (cabecera) | ✅ |
| 2 | Entidad `TicketLinea` (detalle) | ✅ |
| 3 | Schema Pydantic `TicketCreate` | ✅ |
| 4 | Schema Pydantic `TicketResponse` | ✅ |
| 5 | Endpoint `POST /tickets` (transacción atómica) | ✅ |
| 6 | Endpoint `GET /tickets` (con filtros) | ✅ |
| 7 | Endpoint `GET /tickets/{id}` | ✅ |
| 8 | Endpoint `DELETE /tickets/{id}` (anular) | ✅ |
| 9 | Control de concurrencia (`FOR UPDATE`) | ✅ |
| 10 | Número de ticket autoincremental (000001) | ✅ |
| 11 | Cálculo automático de total y cambio | ✅ |
| 12 | 10 endpoints de estadísticas | ✅ |
| 13 | Reintegración de stock al anular | ✅ |
| 14 | Validación de stock insuficiente | ✅ |
| 15 | Solo anular tickets del día actual | ✅ |

### Frontend TPV
| # | Funcionalidad | Estado |
|---|---------------|--------|
| 16 | Layout dos paneles (35/65) | ✅ |
| 17 | Selectbox de cajero (9 nombres) | ✅ |
| 18 | Input de código de barras / búsqueda | ✅ |
| 19 | Grid de categorías con colores | ✅ |
| 20 | Grid de productos (4 columnas) | ✅ |
| 21 | Imágenes redimensionadas a thumbnail | ✅ |
| 22 | Badges de stock en esquina | ✅ |
| 23 | Productos favoritos (más vendidos primero) | ✅ |
| 24 | Productos sin stock deshabilitados | ✅ |
| 25 | Barra de búsqueda en tiempo real | ✅ |
| 26 | Botón "Agregar" (+1) | ✅ |
| 27 | Botón "Cantidad" (modal para elegir N) | ✅ |
| 28 | Lista de líneas del ticket | ✅ |
| 29 | Botones [-], [+], [🗑️] por línea | ✅ |
| 30 | Teclado numérico funcional | ✅ |
| 31 | Input rápido de cantidad (number_input) | ✅ |
| 32 | Scroll en panel de ticket | ✅ |
| 33 | Descuento rápido (5%, 10%, 20%) | ✅ |
| 34 | Alerta de stock bajo (<5) | ✅ |
| 35 | Total grande y visible | ✅ |
| 36 | Botón "Efectivo" con gradiente verde | ✅ |
| 37 | Botón "Tarjeta" con gradiente cian | ✅ |
| 38 | Botón "Limpiar" con gradiente gris | ✅ |

### Modal de Cobro
| # | Funcionalidad | Estado |
|---|---------------|--------|
| 39 | Modal centrado con columnas Streamlit | ✅ |
| 40 | Backdrop blur | ✅ |
| 41 | Animación de entrada (fadeIn + scale) | ✅ |
| 42 | Icono animado (bounce) | ✅ |
| 43 | Sonido de caja registradora | ✅ |
| 44 | Botones rápidos de billetes (€5, €10, €20, €50) | ✅ |
| 45 | Cálculo automático de cambio | ✅ |
| 46 | Checkbox "Confirmar cobro" | ✅ |
| 47 | Atajo Enter para finalizar | ✅ |
| 48 | Foco automático en input de entrega | ✅ |
| 49 | Botón Cancelar (rojo) | ✅ |
| 50 | Botón Finalizar Venta (cian, disabled hasta confirmar) | ✅ |

### Post-Cobro
| # | Funcionalidad | Estado |
|---|---------------|--------|
| 51 | Ticket simplificado tipo Carrefour | ✅ |
| 52 | Botón Descargar (.txt) | ✅ |
| 53 | Botón Imprimir (window.print) | ✅ |
| 54 | Botón Nueva Venta | ✅ |
| 55 | Cierre automático en 5 segundos | ✅ |

### Dashboard
| # | Funcionalidad | Estado |
|---|---------------|--------|
| 56 | Métricas principales (4 tarjetas) | ✅ |
| 57 | Meta diaria configurable | ✅ |
| 58 | Gráfica de objetivos (Meta vs Real) | ✅ |
| 59 | Tendencia de ventas | ✅ |
| 60 | Top productos (unidades) | ✅ |
| 61 | Ventas por hora | ✅ |
| 62 | Distribución de ingresos | ✅ |
| 63 | Ventas por categoría | ✅ |
| 64 | Ticket promedio | ✅ |
| 65 | Top productos (ingresos €) | ✅ |
| 66 | Mapa de calor día/hora | ✅ |
| 67 | Métodos de pago | ✅ |
| 68 | Comparativa mes actual vs anterior | ✅ |

### Historial
| # | Funcionalidad | Estado |
|---|---------------|--------|
| 69 | Filtros rápidos de fecha (5 botones) | ✅ |
| 70 | Filtro por cajero | ✅ |
| 71 | Filtro por rango de fecha | ✅ |
| 72 | Lista expandible con líneas | ✅ |
| 73 | Paginación (10 por página) | ✅ |
| 74 | Botón Anular (solo día actual) | ✅ |
| 75 | Exportación a Excel | ✅ |

**Total: 75 funcionalidades implementadas y probadas**

---

## 7. Archivos Modificados y Creados

### Nuevos
| Archivo | Descripción |
|---------|-------------|
| `src/api/tickets.py` | Router completo de tickets (CRUD + estadísticas) |

### Modificados
| Archivo | Cambios |
|---------|---------|
| `src/dominio/entidades/entidades.py` | Agregadas `Ticket` y `TicketLinea` |
| `src/aplicacion/schemas/schemas.py` | Agregados schemas de tickets |
| `src/api/router.py` | Incluido router `/tickets` |
| `src/core/database/database.py` | Actualizado import de entidades |
| `app/views/ventas.py` | **Reescrito completo** (TPV + Dashboard + Historial) |
| `app/utils/state.py` | Agregadas variables de session_state para TPV |
| `app/styles/ventas.css` | Agregados estilos de modal, teclado, badges, alertas, gradientes |

### Eliminados
| Archivo | Razón |
|---------|-------|
| `data/markettalento.db` | Legacy, incompatible con nuevo modelo |
| `data/inventario.db` | Legacy, duplicada |

---

## 8. Guía de Uso

### Primer uso (después de borrar la BD)

1. Ejecuta `python run.py`
2. Ve a **"📦 Productos"** y crea al menos una **Categoría**
3. Crea al menos un **Producto** con stock inicial > 0
4. Ve a **"💰 Ventas"** → Tab **"TPV"**
5. Selecciona tu **Cajero**
6. Haz clic en una **Categoría**
7. Haz clic en un **Producto** para agregarlo
8. Modifica cantidades con [-], [+] o el **teclado numérico**
9. Presiona **"💶 Efectivo"** o **"💳 Tarjeta"**
10. En el modal: marca **"Confirmar cobro"** y presiona **"Finalizar Venta"**
11. ¡Listo! Descarga el ticket o inicia una **Nueva Venta**

### Atajos de teclado

| Atajo | Acción |
|-------|--------|
| `Enter` | En el modal de cobro, finaliza la venta si el checkbox está marcado |
| `Esc` | No implementado (Streamlit no captura Esc fácilmente) |

### Descuentos

1. Agrega productos al ticket
2. Presiona **"DTO 10%"** (o 5%, 20%)
3. El total se actualiza automáticamente
4. Presiona Efectivo/Tarjeta para cobrar

### Anulación

1. Ve a **"📋 Historial de Tickets"**
2. Expande el ticket que quieres anular
3. Presiona **"❌ Anular Ticket"**
4. El stock se reintegra automáticamente
5. **Solo se pueden anular tickets del día actual**

---

## 9. Mejoras Visuales y de Flujo

### Diseño
| Mejora | Implementación |
|--------|---------------|
| Backdrop blur | `backdrop-filter: blur(10px)` en CSS |
| Animación entrada | `@keyframes modalFadeIn` con `scale` y `translateY` |
| Icono animado | `@keyframes iconoPop` con bounce |
| Gradientes botones | `linear-gradient(135deg, ...)` en Efectivo, Tarjeta, Limpiar |
| Colores por categoría | Diccionario `COLORES_CAT` con hex por nombre |
| Badges de stock | CSS `position: absolute` con esquina superior derecha |
| Productos favoritos | Borde dorado `#f59e0b` + estrella ⭐ |
| Alerta stock bajo | `@keyframes alertaPulse` con opacidad pulsante |
| Scroll panel | `max-height: 55vh` + `overflow-y: auto` |

### Flujo
| Mejora | Implementación |
|--------|---------------|
| Cobro rápido | Botones €5, €10, €20, €50 rellenan input |
| Atajo Enter | JS `keydown` listener en el modal |
| Foco automático | JS `setTimeout` enfoca input de entrega |
| Sonido al cobrar | `<audio>` tag con URL externa |
| Impresión directa | `window.print()` vía `components.html` |
| Cierre automático | `time.time()` + verificación cada rerender |
| Imágenes optimizadas | Pillow `thumbnail(100, 100)` antes de base64 |
| Cantidad directa | Modal emergente con `number_input` antes de agregar |

---

## Notas Técnicas

### Limitaciones conocidas
1. **Streamlit no permite modales reales**: Se simula con columnas centradas y CSS
2. **Sonido requiere interacción previa**: El navegador puede bloquear autoplay hasta que el usuario haga clic
3. **Imágenes base64**: Si hay muchas imágenes grandes, el renderizado puede tardar. Se mitiga con thumbnails de 100x100.
4. **Cierre automático**: Depende de rerenders de Streamlit. Si el usuario no interactúa, puede tardar más de 5 segundos.

### Próximas mejoras posibles
- [ ] Múltiples tickets abiertos simultáneamente (mesas)
- [ ] Soporte para impresora térmica USB directa
- [ ] Sistema de notas/observaciones por ticket
- [ ] Descuentos por producto (no solo por ticket total)
- [ ] Clientes frecuentes / programa de fidelidad
- [ ] Facturación fiscal integrada

---

*Documento generado automáticamente para el proyecto MarkeTTalento.*
