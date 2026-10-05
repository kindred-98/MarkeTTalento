"""
Servicio de Machine Learning para predicción de demanda e inteligencia de negocio.
Usa scikit-learn para regresión lineal y numpy para análisis estadístico.
"""
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from src.dominio.repositorios.repositorios import TicketRepositorio, ProductoRepositorio, InventarioRepositorio
from src.core.utils.fechas import hoy_utc, utcnow_naive
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


FACTORES_TENDENCIA = {"ALZA": 1.05, "BAJA": 0.95, "ESTABLE": 1.0}
VENTANA_TENDENCIA_DIAS = 7
DIAS_MINIMOS_TENDENCIA = 14
DIAS_CONSUMO_PROMEDIO = 30
UMBRAL_TENDENCIA_ALZA = 1.2
UMBRAL_TENDENCIA_BAJA = 0.8
DIAS_FIN_DE_SEMANA = 4
FACTOR_FIN_DE_SEMANA = 1.2
CONSUMO_MINIMO_PRODUCTO = 0.1
CONSUMO_MINIMO_CATEGORIA = 0.5

# (umbral acumulado de ingresos, clase ABC)
CLASES_ABC = ((0.80, "A"), (0.95, "B"))
CLASE_ABC_FINAL = "C"

# (demanda mínima, rotación)
NIVELES_ROTACION = ((5, "ALTA"), (2, "MEDIA"))
ROTACION_FINAL = "BAJA"

# (rotación, operador de stock, umbral, sugerencia, ajuste %)
REGLAS_SUGERENCIA = (
    ("ALTA", "<", 10, "SUBIR", 8.0),
    ("ALTA", ">", 50, "MANTENER", 0.0),
    ("BAJA", ">", 30, "BAJAR", -10.0),
    ("MEDIA", "<", 5, "SUBIR", 5.0),
)
COMPARADORES_STOCK = {
    "<": lambda stock, umbral: stock < umbral,
    ">": lambda stock, umbral: stock > umbral,
}
DIAS_IMPACTO_PRESUPUESTO = 30
AUMENTO_VENTAS_BAJADA_PRECIO = 1.15
REDUCCION_PRECIO_BAJADA = 0.85
TOP_SUGERENCIAS = 20

UMBRAL_ESTACIONALIDAD_ALZA = 10
UMBRAL_ESTACIONALIDAD_BAJA = -10


def _calcular_tendencia(serie: List[Tuple[str, float]]) -> str:
    """Compara las dos últimas semanas completas (con ceros incluidos)."""
    if len(serie) < DIAS_MINIMOS_TENDENCIA:
        return "ESTABLE"

    ultima = float(np.mean([c for _, c in serie[-VENTANA_TENDENCIA_DIAS:]]))
    anterior = float(np.mean([
        c for _, c in serie[-2 * VENTANA_TENDENCIA_DIAS:-VENTANA_TENDENCIA_DIAS]
    ]))

    if anterior <= 0:
        return "ESTABLE"
    if ultima > anterior * UMBRAL_TENDENCIA_ALZA:
        return "ALZA"
    if ultima < anterior * UMBRAL_TENDENCIA_BAJA:
        return "BAJA"
    return "ESTABLE"


def _consumo_promedio(serie: List[Tuple[str, float]], minimo: float) -> float:
    """Consumo medio diario de los últimos 30 días, nunca cero."""
    valores = [c for _, c in serie[-DIAS_CONSUMO_PROMEDIO:]]
    consumo = float(sum(valores) / DIAS_CONSUMO_PROMEDIO) if valores else minimo
    return consumo if consumo > 0 else minimo


def _clasificacion_abc(porcentaje_acumulado: float) -> str:
    """Clase ABC segun el porcentaje de ingresos acumulados."""
    for umbral, clase in CLASES_ABC:
        if porcentaje_acumulado <= umbral:
            return clase
    return CLASE_ABC_FINAL


def _tendencia_por_variacion(variacion_pct: float) -> str:
    """Tendencia estacional segun la variación de ingresos en porcentaje."""
    if variacion_pct > UMBRAL_ESTACIONALIDAD_ALZA:
        return "ALZA"
    if variacion_pct < UMBRAL_ESTACIONALIDAD_BAJA:
        return "BAJA"
    return "ESTABLE"


def _factor_dia(fecha) -> float:
    """Multiplicador por día de semana: fines de semana +20%."""
    if fecha.weekday() >= DIAS_FIN_DE_SEMANA:
        return FACTOR_FIN_DE_SEMANA
    return 1.0


def _rotacion(demanda: float) -> str:
    """Clasifica la rotación de un producto según su demanda diaria."""
    for umbral, nivel in NIVELES_ROTACION:
        if demanda >= umbral:
            return nivel
    return ROTACION_FINAL


def _sugerencia_precio(rotacion: str, stock: int) -> Optional[tuple]:
    """Devuelve (sugerencia, ajuste %) según rotación y stock, o None si no aplica."""
    for rot, operador, umbral, sugerencia, ajuste in REGLAS_SUGERENCIA:
        if rotacion == rot and COMPARADORES_STOCK[operador](stock, umbral):
            return sugerencia, ajuste
    return None


def _impacto_estimado(sugerencia: str, ajuste: float, precio: float, demanda: float) -> float:
    """Impacto estimado en ingresos a 30 días del ajuste de precio."""
    ingresos_actuales = precio * demanda * DIAS_IMPACTO_PRESUPUESTO

    if sugerencia == "SUBIR":
        return ingresos_actuales * (ajuste / 100)

    if sugerencia == "BAJAR":
        precio_nuevo = precio * REDUCCION_PRECIO_BAJADA
        ventas_nuevas = demanda * AUMENTO_VENTAS_BAJADA_PRECIO
        return precio_nuevo * ventas_nuevas * DIAS_IMPACTO_PRESUPUESTO - ingresos_actuales

    return 0.0


def _metricas_tickets(tickets) -> Dict:
    """Ingresos, nº de tickets y unidades de una lista de tickets."""
    total = 0.0
    unidades = 0
    for t in tickets:
        total += t.total
        for l in t.lineas:
            unidades += l.cantidad
    return {"ingresos": total, "tickets": len(tickets), "unidades": unidades}


def _variacion_pct(actual: Dict, anterior: Dict, claves: List[str]) -> Dict:
    """Variación porcentual entre dos Metricas, 0 cuando el periodo anterior es 0."""
    variacion = {}
    for k in claves:
        base = anterior[k]
        variacion[k] = round(((actual[k] - base) / base) * 100, 1) if base > 0 else 0.0
    return variacion


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
        hoy = hoy_utc()
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
                fecha.weekday(),  # Lunes es el día 0
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

        consumo_promedio = _consumo_promedio(serie, CONSUMO_MINIMO_PRODUCTO)
        tendencia = _calcular_tendencia(serie)

        # Pronóstico con regresión lineal, o fallback si no hay sklearn
        pronostico = self._pronostico_ml(X, y, consumo_promedio, tendencia, dias_futuro)

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

    def _pronostico_ml(self, X, y, consumo_promedio: float,
                       tendencia: str, dias_futuro: int) -> List[Dict]:
        """Predicción con regresión lineal; cae al heurístico si sklearn no está o falla."""
        if not (SKLEARN_AVAILABLE and len(y) >= DIAS_MINIMOS_TENDENCIA):
            return self._pronostico_simple(consumo_promedio, tendencia, dias_futuro)

        try:
            model = LinearRegression()
            model.fit(X, y)
        except Exception:
            return self._pronostico_simple(consumo_promedio, tendencia, dias_futuro)

        hoy = hoy_utc()
        pronostico = []
        for i in range(1, dias_futuro + 1):
            fecha_futura = hoy + timedelta(days=i)
            x_futuro = np.array([[fecha_futura.weekday(), fecha_futura.day, fecha_futura.month]])
            pred = float(max(0, model.predict(x_futuro)[0]))
            pronostico.append({
                "fecha": fecha_futura.strftime("%Y-%m-%d"),
                "cantidad": round(pred, 1),
            })
        return pronostico

    def _pronostico_simple(self, consumo_promedio: float, tendencia: str, dias: int) -> List[Dict]:
        """Fallback de pronóstico sin sklearn."""
        hoy = hoy_utc()
        factor = FACTORES_TENDENCIA.get(tendencia, 1.0)
        resultado = []
        for i in range(1, dias + 1):
            fecha = hoy + timedelta(days=i)
            cantidad = float(consumo_promedio * factor * _factor_dia(fecha))
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

        consumo_promedio = _consumo_promedio(serie, CONSUMO_MINIMO_CATEGORIA)
        tendencia = _calcular_tendencia(serie)

        historico = [{"fecha": f, "cantidad": c} for f, c in serie]
        pronostico = self._pronostico_simple(consumo_promedio, tendencia, dias_futuro)

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

    def _ingresos_por_producto(self, tickets) -> Dict:
        """Acumula ingresos, unidades, nombre y categoría por producto."""
        ingresos = defaultdict(lambda: {"ingresos": 0.0, "unidades": 0, "nombre": "", "categoria": ""})
        for ticket in tickets:
            for linea in ticket.lineas:
                if not linea.producto:
                    continue
                pid = linea.producto_id
                ingresos[pid]["ingresos"] += linea.subtotal
                ingresos[pid]["unidades"] += linea.cantidad
                ingresos[pid]["nombre"] = linea.producto.nombre
                cat = linea.producto.categoria
                ingresos[pid]["categoria"] = cat.nombre if cat else ""
        return ingresos

    def analisis_abc(self, dias: int = 90) -> List[ProductoABC]:
        """Clasifica productos por método ABC (Pareto 80/20) en los últimos N días."""
        tickets = self.ticket_repo.obtener_todos_completados(limite=500)
        fecha_limite = utcnow_naive() - timedelta(days=max(1, dias))
        tickets = [t for t in tickets if t.fecha is not None and t.fecha >= fecha_limite]

        if not tickets:
            return []

        items = sorted(
            self._ingresos_por_producto(tickets).items(),
            key=lambda x: x[1]["ingresos"],
            reverse=True,
        )
        total_ingresos = sum(datos["ingresos"] for _, datos in items)

        if total_ingresos == 0:
            return []

        acumulado = 0.0
        resultado = []
        for pid, datos in items:
            acumulado += datos["ingresos"]
            resultado.append(ProductoABC(
                producto_id=pid,
                nombre=datos["nombre"],
                categoria=datos["categoria"],
                ingresos_totales=datos["ingresos"],
                unidades_vendidas=datos["unidades"],
                clasificacion=_clasificacion_abc(acumulado / total_ingresos),
            ))

        return resultado

    # =====================================================================
    # MODELO 4: SUGERENCIAS DE PRECIO
    # =====================================================================

    def _construir_sugerencia(self, prod, pred) -> Optional[SugerenciaPrecio]:
        """Genera la sugerencia de precio de un producto, o None si no aplica."""
        rotacion = _rotacion(pred.consumo_promedio)
        regla = _sugerencia_precio(rotacion, pred.stock_actual)
        if regla is None:
            return None

        sugerencia, ajuste = regla
        return SugerenciaPrecio(
            producto_id=prod.id,
            nombre=prod.nombre,
            precio_actual=prod.precio_venta,
            demanda_diaria=pred.consumo_promedio,
            rotacion=rotacion,
            sugerencia=sugerencia,
            ajuste_pct=ajuste,
            impacto_estimado=_impacto_estimado(sugerencia, ajuste, prod.precio_venta, pred.consumo_promedio),
        )

    def sugerencias_precio(self, dias: int = 60) -> List[SugerenciaPrecio]:
        """Genera sugerencias de ajuste de precio basado en demanda y rotación."""
        sugerencias = []

        for prod in self.producto_repo.obtener_todos():
            pred = self.predecir_demanda_producto(prod.id, dias_historia=dias, dias_futuro=7)
            if not pred:
                continue
            sugerencia = self._construir_sugerencia(prod, pred)
            if sugerencia:
                sugerencias.append(sugerencia)

        sugerencias.sort(key=lambda s: abs(s.impacto_estimado), reverse=True)
        return sugerencias[:TOP_SUGERENCIAS]

    # =====================================================================
    # MODELO 5: ESTACIONALIDAD
    # =====================================================================

    METRICAS_ESTACIONALIDAD = ["ingresos", "tickets", "unidades"]

    def analisis_estacionalidad(self) -> Dict:
        """Analiza patrones estacionales comparando meses."""
        hoy = utcnow_naive()
        inicio_actual = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        if inicio_actual.month == 1:
            inicio_anterior = inicio_actual.replace(year=inicio_actual.year - 1, month=12)
        else:
            inicio_anterior = inicio_actual.replace(month=inicio_actual.month - 1)

        fin_anterior = inicio_actual - timedelta(microseconds=1)

        tickets_actual = self.ticket_repo.obtener_por_fecha(inicio_actual, hoy)
        tickets_anterior = self.ticket_repo.obtener_por_fecha(inicio_anterior, fin_anterior)

        actual = _metricas_tickets(tickets_actual)
        anterior = _metricas_tickets(tickets_anterior)
        variacion = _variacion_pct(actual, anterior, self.METRICAS_ESTACIONALIDAD)

        return {
            "mes_actual": inicio_actual.strftime("%B %Y"),
            "mes_anterior": inicio_anterior.strftime("%B %Y"),
            "metricas_actual": {k: round(v, 2) for k, v in actual.items()},
            "metricas_anterior": {k: round(v, 2) for k, v in anterior.items()},
            "variacion_pct": variacion,
            "tendencia": _tendencia_por_variacion(variacion.get("ingresos", 0)),
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
