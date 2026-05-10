# Inspector de Producto

## Resumen Ejecutivo

El modulo de **Inspector de Producto** transforma el antiguo buscador de codigos de barras en una **ficha tecnica inteligente** que permite escanear un producto (por codigo de barras, SKU o nombre) y obtener toda su informacion de negocio en una sola pantalla:

- Ficha completa del producto (foto, precio, categoria, proveedor)
- Stock actual con estado visual (OK/BAJO/CRITICO)
- Prediccion ML (consumo, dias hasta agotarse, tendencia)
- Acciones rapidas de ajuste de stock (+1, +5, -1, -5)
- Historial de ventas recientes (ultimos tickets)

Este modulo cierra el circulo del sistema: **Ventas (TPV) -> Predicciones (ML) -> Accion (Inspector)**.

---

## Arquitectura

```
Usuario escanea/escribe codigo
       ↓
[Frontend Streamlit] app/views/barcode.py
       ↓
Busqueda por: barcode | SKU | nombre
       ↓
├─ GET /api/v1/productos/barcode/{codigo}  → Ficha del producto
├─ GET /api/v1/inventario/{producto_id}    → Stock actual
├─ GET /api/v1/prediccion/producto/{id}    → Prediccion ML
└─ GET /api/v1/tickets/historial/{id}      → Ultimas ventas
       ↓
[Frontend] Renderiza en 4 secciones:
   ├─ Fila 1: Foto + Ficha + Stock
   ├─ Fila 2: Prediccion ML (4 metricas)
   ├─ Fila 3: Acciones rapidas
   └─ Fila 4: Historial de ventas
```

---

## Diferencia con el sistema anterior

| Aspecto | Antes (Barcode simple) | Ahora (Inspector inteligente) |
|---------|------------------------|-------------------------------|
| Funcion | Buscar y mostrar nombre/precio | Ficha completa + stock + ML + historial |
| Valor | Nulo (ya estaba en el TPV) | Decision de negocio en 2 segundos |
| Datos | Solo productos | Productos + Inventario + Predicciones + Tickets |
| Acciones | Ninguna | Ajustar stock al vuelo |
| Tecnologia | Text input + lista filtrada | 4 endpoints API + cache + CSS |

---

## API Endpoints Nuevos/Modificados

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/api/v1/productos/barcode/{codigo}` | GET | Busca producto por codigo de barras |
| `/api/v1/inventario/{producto_id}` | GET | Obtiene stock y ubicacion de un producto |
| `/api/v1/tickets/historial/{producto_id}` | GET | Historial de tickets con ese producto (limite configurable) |

**Endpoints reutilizados:**
| Endpoint | Uso en Inspector |
|----------|------------------|
| `/api/v1/productos` | Busqueda por nombre (filtra en frontend) |
| `/api/v1/productos/sku/{sku}` | Busqueda directa por SKU |
| `/api/v1/prediccion/producto/{id}` | Prediccion ML de demanda |
| `/api/v1/inventario/{producto_id} (POST)` | Actualizar stock tras accion rapida |

---

## Frontend: Secciones

### Seccion 1: Barra de Busqueda
- **Input de texto:** Codigo de barras, SKU o nombre parcial.
- **Selector:** "Buscar por: Codigo de barras | SKU | Nombre".
- **Boton "🔍 Buscar":** Ejecuta la busqueda.

### Seccion 2: Fila de Ficha (3 columnas)

**Columna 1 - Foto:**
- Muestra `imagen_url` del producto si existe.
- Fallback: icono 📦 sobre fondo neutro.

**Columna 2 - Ficha Tecnica:**
- Nombre del producto (titulo).
- SKU e ID.
- Precio de venta (destacado en verde).
- Unidad de medida.
- Stock minimo configurado.
- Nombre del proveedor.

**Columna 3 - Stock:**
- Cantidad actual en numeros grandes.
- Badge de estado:
  - **CRITICO** (rojo): stock <= 2
  - **BAJO** (naranja): stock <= stock_minimo
  - **OK** (verde): stock > stock_minimo
- Ubicacion en almacen.

### Seccion 3: Prediccion ML (4 tarjetas)
- **Consumo promedio:** uds/dia (ej: 1.5).
- **Dias hasta agotarse:** calculo stock/consumo (ej: 8.0).
- **Tendencia:** ALZA / BAJA / ESTABLE.
- **Estado stock:** CRITICO / BAJO / MODERADO / ADECUADO.

### Seccion 4: Acciones Rapidas
- Botones: `+1`, `+5`, `-1`, `-5`.
- Cada boton hace POST a `/api/v1/inventario/{id}` con el nuevo stock.
- Boton "📊 Inventario" (deshabilitado, tooltip indica ir al menu lateral).

### Seccion 5: Historial de Ventas
- Tabla con ultimos 10 tickets donde aparecio el producto.
- Columnas: Fecha, Cajero, Cantidad, Precio unitario, Ticket #, Total ticket.
- Ordenado descendente por fecha.

---

## Flujo de Uso

### Escenario: Encargado revisa stock de Coca-Cola

1. Ve a **🔍 Inspector** en el sidebar.
2. Escribe `CC330` (SKU de Coca-Cola).
3. Selecciona "SKU" y pulsa Buscar.
4. Ve en pantalla:
   - Foto de la lata, precio €2.50, categoria Bebidas.
   - Stock actual: 12 uds, estado OK.
   - Prediccion: consume 1.5 uds/dia, se agota en 8 dias, tendencia ALZA.
5. Decide que no hace falta reponer aun.
6. Si quisiera ajustar: pulsa `+5` y el stock pasa a 17.

### Escenario: Reponer leche urgentemente

1. Escaner lee codigo de barras de Leche Asturiana.
2. Inspector muestra: Stock 2 uds, estado CRITICO.
3. Prediccion: 0.1 dias hasta agotarse.
4. Encargado pulsa `+10` (via Inventario) o va a proveedores.

---

## Estructura de Archivos

```
src/
  api/
    productos.py          → GET /barcode/{codigo} (nuevo)
    inventario.py         → GET /{producto_id} (movido antes de rutas estaticas)
    tickets.py            → GET /historial/{producto_id} (nuevo)
app/
  views/
    barcode.py            → Reescrito completo como Inspector
  components/
    sidebar.py            → Renombrado "Barcode" → "Inspector"
  main.py               → Actualizado routing
```

---

## Registro de Construccion (Bitacora)

### Fase 1: Backend - Endpoints nuevos
- **src/api/productos.py:**
  - Agregado `GET /barcode/{codigo}` que busca por `codigo_barras` en la tabla `productos`.
  - Devuelve 404 si no existe.
- **src/api/inventario.py:**
  - Movido `GET /{producto_id}` al **principio** del router, antes de rutas estaticas.
  - Motivo: FastAPI registra rutas en orden; `/{id}` al final evita que "resumen" se interprete como ID.
  - Endpoint devuelve dict serializable: `{producto_id, cantidad, ubicacion, fecha_ultima_actualizacion}`.
- **src/api/tickets.py:**
  - Agregado `GET /historial/{producto_id}` con parametro `limite` (default 10, max 50).
  - Join entre `TicketLinea` y `Ticket`, filtra por `producto_id` y `estado == "completado"`.
  - Ordena por `Ticket.fecha DESC`.

### Fase 2: Frontend - Reescritura completa
- **app/views/barcode.py:**
  - Funcion `render()`: barra de busqueda con selector de tipo.
  - Funcion `_buscar_producto()`: logica de busqueda por barcode/SKU/nombre.
  - Funcion `_mostrar_ficha_producto()`: renderizado de las 5 secciones.
  - Funcion `_obtener_inventario()`: llamada a API de stock.
  - Funcion `_obtener_prediccion()`: llamada a API de predicciones ML.
  - Funcion `_obtener_historial()`: llamada a API de historial.
  - Funcion `_ajustar_stock()`: POST para actualizar cantidad.

### Fase 3: Navegacion
- **app/components/sidebar.py:**
  - Cambiado label de menu de `"🔍 Barcode"` a `"🔍 Inspector"`.
- **app/main.py:**
  - Actualizado `elif menu == "🔍 Inspector":`.

### Fase 4: Bug fixes
- **Problema:** `st.page_link("pages/inventario.py", ...)` crasheaba con `KeyError: 'url_pathname'`.
  - **Causa:** `st.page_link` solo funciona en apps Streamlit multipagina (carpeta `pages/`).
  - **Solucion:** Reemplazado por `st.button` deshabilitado con tooltip.
- **Problema:** `GET /inventario/resumen` devolvia 422 Unprocessable Entity.
  - **Causa:** `GET /{producto_id}` estaba al principio del archivo, capturando "resumen" como ID.
  - **Solucion:** Reordenadas rutas en `src/api/inventario.py`:
    1. Estaticas primero: `/resumen`, `/bajo-stock`, `/recomendaciones`
    2. Dinamicas al final: `/{producto_id}`
- **Problema:** `GET /inventario/{id}` devolvia objeto SQLAlchemy no serializable.
  - **Solucion:** Se construye dict manual con campos basicos en vez de devolver la entidad ORM.
- **Problema:** `AttributeError: 'list' object has no attribute 'get'` en Dashboard.
  - **Causa:** `api_get("/inventario/resumen")` devolvia lista vacia `[]` en vez de dict.
  - **Solucion:** Validacion `if not isinstance(resumen, dict): resumen = {}` en `dashboard.py`.

### Fase 5: Tests
- `GET /productos/barcode/999999` → 404 correcto.
- `GET /productos/sku/PROD001` → 200 "Leche Asturiana".
- `GET /inventario/1` → 200 `{cantidad: 2, ubicacion: "Almacen A"}`.
- `GET /tickets/historial/1` → 200, 3 registros.
- `POST /inventario/1` → 200, stock actualizado.
- Dashboard carga sin errores tras fix de tipo.

---

## Decisiones Tecnicas Clave

1. **Busqueda flexible:** Soporta barcode, SKU y nombre parcial. El usuario no necesita saber exactamente que campo tiene.
2. **Flujo 100% API:** El frontend nunca importa servicios Python. Toda comunicacion es HTTP.
3. **Lazy loading de datos:** La ficha, stock, prediccion e historial se cargan solo tras la busqueda, no al entrar a la pagina.
4. **Acciones inmediatas:** Los botones `+1/+5/-1/-5` actualizan stock sin recargar la pagina (`st.rerun()`).
5. **Reutilizacion maxima:** Se usan endpoints existentes de Predicciones y Tickets. Solo se crearon 3 endpoints nuevos.
6. **Orden de rutas FastAPI:** Las rutas estaticas (`/resumen`) deben ir siempre antes que las dinamicas (`/{id}`) para evitar colisiones.

---

## Limitaciones

- **Sin escaner fisico:** El input es manual. Para integrar un lector de codigo de barras USB habria que capturar eventos de teclado (no soportado nativamente por Streamlit).
- **Prediccion requiere datos:** Si el producto no tiene ventas suficientes, la prediccion ML devuelve null y las tarjetas muestran "Sin datos".
- **Ajuste de stock sin confirmacion:** Los botones `+1/+5` aplican inmediatamente sin modal de confirmacion. Esto es intencional para rapidez, pero podria agregarse una confirmacion si hay riesgo de errores.
