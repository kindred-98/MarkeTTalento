# 📋 MarkeTTalento - Lista de Tareas Pendientes

> **Última actualización:** Mayo 2026  
> **Estado:** En desarrollo activo

---

## 🔴 CRÍTICO - Arreglar Inmediatamente

### Problemas de Funcionamiento

| # | Problema | Descripción | Prioridad |
|---|----------|-------------|-----------|
| 1 | **Caching agresivo** | Los datos no se actualizan tras crear/editar/eliminar. El usuario ve información desactualizada. | 🔴 Alta |
| 2 | **Navegación del sidebar** | Botones de menú no responden correctamente con el caching implementado. | 🔴 Alta |
| 3 | **Validaciones de formularios** | Formularios aceptan datos inválidos (precios negativos, stock negativo, SKU duplicados). | 🔴 Alta |
| 4 | **Manejo de errores API** | Si la API falla, la app no muestra mensajes amigables al usuario. | 🔴 Alta |
| 5 | **Paginación** | Bugs al cambiar entre páginas en listados largos. | 🟡 Media |

---

## 🟡 IMPORTANTE - Funcionalidad Faltante

### Testing

- [ ] **Tests Unitarios**
  - [ ] Probar funciones en `app/logic/`
  - [ ] Probar validaciones de entrada
  - [ ] Probar cálculos de inventario

- [ ] **Tests de Integración**
  - [ ] Flujo completo: crear producto → ver en inventario → editar → eliminar
  - [ ] Flujo de ventas: registrar venta → actualizar stock → ver en historial

- [ ] **Tests de API**
  - [ ] Todos los endpoints responden correctamente
  - [ ] Manejo de errores HTTP (404, 500, etc.)
  - [ ] Validación de schemas

### Validaciones Robustas

- [ ] **Productos**
  - [ ] Validar SKU único (no duplicados)
  - [ ] Validar precio mayor a 0
  - [ ] Validar stock máximo mayor a 0
  - [ ] Validar código de barras (formato correcto)

- [ ] **Inventario**
  - [ ] No permitir stock negativo
  - [ ] Validar ubicación no vacía

- [ ] **Ventas**
  - [ ] No permitir vender más del stock disponible
  - [ ] Validar cantidad mayor a 0

---

## 🟢 MEJORAS - UX/UI

### Feedback Visual

- [ ] **Indicadores de carga (spinners)**
  - [ ] Al cargar datos del dashboard
  - [ ] Al guardar productos
  - [ ] Al procesar imágenes con IA

- [ ] **Mensajes de confirmación**
  - [ ] "¿Estás seguro de eliminar este producto?"
  - [ ] "¿Deseas salir sin guardar cambios?"

- [ ] **Toast notifications**
  - [ ] Éxito: "Producto creado correctamente"
  - [ ] Error: "No se pudo conectar con la API"
  - [ ] Advertencia: "Stock bajo para este producto"

### Mejoras de Flujo

- [ ] **Recuperación de errores**
  - [ ] Reintentos automáticos si falla la API
  - [ ] Guardar datos en localStorage antes de enviar
  - [ ] Sincronización cuando vuelve la conexión

- [ ] **Optimización de rendimiento**
  - [ ] Lazy loading de imágenes
  - [ ] Virtualización de listas largas
  - [ ] Compresión de datos

---

## 📊 Roadmap por Fases

### FASE 1: Estabilidad (Semana 1-2)
**Objetivo:** Que todo funcione sin errores críticos

1. Arreglar caching (reducir TTL o eliminar temporalmente)
2. Arreglar navegación del sidebar
3. Implementar validaciones básicas en formularios
4. Mejorar manejo de errores con mensajes amigables

### FASE 2: Testing (Semana 3-4)
**Objetivo:** Tener confianza en que nada se rompe

1. Escribir tests unitarios para lógica de negocio
2. Crear tests de integración para flujos principales
3. Configurar CI/CD con GitHub Actions
4. Cobertura de código > 80%

### FASE 3: UX Polish (Semana 5-6)
**Objetivo:** Experiencia de usuario profesional

1. Agregar spinners de carga
2. Implementar confirmaciones y toasts
3. Mejorar feedback visual (animaciones, transiciones)
4. Optimizar rendimiento de carga

### FASE 4: Features Avanzadas (Futuro)
**Objetivo:** Funcionalidades enterprise

1. Autenticación de usuarios
2. Roles y permisos
3. Reportes exportables (PDF, Excel avanzado)
4. Integración con otros sistemas

---

## 🐛 Bugs Conocidos

### Por Arreglar

- [ ] **Issue #1:** Los filtros no funcionan correctamente con el cache implementado
- [ ] **Issue #2:** Algunos gráficos de Plotly muestran warning de deprecación
- [ ] **Issue #3:** La paginación reinicia al cambiar filtros

### En Investigación

- [ ] **Issue #4:** Rendimiento lento con más de 100 productos
- [ ] **Issue #5:** Memoria alta al usar visión artificial repetidamente

---

## 💡 Recomendaciones del Tutor

> **Regla de oro:** No agregar nuevas features hasta que lo existente funcione perfectamente.

### Prioridad de Trabajo

1. **NO** agregar más funcionalidades nuevas
2. **SÍ** arreglar los bugs críticos (Fase 1)
3. **SÍ** escribir tests (Fase 2)
4. **DESPUÉS** pulir UX (Fase 3)

### Cómo Reportar Problemas

Cuando encuentres un bug, documenta:
1. **Qué botón/función** no funciona
2. **Qué esperabas** que pasara
3. **Qué pasó realmente**
4. **Mensaje de error** (si hay)

---

## ✅ Completado Recientemente

- [x] Modularización completa del código
- [x] Sistema de logging profesional
- [x] Manejo de errores global
- [x] Protección de datos sensibles (.gitignore)
- [x] Soporte para múltiples bases de datos
- [x] Caching básico implementado

---

**Nota:** Este documento se actualiza conforme avanzamos. Última revisión: Mayo 2026.
