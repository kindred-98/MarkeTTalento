from typing import List
from datetime import datetime, timedelta, timezone

from src.dominio.entidades.entidades import Venta
from src.dominio.repositorios.repositorios import VentaRepositorio

DIAS_SIN_CONSUMO = 999.0
LIMITE_HISTORIAL = 30
DIAS_TENDENCIA = 5
FACTOR_TENDENCIA_ALTA = 1.2
FACTOR_TENDENCIA_BAJA = 0.8
VARIACION_TENDENCIA = {"ALTA": 1.2, "BAJA": 0.8, "ESTABLE": 1.0}


class PrediccionModelo:
    """Resultado de predicción de demanda."""

    def __init__(self, producto_nombre: str, dias_hasta_agotarse: float,
                 consumo_promedio: float, tendencia: str, datos_grafico: List):
        self.producto_nombre = producto_nombre
        self.dias_hasta_agotarse = dias_hasta_agotarse
        self.consumo_promedio = consumo_promedio
        self.tendencia = tendencia
        self.datos_grafico = datos_grafico

    @property
    def estado(self) -> str:
        dias = self.dias_hasta_agotarse
        if dias <= 2:
            return "CRÍTICO"
        elif dias <= 5:
            return "BAJO"
        elif dias <= 10:
            return "MODERADO"
        return "ADECUADO"

    @property
    def nivel_stock(self) -> str:
        if self.dias_hasta_agotarse <= 0:
            return "AGOTADO"
        dias = self.dias_hasta_agotarse
        if dias <= 2:
            return "CRÍTICO"
        elif dias <= 5:
            return "BAJO"
        elif dias <= 10:
            return "MODERADO"
        return "OK"


class PrediccionServicio:
    """Servicio para predicción de demanda usando series temporales."""

    def __init__(self, venta_repo: VentaRepositorio):
        self.venta_repo = venta_repo

    @staticmethod
    def _nombre_producto(producto_id: int) -> str:
        from src.implementaciones.repositorios_impl import SQLAlchemyProductoRepositorio

        producto = SQLAlchemyProductoRepositorio().obtener_por_id(producto_id)
        return producto.nombre if producto else f"Producto {producto_id}"

    @staticmethod
    def _stock_actual(producto_id: int) -> int:
        from src.implementaciones.repositorios_impl import SQLAlchemyInventarioRepositorio

        inventario = SQLAlchemyInventarioRepositorio().obtener_por_producto(producto_id)
        return inventario.cantidad if inventario else 0

    @staticmethod
    def _dias_observados(historial: List[Venta]) -> int:
        """Días cubiertos por el historial (mínimo 1 para evitar división por cero)."""
        fechas = [v.fecha for v in historial if v.fecha is not None]
        if len(fechas) < 2:
            return 1
        return max(1, (max(fechas) - min(fechas)).days + 1)

    @staticmethod
    def _calcular_tendencia(cantidades: List[float], consumo_promedio: float) -> str:
        if len(cantidades) < DIAS_TENDENCIA:
            return "ESTABLE"
        ultimos = sum(cantidades[-DIAS_TENDENCIA:]) / DIAS_TENDENCIA
        if ultimos > consumo_promedio * FACTOR_TENDENCIA_ALTA:
            return "ALTA"
        if ultimos < consumo_promedio * FACTOR_TENDENCIA_BAJA:
            return "BAJA"
        return "ESTABLE"

    @staticmethod
    def _serie_historica(historial: List[Venta]) -> List[dict]:
        return [
            {
                "fecha": v.fecha.strftime("%Y-%m-%d") if v.fecha else "",
                "cantidad": v.cantidad,
            }
            for v in reversed(historial)
        ]

    def predecir_demanda(self, producto_id: int, dias_futuro: int = 30) -> PrediccionModelo:
        """Predice la demanda futura para un producto.

        `dias_futuro` es el horizonte de la predicción: si el stock no se agota
        dentro de ese periodo se devuelve ese limite como dias_hasta_agotarse.
        """
        historial = self.venta_repo.obtener_por_producto(
            producto_id, limite=LIMITE_HISTORIAL
        )

        if not historial:
            return PrediccionModelo(
                producto_nombre=self._nombre_producto(producto_id),
                dias_hasta_agotarse=DIAS_SIN_CONSUMO,
                consumo_promedio=0.0,
                tendencia="sin datos",
                datos_grafico=[],
            )

        cantidades = [v.cantidad for v in historial]
        consumo_por_venta = sum(cantidades) / len(cantidades)
        consumo_diario = sum(cantidades) / self._dias_observados(historial)

        horizonte = max(1, dias_futuro)
        stock_actual = self._stock_actual(producto_id)
        if consumo_diario <= 0:
            dias_hasta_agotarse = DIAS_SIN_CONSUMO
        else:
            dias_hasta_agotarse = min(stock_actual / consumo_diario, float(horizonte))

        return PrediccionModelo(
            producto_nombre=self._nombre_producto(producto_id),
            dias_hasta_agotarse=round(dias_hasta_agotarse, 2),
            consumo_promedio=round(consumo_diario, 3),
            tendencia=self._calcular_tendencia(cantidades, consumo_por_venta),
            datos_grafico=self._serie_historica(historial),
        )

    def generar_pronostico_semanal(self, producto_id: int) -> List[dict]:
        """Genera pronóstico para los próximos 7 días."""
        prediccion = self.predecir_demanda(producto_id, dias_futuro=7)
        variacion = VARIACION_TENDENCIA.get(prediccion.tendencia, 1.0)
        hoy = datetime.now(timezone.utc)

        return [
            {
                "fecha": (hoy + timedelta(days=i + 1)).strftime("%Y-%m-%d"),
                "cantidad_estimada": round(prediccion.consumo_promedio * variacion, 1),
                "tendencia": prediccion.tendencia,
            }
            for i in range(7)
        ]