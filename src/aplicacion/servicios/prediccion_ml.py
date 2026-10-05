"""
Servicio de Machine Learning para predicción de demanda e inteligencia de negocio.
Usa scikit-learn para regresión lineal y numpy para análisis estadístico.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
import numpy as np
from collections import defaultdict

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from src.dominio.repositorios.repositorios import TicketRepositorio, ProductoRepositorio, InventarioRepositorio
from src.implementaciones.repositorios_impl import SQLAlchemyTicketRepositorio, SQLAlchemyProductoRepositorio, SQLAlchemyInventarioRepositorio


class PrediccionDemandaResultado:
    """Resultado de predicción de demanda para un producto."""
    def __init__(self, producto_id: int, producto_nombre: str,
                 historico: List[Dict], pronostico: List[Dict],
                 consumo_promedio: float, dias_hasta_agotarse: float,
                 tendencia: str, stock_actual: int):
        self.producto_id = producto_id
        self.producto_nombre = producto_nombre
        self.historico = historico
        self.pronostico = pronostico
        self.consumo_promedio = consumo_promedio
        self.dias_hasta_agotarse = dias_hasta_agotarse
        self.tendencia = tendencia
        self.stock_actual = stock_actual

    @property
    def estado_stock(self) -> str:
        if self.dias_hasta_agotarse <= 2:
            return "CRITICO"
        elif self.dias_hasta_agotarse <= 7:
            return "BAJO"
        elif self.dias_hasta_agotarse <= 14:
            return "MODERADO"
        return "ADECUADO"

    def to_dict(self) -> Dict:
        return {
            "producto_id": self.producto_id,
            "producto_nombre": self.producto_nombre,
            "historico": self.historico,
            "pronostico": self.pronostico,
            "consumo_promedio_diario": round(self.consumo_promedio, 2),
            "dias_hasta_agotarse": round(self.dias_hasta_agotarse, 1),
            "tendencia": self.tendencia,
            "estado_stock": self.estado_stock,
            "stock_actual": self.stock_actual,
        }


class AlertaReposicion:
    """Alerta para reponer stock."""
    def __init__(self, producto_id: int, nombre: str, stock_actual: int,
                 dias_hasta_agotarse: float, cantidad_recomendada: int, nivel: str):
        self.producto_id = producto_id
        self.nombre = nombre
        self.stock_actual = stock_actual
        self.dias_hasta_agotarse = dias_hasta_agotarse
        self.cantidad_recomendada = cantidad_recomendada
        self.nivel = nivel  # URGENTE, ATENCION, OPORTUNIDAD

    def to_dict(self) -> Dict:
        return {
            "producto_id": self.producto_id,
            "nombre": self.nombre,
            "stock_actual": self.stock_actual,
            "dias_hasta_agotarse": round(self.dias_hasta_agotarse, 1),
            "cantidad_recomendada": self.cantidad_recomendada,
            "nivel": self.nivel,
        }


class ProductoABC:
    """Clasificación ABC de un producto."""
    def __init__(self, producto_id: int, nombre: str, categoria: str,
                 ingresos_totales: float, unidades_vendidas: int, clasificacion: str):
        self.producto_id = producto_id
        self.nombre = nombre
        self.categoria = categoria
        self.ingresos_totales = ingresos_totales
        self.unidades_vendidas = unidades_vendidas
        self.clasificacion = clasificacion  # A, B, C

    def to_dict(self) -> Dict:
        return {
            "producto_id": self.producto_id,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "ingresos_totales": round(self.ingresos_totales, 2),
            "unidades_vendidas": self.unidades_vendidas,
            "clasificacion": self.clasificacion,
        }


class SugerenciaPrecio:
    """Sugerencia de ajuste de precio."""
    def __init__(self, producto_id: int, nombre: str, precio_actual: float,
                 demanda_diaria: float, rotacion: str, sugerencia: str,
                 ajuste_pct: float, impacto_estimado: float):
        self.producto_id = producto_id
        self.nombre = nombre
        self.precio_actual = precio_actual
        self.demanda_diaria = demanda_diaria
        self.rotacion = rotacion  # ALTA, MEDIA, BAJA
        self.sugerencia = sugerencia  # SUBIR, BAJAR, MANTENER
        self.ajuste_pct = ajuste_pct
        self.impacto_estimado = impacto_estimado

    def to_dict(self) -> Dict:
        return {
            "producto_id": self.producto_id,
            "nombre": self.nombre,
            "precio_actual": round(self.precio_actual, 2),
            "demanda_diaria": round(self.demanda_diaria, 2),
            "rotacion": self.rotacion,
            "sugerencia": self.sugerencia,
            "ajuste_pct": round(self.ajuste_pct, 1),
            "impacto_estimado": round(self.impacto_estimado, 2),
        }


class PrediccionServicioML:
    """Servicio de Machine Learning para predicción de demanda."""

    def __init__(self,
                 ticket_repo: Optional[TicketRepositorio] = None,
                 producto_repo: Optional[ProductoRepositorio] = None,
                 inventario_repo: Optional[InventarioRepositorio] = None):
        self.ticket_repo = ticket_repo or SQLAlchemyTicketRepositorio()
        self.producto_repo = producto_repo or SQLAlchemyProductoRepositorio()
        self.inventario_repo = inventario_repo or SQLAlchemyInventarioRepositorio()

    # =====================================================================
    # PREPARACIÓN DE DATOS
    # =====================================================================

    def _agrupar_ventas_por_dia(self, lineas: List) -> Dict[str, float]:
        """Agrupa líneas de tickets por día, sumando cantidades."""
        ventas_por_dia = defaultdict(float)
        for linea in lineas:
            fecha = linea.ticket.fecha
            if isinstance(fecha, datetime):
                fecha_str = fecha.strftime("%Y-%m-%d")
            else:
                fecha_str = str(fecha)[:10]
            ventas_por_dia[fecha_str] += linea.cantidad
        return dict(ventas_por_dia)

    def _rellenar_dias_faltantes(self, ventas_por_dia: Dict[str, float], dias: int = 90) -> List[Tuple[str, float]]:
        """Rellena días sin ventas con 0 para tener serie temporal completa."""
        hoy = datetime.utcnow().date()
        resultado = []
        for i in range(dias, -1, -1):
            fecha = hoy - timedelta(days=i)
            fecha_str = fecha.strftime("%Y-%m-%d")
            cantidad = ventas_por_dia.get(fecha_str, 0.0)
            resultado.append((fecha_str, cantidad))
        return resultado

    def _preparar_features(self, serie: List[Tuple[str, float]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara features para ML: [dia_semana, dia_mes, mes] -> cantidad."""
        X = []
        y = []
        for fecha_str, cantidad in serie:
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            X.append([
                fecha.weekday(),  # 0=Lunes
                fecha.day,
                fecha.month,
            ])
            y.append(cantidad)
        return np.array(X), np.array(y)

    # =====================================================================
    # MODELO 1: PREDICCIÓN DE DEMANDA
    # =====================================================================

    def predecir_demanda_producto(self, producto_id: int, dias_historia: int = 90,
                                  dias_futuro: int = 30) -> Optional[PrediccionDemandaResultado]:
        """Predice demanda futura para un producto usando regresión lineal."""
        # Obtener datos históricos
        lineas = self.ticket_repo.obtener_por_producto(producto_id, dias=dias_historia)
        if not lineas:
            return None

        ventas_por_dia = self._agrupar_ventas_por_dia(lineas)
        serie = self._rellenar_dias_faltantes(ventas_por_dia, dias=dias_historia)

        if len(serie) < 7:
            return None

        # Preparar datos
        X, y = self._preparar_features(serie)

        # Consumo promedio (total últimos 30 días / 30)
        ultimos_30_vals = [c for _, c in serie[-30:]]
        consumo_promedio = float(sum(ultimos_30_vals) / 30.0) if ultimos_30_vals else 0.0
        if consumo_promedio == 0:
            consumo_promedio = 0.1  # Evitar división por cero

        # Tendencia (comparar semanas completas con ceros incluidos)
        if len(serie) >= 14:
            ultima_semana = float(np.mean([c for _, c in serie[-7:]]))
            semana_anterior = float(np.mean([c for _, c in serie[-14:-7]]))
            if semana_anterior > 0 and ultima_semana > semana_anterior * 1.2:
                tendencia = "ALZA"
            elif semana_anterior > 0 and ultima_semana < semana_anterior * 0.8:
                tendencia = "BAJA"
            else:
                tendencia = "ESTABLE"
        else:
            tendencia = "ESTABLE"

        # Entrenar modelo
        pronostico = []
        if SKLEARN_AVAILABLE and len(serie) >= 14:
            try:
                model = LinearRegression()
                model.fit(X, y)

                # Generar predicciones futuras
                hoy = datetime.utcnow().date()
                for i in range(1, dias_futuro + 1):
                    fecha_futura = hoy + timedelta(days=i)
                    x_futuro = np.array([[fecha_futura.weekday(), fecha_futura.day, fecha_futura.month]])
                    pred = float(max(0, model.predict(x_futuro)[0]))
                    pronostico.append({
                        "fecha": fecha_futura.strftime("%Y-%m-%d"),
                        "cantidad": round(pred, 1),
                    })
            except Exception:
                # Fallback si sklearn falla
                pronostico = self._pronostico_simple(consumo_promedio, tendencia, dias_futuro)
        else:
            # Fallback sin sklearn
            pronostico = self._pronostico_simple(consumo_promedio, tendencia, dias_futuro)

        # Construir histórico para gráfica
        historico = [{"fecha": f, "cantidad": c} for f, c in serie]

        # Stock actual
        inv = self.inventario_repo.obtener_por_producto(producto_id)
        stock_actual = inv.cantidad if inv else 0

        # Días hasta agotarse
        dias_hasta_agotarse = stock_actual / consumo_promedio if consumo_promedio > 0 else 999

        # Obtener nombre
        prod = self.producto_repo.obtener_por_id(producto_id)
        nombre = prod.nombre if prod else f"Producto {producto_id}"

        return PrediccionDemandaResultado(
            producto_id=producto_id,
            producto_nombre=nombre,
            historico=historico,
            pronostico=pronostico,
            consumo_promedio=consumo_promedio,
            dias_hasta_agotarse=dias_hasta_agotarse,
            tendencia=tendencia,
            stock_actual=stock_actual,
        )

    def _pronostico_simple(self, consumo_promedio: float, tendencia: str, dias: int) -> List[Dict]:
        """Fallback de pronóstico sin sklearn."""
        hoy = datetime.utcnow().date()
        factor = {"ALZA": 1.05, "BAJA": 0.95, "ESTABLE": 1.0}.get(tendencia, 1.0)
        resultado = []
        for i in range(1, dias + 1):
            fecha = hoy + timedelta(days=i)
            # Variación por día de semana
            factor_dia = 1.2 if fecha.weekday() >= 4 else 1.0  # Fin de semana +20%
            cantidad = float(consumo_promedio * factor * factor_dia)
            resultado.append({
                "fecha": fecha.strftime("%Y-%m-%d"),
                "cantidad": round(max(0, cantidad), 1),
            })
        return resultado

    def predecir_demanda_categoria(self, categoria_id: int, dias_historia: int = 90,
                                   dias_futuro: int = 30) -> Optional[PrediccionDemandaResultado]:
        """Predice demanda agregada para una categoría."""
        lineas = self.ticket_repo.obtener_lineas_por_categoria(categoria_id, dias=dias_historia)
        if not lineas:
            return None

        # Mismo proceso pero con datos agregados
        ventas_por_dia = self._agrupar_ventas_por_dia(lineas)
        serie = self._rellenar_dias_faltantes(ventas_por_dia, dias=dias_historia)

        if len(serie) < 7:
            return None

        X, y = self._preparar_features(serie)
        ultimos_30_vals = [c for _, c in serie[-30:]]
        consumo_promedio = float(sum(ultimos_30_vals) / 30.0) if ultimos_30_vals else 0.5
        if consumo_promedio == 0:
            consumo_promedio = 0.5

        tendencia = "ESTABLE"
        if len(serie) >= 14:
            ultima_sem = float(np.mean([c for _, c in serie[-7:]]))
            sem_ant = float(np.mean([c for _, c in serie[-14:-7]]))
            if sem_ant > 0 and ultima_sem > sem_ant * 1.2:
                tendencia = "ALZA"
            elif sem_ant > 0 and ultima_sem < sem_ant * 0.8:
                tendencia = "BAJA"

        historico = [{"fecha": f, "cantidad": c} for f, c in serie]

        # Pronóstico
        hoy = datetime.utcnow().date()
        factor = {"ALZA": 1.05, "BAJA": 0.95, "ESTABLE": 1.0}.get(tendencia, 1.0)
        pronostico = []
        for i in range(1, dias_futuro + 1):
            fecha = hoy + timedelta(days=i)
            factor_dia = 1.2 if fecha.weekday() >= 4 else 1.0
            pronostico.append({
                "fecha": fecha.strftime("%Y-%m-%d"),
                "cantidad": round(max(0, float(consumo_promedio * factor * factor_dia)), 1),
            })

        return PrediccionDemandaResultado(
            producto_id=categoria_id,
            producto_nombre=f"Categoría {categoria_id}",
            historico=historico,
            pronostico=pronostico,
            consumo_promedio=consumo_promedio,
            dias_hasta_agotarse=0,  # No aplica a categoría
            tendencia=tendencia,
            stock_actual=0,
        )

    # =====================================================================
    # MODELO 2: ALERTAS DE REPOSICIÓN
    # =====================================================================

    def generar_alertas_reposicion(self, dias_seguridad: int = 14) -> List[AlertaReposicion]:
        """Genera alertas de reposición para todos los productos."""
        productos = self.producto_repo.obtener_todos()
        alertas = []

        for prod in productos:
            inv = self.inventario_repo.obtener_por_producto(prod.id)
            if not inv:
                continue

            stock = inv.cantidad
            pred = self.predecir_demanda_producto(prod.id, dias_historia=60, dias_futuro=30)
            if not pred:
                continue

            consumo = pred.consumo_promedio
            if consumo <= 0:
                continue

            dias_restantes = stock / consumo
            cantidad_recomendada = int(consumo * dias_seguridad)

            if dias_restantes <= 2:
                nivel = "URGENTE"
                cantidad_recomendada = max(cantidad_recomendada, int(consumo * 21))
            elif dias_restantes <= 7:
                nivel = "ATENCION"
                cantidad_recomendada = max(cantidad_recomendada, int(consumo * 14))
            elif dias_restantes <= 14:
                nivel = "OPORTUNIDAD"
            else:
                continue  # No alerta

            alertas.append(AlertaReposicion(
                producto_id=prod.id,
                nombre=prod.nombre,
                stock_actual=stock,
                dias_hasta_agotarse=dias_restantes,
                cantidad_recomendada=cantidad_recomendada,
                nivel=nivel,
            ))

        # Ordenar por urgencia
        orden = {"URGENTE": 0, "ATENCION": 1, "OPORTUNIDAD": 2}
        alertas.sort(key=lambda a: orden.get(a.nivel, 99))
        return alertas

    # =====================================================================
    # MODELO 3: ANÁLISIS ABC
    # =====================================================================

    def analisis_abc(self, dias: int = 90) -> List[ProductoABC]:
        """Clasifica productos por método ABC (Pareto 80/20) en los últimos N días."""
        tickets = self.ticket_repo.obtener_todos_completados(limite=500)
        fecha_limite = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=max(1, dias))
        tickets = [t for t in tickets if t.fecha is not None and t.fecha >= fecha_limite]

        if not tickets:
            return []

        # Agregar ingresos por producto
        ingresos = defaultdict(lambda: {"ingresos": 0.0, "unidades": 0, "nombre": "", "categoria": ""})
        for ticket in tickets:
            for linea in ticket.lineas:
                if linea.producto:
                    pid = linea.producto_id
                    ingresos[pid]["ingresos"] += linea.subtotal
                    ingresos[pid]["unidades"] += linea.cantidad
                    ingresos[pid]["nombre"] = linea.producto.nombre
                    cat = linea.producto.categoria
                    ingresos[pid]["categoria"] = cat.nombre if cat else ""

        # Ordenar por ingresos
        items = sorted(ingresos.items(), key=lambda x: x[1]["ingresos"], reverse=True)
        total_ingresos = sum(i["ingresos"] for _, i in items)

        if total_ingresos == 0:
            return []

        # Clasificar A/B/C
        acumulado = 0.0
        resultado = []
        for pid, datos in items:
            acumulado += datos["ingresos"]
            pct = acumulado / total_ingresos
            if pct <= 0.80:
                clas = "A"
            elif pct <= 0.95:
                clas = "B"
            else:
                clas = "C"

            resultado.append(ProductoABC(
                producto_id=pid,
                nombre=datos["nombre"],
                categoria=datos["categoria"],
                ingresos_totales=datos["ingresos"],
                unidades_vendidas=datos["unidades"],
                clasificacion=clas,
            ))

        return resultado

    # =====================================================================
    # MODELO 4: SUGERENCIAS DE PRECIO
    # =====================================================================

    def sugerencias_precio(self, dias: int = 60) -> List[SugerenciaPrecio]:
        """Genera sugerencias de ajuste de precio basado en demanda y rotación."""
        productos = self.producto_repo.obtener_todos()
        sugerencias = []

        for prod in productos:
            pred = self.predecir_demanda_producto(prod.id, dias_historia=dias, dias_futuro=7)
            if not pred:
                continue

            demanda = pred.consumo_promedio
            stock = pred.stock_actual
            precio = prod.precio_venta

            # Rotación
            if demanda >= 5:
                rotacion = "ALTA"
            elif demanda >= 2:
                rotacion = "MEDIA"
            else:
                rotacion = "BAJA"

            # Lógica de sugerencia
            if rotacion == "ALTA" and stock < 10:
                sugerencia = "SUBIR"
                ajuste = 8.0
            elif rotacion == "ALTA" and stock > 50:
                sugerencia = "MANTENER"
                ajuste = 0.0
            elif rotacion == "BAJA" and stock > 30:
                sugerencia = "BAJAR"
                ajuste = -10.0
            elif rotacion == "MEDIA" and stock < 5:
                sugerencia = "SUBIR"
                ajuste = 5.0
            else:
                continue  # Sin sugerencia

            # Impacto estimado
            if sugerencia == "SUBIR":
                impacto = precio * (ajuste / 100) * demanda * 30  # 30 días
            elif sugerencia == "BAJAR":
                # Asumimos +15% en ventas por bajar precio
                impacto = (precio * 0.85) * (demanda * 1.15 * 30) - (precio * demanda * 30)
            else:
                impacto = 0.0

            sugerencias.append(SugerenciaPrecio(
                producto_id=prod.id,
                nombre=prod.nombre,
                precio_actual=precio,
                demanda_diaria=demanda,
                rotacion=rotacion,
                sugerencia=sugerencia,
                ajuste_pct=ajuste,
                impacto_estimado=impacto,
            ))

        # Ordenar por impacto
        sugerencias.sort(key=lambda s: abs(s.impacto_estimado), reverse=True)
        return sugerencias[:20]  # Top 20

    # =====================================================================
    # MODELO 5: ESTACIONALIDAD
    # =====================================================================

    def analisis_estacionalidad(self) -> Dict:
        """Analiza patrones estacionales comparando meses."""
        hoy = datetime.utcnow()
        mes_actual = hoy.month
        mes_anterior = (hoy.replace(day=1) - timedelta(days=1)).month

        # Obtener tickets del mes actual y anterior
        inicio_actual = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if mes_actual == 1:
            inicio_anterior = inicio_actual.replace(year=inicio_actual.year - 1, month=12)
        else:
            inicio_anterior = inicio_actual.replace(month=mes_actual - 1)

        fin_anterior = inicio_actual - timedelta(microseconds=1)

        tickets_actual = self.ticket_repo.obtener_por_fecha(inicio_actual, hoy)
        tickets_anterior = self.ticket_repo.obtener_por_fecha(inicio_anterior, fin_anterior)

        def calcular_metricas(tickets):
            total = 0.0
            unidades = 0
            for t in tickets:
                total += t.total
                for l in t.lineas:
                    unidades += l.cantidad
            return {"ingresos": total, "tickets": len(tickets), "unidades": unidades}

        actual = calcular_metricas(tickets_actual)
        anterior = calcular_metricas(tickets_anterior)

        variacion = {}
        for k in ["ingresos", "tickets", "unidades"]:
            if anterior[k] > 0:
                variacion[k] = round(((actual[k] - anterior[k]) / anterior[k]) * 100, 1)
            else:
                variacion[k] = 0.0

        return {
            "mes_actual": inicio_actual.strftime("%B %Y"),
            "mes_anterior": inicio_anterior.strftime("%B %Y"),
            "metricas_actual": {k: round(v, 2) for k, v in actual.items()},
            "metricas_anterior": {k: round(v, 2) for k, v in anterior.items()},
            "variacion_pct": variacion,
            "tendencia": "ALZA" if variacion.get("ingresos", 0) > 10 else ("BAJA" if variacion.get("ingresos", 0) < -10 else "ESTABLE"),
        }

    # =====================================================================
    # DASHBOARD GLOBAL
    # =====================================================================

    def dashboard_global(self) -> Dict:
        """Resumen global con todas las métricas predictivas."""
        alertas = self.generar_alertas_reposicion()
        abc = self.analisis_abc()
        precios = self.sugerencias_precio()
        estacional = self.analisis_estacionalidad()

        # Contar alertas por nivel
        urgente = len([a for a in alertas if a.nivel == "URGENTE"])
        atencion = len([a for a in alertas if a.nivel == "ATENCION"])

        return {
            "alertas": {
                "total": len(alertas),
                "urgentes": urgente,
                "atencion": atencion,
            },
            "abc": {
                "total_productos": len(abc),
                "clase_a": len([p for p in abc if p.clasificacion == "A"]),
                "clase_b": len([p for p in abc if p.clasificacion == "B"]),
                "clase_c": len([p for p in abc if p.clasificacion == "C"]),
            },
            "precios": {
                "sugerencias_total": len(precios),
                "subir": len([p for p in precios if p.sugerencia == "SUBIR"]),
                "bajar": len([p for p in precios if p.sugerencia == "BAJAR"]),
            },
            "estacionalidad": estacional,
        }
