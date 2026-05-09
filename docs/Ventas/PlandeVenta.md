# Plan de Venta — TPV MarkeTTalento

> Quiero acomodar mi apartado de venta y tengo una idea pero necesito ayuda y recomendaciones.
>
> Mi idea es hacer un apartado de dashboard con 4 tipos de gráficas distintas, un apartado de registro de ticket, pero también quiero saber que le falta a mi apartado de ventas para poder llevarlo a producción.

---

## Requerimientos del usuario

El usuario quiere mejorar su apartado de ventas y tiene algunas ideas:

1. Un dashboard con 4 tipos de gráficas distintas
2. Un apartado de registro de tickets
3. Quiere saber qué le falta para llevarlo a producción

Primero necesito entender su proyecto actual. Debo explorar el código base para ver qué ya tiene en su apartado de ventas, qué tecnologías usa, etc.

---

## Exploración del proyecto

¡Perfecto! Vamos a explorar tu proyecto actual para entender bien qué ya tienes y poder darte recomendaciones precisas. Déjame revisar la estructura de tu código y el apartado de ventas existente.

Bien, ahora tengo una visión general del proyecto. Es una aplicación en Python que usa Streamlit (veo `streamlit_app.cpython-314.pyc`), tiene API en `src/api/`, lógica de negocio en `app/logic/`, y componentes en `app/components/`.

El usuario quiere mejorar su apartado de ventas. Necesito leer los archivos clave:

- `app/logic/venta.py` — lógica de ventas
- `src/api/ventas.py` — API de ventas
- `app/main.py` — probablemente la app principal de Streamlit
- Tal vez `app/components/sidebar.py` para ver la navegación

Voy a leer estos archivos para entender el estado actual.

Ahora necesito ver el archivo de ventas actual en la vista de Streamlit y también revisar la estructura de la base de datos, modelos y schemas para entender qué campos hay disponibles.

Necesito leer los archivos de ventas (vista), entidades y schemas para entender el modelo de datos actual.

Ahora tengo un panorama bastante claro del proyecto. Déjame revisar también el dashboard actual y otros archivos relevantes para poder dar una recomendación completa.

Ahora tengo una visión completa del proyecto. Es una aplicación de gestión de inventario/ventas llamada **MarkeTTalento** construida con:

- **FastAPI** como backend
- **Streamlit** como frontend
- **SQLAlchemy** como ORM
- **Plotly** para gráficos
- **SQLite/PostgreSQL** como base de datos

El usuario quiere:

1. Un apartado de dashboard con 4 tipos de gráficas distintas
2. Un apartado de registro de tickets
3. Saber qué le falta a su apartado de ventas para llevarlo a producción

---

## Estado actual del apartado de ventas

Analicemos el estado actual del apartado de ventas:

- Ya tiene un dashboard de ventas con 4 gráficas: tendencia de ventas, top productos, ventas por hora, distribución de ingresos
- Tiene historial completo con filtros y paginación
- Tiene registro de nueva venta con selección de productos en grid
- Tiene exportación a PDF y Excel
- Tiene métricas principales (ingresos, ventas, unidades, ticket promedio)
- Tiene filtros por fecha

### Lo que SÍ tiene en ventas

- Tendencia de ventas (línea con área)
- Top productos vendidos (barras verticales)
- Ventas por hora (barras)
- Distribución de ingresos (donut/pie)

Sobre "registro de tickets", el usuario menciona esto pero no está claro si se refiere a:

- **Opción A:** Tickets de venta / recibos / comprobantes de venta
- **Opción B:** Un sistema de tickets de soporte/incidencias
- **Opción C:** Un registro de cada transacción como "ticket"

Necesito hacer algunas preguntas aclaratorias al usuario antes de dar un plan completo.

También necesito entender qué significa "llevarlo a producción" para él. Algunas cosas que faltan típicamente:

- Autenticación y autorización
- Manejo de errores robusto
- Validaciones de negocio más completas
- Tests de integración
- Manejo de concurrencia en ventas (race conditions)
- Registro de clientes
- Métodos de pago
- Facturación/comprobantes
- Historial de precios
- Descuentos/promociones
- Reportes más avanzados
- Notificaciones
- Backup de datos
- Logging de operaciones críticas
- Rate limiting
- Manejo de transacciones atómicas

Voy a estructurar mi respuesta con preguntas clarificadoras y luego un análisis de lo que falta.

---

## Conversación inicial

¡Excelente proyecto! Ya revisé tu código y tengo un panorama claro de tu apartado de ventas actual. Me parece que ya tienes bastante avanzado: 4 gráficas (tendencia, top productos, ventas por hora, distribución de ingresos), historial con filtros, paginación, exportación a PDF/Excel y un formulario de registro visual. Antes de darte el plan completo, necesito aclarar algunos puntos:

### Preguntas rápidas para afinar el plan

**1. Sobre "registro de tickets" — ¿a qué te refieres exactamente?**

| Opción | Descripción |
|--------|-------------|
| **A** | Tickets de venta / comprobantes / recibos que se generan e imprimen al registrar una venta |
| **B** | Un sistema de tickets de soporte/incidencias (reportar problemas con ventas, stock, etc.) |
| **C** | Un registro tipo "ticket" donde una venta puede tener múltiples productos (carrito de compras), no solo uno por uno como está ahora |

**2. ¿Qué significa exactamente "llevarlo a producción" para ti?**

- ¿Vas a usarlo en una tienda física real con cajeros reales?
- ¿Necesitas que sea multi-usuario (varios empleados vendiendo al mismo tiempo)?
- ¿Necesitas facturación fiscal o comprobantes legales para tu país?

**3. Sobre las 4 gráficas nuevas que quieres — ¿sabes ya qué tipos te gustaría?**

Por ejemplo: comparación mes vs mes, ventas por categoría, evolución del ticket promedio, mapa de calor por día/hora, etc. ¿Tienes preferencias o quieres que te recomiende las más útiles para retail?

---

## Gap analysis — Lo que falta para producción

Mientras tanto, esto es lo que YA detecté que le falta a tu módulo de ventas para ser "producción-ready":

| Área | Estado actual | ¿Falta? |
|------|---------------|---------|
| **Transacciones atómicas** | La venta y el descuento de stock se hacen en la misma transacción ✅ | Bien |
| **Race conditions** | Si 2 usuarios venden el último producto al mismo tiempo, podrías vender en negativo ❌ | **Falta** |
| **Clientes** | No hay tabla de clientes, todas las ventas son anónimas ❌ | **Falta** |
| **Carrito / múltiples ítems** | Solo se vende 1 producto por operación ❌ | **Falta** |
| **Métodos de pago** | No se registra si fue efectivo, tarjeta, transferencia ❌ | **Falta** |
| **Devoluciones** | El campo `tipo_operacion` existe en la BD pero no hay UI para devolver ❌ | **Falta** |
| **Caja / arqueo** | No hay registro de cuánto debería haber en caja al cierre ❌ | **Falta** |
| **Usuarios / permisos** | No hay autenticación, cualquiera puede vender ❌ | **Falta** |
| **Notas / observaciones** | No se puede agregar una nota a la venta ("cliente pidió cambio", etc.) ❌ | **Falta** |
| **Reimpresión de comprobantes** | No hay tickets/recibos ❌ | **Falta** |
| **Auditoría** | No se registra QUIÉN hizo la venta ❌ | **Falta** |

---

## Respuestas del usuario

> **opcion c** quiero un ticket tipo carrefour simplificado con los datos necesarios.
>
> Y quiero que ese ticket se guarde en la base de datos justo con todos sus productos juntos no como ahora que se guarda uno por uno.
>
> Que alguien pueda descargar la app y la pueda usar.
> Es un proyecto de la uni pero quiero hacerlo lo mas profesional posible.
>
> Me dice que tenemos 4 graficas ya no, bueno si la tenemos dejamos esas y agrega todas las que tu creas necesarias.
>
> Quiero que el apartado de nueva venta sea asi como la imagen identica asi

### Interpretación de requerimientos

El usuario quiere:

1. Un sistema de ventas tipo **TPV (Terminal Punto de Venta)** como el de la imagen (estilo Carrefour / TPV de bar)
2. Tickets que se guarden en BD con todos los productos juntos (no ventas individuales como ahora)
3. Que alguien pueda descargar la app y usarla (proyecto de uni pero profesional)
4. Mantener las 4 gráficas actuales y agregar más las que yo considere necesarias
5. La vista de nueva venta debe ser idéntica a la imagen: panel izquierdo con lista de productos del ticket, panel derecho con grid de categorías/productos, teclado numérico, botones de acción (cobro, imprimir, etc.)

Esto es un cambio **ARQUITECTURAL** importante. Necesito entender bien:

- Cómo están las entidades actuales (ya las vi)
- Qué necesita cambiar en la BD (tabla de tickets, líneas de ticket)
- Qué necesita cambiar en la API
- Cómo hacer el UI tipo TPV

Lo que el usuario quiere:

- Nueva arquitectura de ventas: De ventas individuales a **TICKETS** con múltiples líneas (carrito)
- UI tipo TPV como la imagen (grid de productos a la derecha, ticket a la izquierda, teclado numérico, botones de acción)
- Ticket simplificado tipo Carrefour guardado en BD
- Mantener las 4 gráficas actuales y agregar más útiles
- Proyecto profesional para la uni, que alguien pueda descargar y usar

Lo que detecté que falta para producción:

- Race conditions en ventas
- No hay tabla de clientes
- No hay métodos de pago
- No hay usuarios/permisos
- No hay auditoría (quién vendió)
- No hay tickets físicos/descargables
- No hay devoluciones UI
- No hay caja/arqueo

Para el plan, necesito proponer:

- Cambios en la base de datos (nuevas entidades: `Ticket`, `TicketLinea`, posiblemente `Cliente`, `MetodoPago`)
- Cambios en schemas Pydantic
- Cambios en la API (nuevos endpoints para tickets)
- Refactorización del módulo de ventas (vista de Streamlit)
- Nuevas gráficas
- Sistema de impresión/descarga de tickets
- Manejo de estado para el carrito

---

## Preguntas de tradeoffs

### Tradeoffs clave

**¿Mantener la tabla Venta actual o migrar todo a Ticket?**

| Opción | Descripción |
|--------|-------------|
| **A** | Deprecar `Venta` y crear `Ticket`/`TicketLinea` (más limpio, pero pierde datos históricos a menos que migremos) |
| **B** | Mantener `Venta` como "líneas de ticket" y agregar `Ticket` como cabecera (más compatible, pero el modelo actual de `Venta` no tiene foreign key a `Ticket`) |
| **C** | Crear `Ticket` y `TicketLinea` nuevos, mantener `Venta` como legacy (recomendado para no romper nada) |

Dado que es un proyecto de uni y quieren algo profesional, lo mejor es crear las nuevas tablas y dejar `Venta` como legacy, o hacer una migración. Pero como no hay sistema de migraciones (usan `create_all`), podríamos simplemente agregar las nuevas tablas y dejar las viejas. SQLite no es tan estricto.

**¿Usuarios/Autenticación?** Para un TPV real necesitas saber quién cobró. Pero como es un proyecto de uni y quiere que "alguien pueda descargar y usar", quizás un modo simple: seleccionar cajero al inicio o no usar autenticación.

**¿Métodos de pago?** Efectivo, tarjeta, bizum... esto es clave para un TPV.

**¿Clientes?** ¿Las ventas son anónimas o quieren poder asociar a un cliente?

**¿Stock en tiempo real?** El TPV debe bloquear productos sin stock.

---

## Plan técnico propuesto

### Fase 1: Arquitectura de Datos (Backend)

**Nuevas entidades:** `Ticket`, `TicketLinea`

**Nuevos schemas:** `TicketCreate`, `TicketResponse`, `TicketLineaCreate`, `TicketLineaResponse`

**Nuevos endpoints en API:**
- `POST /tickets`
- `GET /tickets`
- `GET /tickets/{id}`

**Servicio de negocio** para crear ticket (transacción atómica: insertar ticket + líneas + actualizar inventario)

**Validación de stock** antes de confirmar (con manejo de race conditions usando `SELECT FOR UPDATE` o similar en SQLite)

### Fase 2: TPV UI (Frontend Streamlit)

Refactorizar `app/views/ventas.py` completamente.

**Layout tipo TPV:**

```
Columna izquierda (30-35%):  Ticket actual
  - Lista de productos agregados, cantidad, precio, total
  - Teclado numérico
  - Total del ticket
  - Botones de acción (Cobrar, Cancelar, Imprimir)

Columna derecha (65-70%):  Catálogo de productos
  - Grid de categorías arriba
  - Grid de productos de la categoría seleccionada abajo
```

**Estado del carrito** en `session_state`

**Flujo:**
1. Clic categoría → muestra productos
2. Clic producto → agrega al ticket
3. Modificar cantidad
4. Cobrar

### Fase 3: Ticket Simplificado

- Diseño tipo Carrefour (cabecera con fecha, número de ticket, items, total, método de pago, cambio)
- Guardar en BD
- Opción de descargar/imprimir (HTML para imprimir desde navegador o PDF)

### Fase 4: Dashboard de Ventas Mejorado

**Mantener las 4 actuales:**
1. Tendencia de ventas (línea temporal)
2. Top productos vendidos (barras)
3. Ventas por hora (barras)
4. Distribución de ingresos (donut)

**Agregar:**
5. Ventas por Categoría
6. Evolución del Ticket Promedio
7. Top Productos por Ingresos
8. Mapa de Calor de ventas por día/hora
9. Comparativa mes actual vs anterior

### Fase 5: Producción-Ready Features

- Métodos de pago (Efectivo, Tarjeta, Transferencia)
- Cálculo de cambio si es efectivo
- Manejo de race conditions en stock
- Botón de "Devolución"
- Registro de qué cajero atendió

### Fase 6: Empaquetado y Distribución

- `setup.py` o `pyproject.toml`
- Script de inicio
- README con instrucciones claras
- Archivo `.spec` para PyInstaller (opcional)

---

## Preguntas al usuario

Dado que estoy en modo planificación, debo presentar este plan al usuario y esperar su aprobación antes de ejecutar.

### Alcance del TPV

¿Quieres TODAS las funciones de la imagen (descuentos, cambiar precio, dividir ticket, mesas) o solo lo esencial?

| Función | ¿Incluir? | Complejidad |
|---------|-----------|-------------|
| Agregar/quitar productos del ticket | ✅ Esencial | Baja |
| Teclado numérico para cantidades | ✅ Esencial | Baja |
| Cobrar Efectivo / Tarjeta | ✅ Esencial | Media |
| Calcular cambio (efectivo) | ✅ Esencial | Baja |
| Descuento % (DTO%) | ⚠️ ¿Sí o no? | Media |
| Descuento € fijo (DTO €) | ⚠️ ¿Sí o no? | Media |
| Cancelar línea (CAN) / Limpiar todo (CLR) | ✅ Esencial | Baja |
| Cambiar precio manual (PREC) | ⚠️ ¿Sí o no? | Media |
| Dividir ticket | ❌ Recomiendo NO | Alta |
| Mesas (Cambiar Mesa) | ❌ Recomiendo NO | Alta |

Mi recomendación: Implementar las **"Esenciales"** + Descuentos si los necesitas. Omitir Mesas y Dividir ticket por ahora (son específicos de restaurantes, no de retail tipo Carrefour).

### Datos históricos

Tu BD actual tiene ventas guardadas como registros sueltos en la tabla `ventas`. Las opciones son:

| Opción | Descripción |
|--------|-------------|
| **A** | Migrar: Convertir ventas viejas en tickets retroactivamente (más trabajo, datos unificados) |
| **B** | Dejar legacy: Las tablas `ventas` se quedan como están. El nuevo TPV usa `ticket`/`ticket_linea`. El dashboard leerá de AMBAS tablas para las estadísticas, o solo de la nueva |
| **C** | Borrar y empezar de cero: Limpiar la tabla `ventas` y empezar fresh (solo si no te importan los datos de prueba) |

Mi recomendación: **Opción B**. Es la más segura y rápida.

### Autenticación de cajeros

Para un proyecto de uni, podemos hacer algo simple:

| Opción | Descripción |
|--------|-------------|
| **A (Simple)** | Al entrar a "Ventas", hay un selectbox "Cajero: [Juan, María, Admin]". Se guarda en el ticket. Sin passwords |
| **B (Completa)** | Login con usuario/contraseña, roles (admin, cajero), etc. |
| **C (Ninguna)** | Todo anónimo, sin registrar quién vendió |

Mi recomendación: **Opción A**. Es profesional, útil para auditoría, y no complica el flujo con logins.

---

## Plan consolidado final

> El usuario respondió:
>
> 1. **Funciones del TPV:** Solo lo esencial (Agregar/quitar productos, teclado numérico, cobrar efectivo/tarjeta, calcular cambio, cancelar/limpiar). **NO** descuentos, **NO** cambiar precio manual, **NO** dividir ticket, **NO** mesas.
> 2. **Datos históricos:** Opción C — Borrar tabla `ventas` y empezar de cero con la nueva arquitectura de tickets.
> 3. **Autenticación:** Opción A — Selectbox simple de cajero al entrar al TPV, sin passwords.
>
> Además:
> - Tiene imágenes en `docs/productos` → las mostraremos en el grid
> - Nombres de cajeros: **andres, edu, carlos, alberto, irrael, YioQueSe, fernando, ernesto, raul**
> - Teclado numérico **funcional** → sí, clic en línea + tecla cambia cantidad
> - Confirmó que puedo borrar ambas bases de datos (`markettalento.db` e `inventario.db`)

---

## ✅ Plan Técnico Final: TPV MarkeTTalento

### Alcance confirmado

| Decisión | Implementación final |
|----------|----------------------|
| **Funciones TPV** | Esenciales: carrito, teclado numérico funcional, cobro efectivo/tarjeta, cálculo de cambio, limpiar/cancelar línea |
| **Datos históricos** | Opción C: Borrar ambas BDs (`markettalento.db` e `inventario.db`). Nueva arquitectura desde cero |
| **Autenticación** | Opción A: Selectbox de cajero sin password |
| **Imágenes productos** | Sí, usar archivos de `docs/productos/` en el grid del TPV |
| **Cajeros** | `["andres", "edu", "carlos", "alberto", "irrael", "YioQueSe", "fernando", "ernesto", "raul"]` |
| **Teclado numérico** | Funcional: clic en línea del ticket → presionar número en teclado → cantidad cambia |

---

## 🗂️ Fases de Implementación

### Fase 1: Backend — Nueva Arquitectura de Tickets

**Objetivo:** Reemplazar el modelo de ventas sueltas por tickets completos con múltiples líneas, transacciones atómicas y control de concurrencia.

**Archivos a crear/modificar:**

| # | Archivo | Acción | Detalle |
|---|---------|--------|---------|
| 1 | `src/dominio/entidades/entidades.py` | Modificar | Crear `Ticket` (cabecera) y `TicketLinea` (detalle). Eliminar/deprecar `Venta`. Relaciones: `Ticket` 1:N `TicketLinea`, `TicketLinea` N:1 `Producto` |
| 2 | `src/aplicacion/schemas/schemas.py` | Modificar | Schemas `TicketCreate`, `TicketLineaCreate`, `TicketResponse`, `TicketLineaResponse` |
| 3 | `src/api/tickets.py` | Crear | Endpoints: `POST /tickets` (transacción atómica con `with_for_update()`), `GET /tickets`, `GET /tickets/{id}`, `DELETE /tickets/{id}` (anular + reintegrar stock) |
| 4 | `src/api/router.py` | Modificar | Incluir router `/tickets` |
| 5 | `src/core/database/database.py` | Modificar | Asegurar que `Base.metadata.create_all` genere las nuevas tablas |

**Lógica clave del `POST /tickets`:**

```
BEGIN transaction
SELECT ... FROM inventario WHERE producto_id IN (...) FOR UPDATE (bloquea filas)
Validar stock suficiente para cada línea
Generar numero_ticket = LPAD(MAX(numero_ticket) + 1, 6, '0')
Insertar Ticket
Insertar cada TicketLinea
UPDATE inventario SET cantidad = cantidad - X WHERE producto_id = Y para cada línea
COMMIT (o ROLLBACK si falla algo)
```

---

### Fase 2: Frontend — UI TPV (Layout tipo la imagen)

**Objetivo:** Reemplazar completamente la vista de ventas por un TPV profesional de dos paneles.

**Archivos a modificar:**

| # | Archivo | Acción | Detalle |
|---|---------|--------|---------|
| 6 | `app/views/ventas.py` | Reescribir | Nuevo layout TPV completo |
| 7 | `app/utils/state.py` | Modificar | Variables de `session_state` para carrito, cajero, categoría activa |
| 8 | `app/styles/ventas.css` | Modificar | Estilos para teclado numérico, grid de productos, tarjetas |

**Layout propuesto (3 tabs: Dashboard | Historial | TPV):**

**Tab "TPV" — Diseño de dos paneles:**

| Panel Izquierdo (35%) | Panel Derecho (65%) |
|-----------------------|---------------------|
| Header: Cajero + Fecha/Hora | Fila superior: Grid de **Categorías** clickeables (4-5 cols) |
| Lista de líneas del ticket: `Cant × Producto = Subtotal` | Grid de **Productos** de la categoría activa (tarjetas con imagen/nombre/precio/stock) |
| Botones por línea: `[-]` `[+]` `[🗑️]` | Clic en producto → se agrega al carrito (o incrementa cantidad) |
| Teclado numérico (HTML/CSS custom) para cantidades | Productos sin stock: opacos y no clickeables |
| **Total grande** | |
| Botones: `💶 Cobrar Efectivo` `💳 Cobrar Tarjeta` `🧹 Limpiar` | |

**Flujo de cobro (modal/expander):**

1. Clic en "Cobrar"
2. Seleccionar método de pago (efectivo/tarjeta/transferencia)
3. Si efectivo: input "Entrega €" → calcula y muestra cambio automáticamente
4. Checkbox "Confirmar cobro"
5. Botón "✅ Finalizar Venta" → llama a `POST /api/v1/tickets`
6. Si éxito: muestra ticket simplificado en pantalla + botón "Descargar ticket" + "Nueva venta"

---

### Fase 3: Ticket Simplificado (Vista e Impresión)

**Objetivo:** Generar un ticket tipo Carrefour que se pueda ver en pantalla y descargar.

**Diseño del ticket:**

```
------------------------------------------
        MARKE TTALENTO
    Ticket N° 00042
    07/05/2026  14:32
    Cajero: andres
------------------------------------------
1 x Café Solo           1,30 €
2 x Coca Cola           5,00 €
------------------------------------------
TOTAL:                  6,30 €
Metodo: Efectivo
Entrega:        10,00 €
Cambio:          3,70 €
------------------------------------------
    ¡Gracias por su visita!
------------------------------------------
```

**Implementación:** Función dentro de `app/views/ventas.py` que renderice el ticket en HTML puro + botón `st.download_button` para descargar como `.txt` formateado.

---

### Fase 4: Dashboard de Ventas — 10 Gráficas + Historial

**Objetivo:** Adaptar el dashboard existente a la nueva arquitectura de tickets y agregar gráficas nuevas.

**Tab "Dashboard" — Métricas y gráficas:**

**Mantener las 4 actuales (adaptadas a tickets):**
1. 📈 Tendencia de Ventas (línea temporal de ingresos)
2. 🥇 Top Productos Vendidos (por unidades)
3. ⏰ Ventas por Hora (barras)
4. 📊 Distribución de Ingresos (donut por rangos)

**Agregar 6 nuevas:**
5. 🏷️ **Ventas por Categoría** (donut) — qué rubro vende más
6. 📉 **Evolución del Ticket Promedio** (línea temporal)
7. 💶 **Top Productos por Ingresos** (barras horizontales en €)
8. 🔥 **Mapa de Calor** (heatmap tabla) — día de semana vs hora
9. 💳 **Métodos de Pago** (barras horizontales) — efectivo vs tarjeta
10. 📅 **Comparativa Mes Actual vs Anterior** (barras agrupadas)

**Tab "Historial":**
- Lista de tickets (cabecera expandible con líneas)
- Filtros: fecha, cajero, método de pago, rango de total
- Paginación
- Botón "❌ Anular" (solo tickets del día, por seguridad)
- Exportar a Excel

---

### Fase 5: Producción-Ready

| Feature | Implementación |
|---------|---------------|
| **Número de ticket autoincremental** | Lógica en backend: `MAX(numero_ticket) + 1` |
| **Stock en tiempo real** | Grid de productos consulta stock actual; sin stock = deshabilitado |
| **Anulación de ticket** | Botón en historial; backend reintegra stock y marca como "anulado" |
| **Cajero en ticket** | Selectbox al entrar al TPV; se envía en cada ticket |
| **Reset de datos** | Instrucciones para borrar `data/markettalento.db` y recrear |

---

## 📁 Archivos a Modificar/Crear (Resumen)

### Nuevos
- `src/api/tickets.py`

### Modificaciones mayores (rewrite)
- `app/views/ventas.py`

### Modificaciones menores
- `src/dominio/entidades/entidades.py`
- `src/aplicacion/schemas/schemas.py`
- `src/api/router.py`
- `app/utils/state.py`
- `app/styles/ventas.css`

### Deprecados (se dejan pero no se usan)
- `src/api/ventas.py` (legacy)

---

## ⚠️ Acciones Destructivas Confirmadas

Antes de la primera ejecución, se realizarán estas acciones destructivas:

| Acción | Justificación |
|--------|---------------|
| `rm data/markettalento.db` | Legacy, ya no es compatible con nuevo modelo |
| `rm data/inventario.db` | Legacy, duplicada |
| `src/api/ventas.py` queda inactivo | Ya no se usa, reemplazado por `tickets.py` |
| Tabla `ventas` no se migra | El usuario confirmó que no le importan los datos de prueba |

---

## 🚀 Orden de Implementación

Para minimizar errores y permitir pruebas en cada etapa:

1. **Backend primero:** Entidades → Schemas → API Tickets → Router
2. **Probar backend:** Verificar con `curl` o Postman que `POST /tickets` funciona y descuenta stock correctamente
3. **Frontend TPV:** Layout básico → Grid categorías/productos → Carrito → Teclado numérico → Cobro → Ticket
4. **Dashboard:** Adaptar métricas a nueva tabla + agregar nuevas gráficas
5. **Historial:** Lista de tickets + filtros + anulación
6. **Polish:** CSS, validaciones, manejo de errores, descarga de ticket

---

## ❓ Confirmación Final

Antes de empezar a escribir código, confirma que estás de acuerdo con:

1. **Borrar ambas bases de datos** (`data/markettalento.db` e `inventario.db`) para regenerarlas desde cero.
2. **El layout del TPV** descrito arriba (panel izquierdo ticket + derecho productos/categorías).
3. **Las 10 gráficas** del dashboard.
4. **Los 9 nombres de cajeros** hardcodeados en el selectbox.

> **Si todo está correcto, dime "Ejecutar" y comenzamos inmediatamente con la Fase 1: Backend.** 🚀

---

*Documento generado automáticamente para el proyecto MarkeTTalento.*
