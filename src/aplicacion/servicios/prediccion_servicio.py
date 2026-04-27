from typing import List, Optional
import numpy as np
from datetime import datetime, timedelta
from src.dominio.entidades.entidades import Venta
from src.dominio.repositorios.repositorios import VentaRepositorio


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

    def predecir_demanda(self, producto_id: int, dias_futuro: int = 30) -> PrediccionModelo:
        """Predice la demanda futura para un producto."""
        # Obtener historial de ventas
        historial = self.venta_repo.obtener_por_producto(producto_id, limite=30)
        
        if not historial:
            return PrediccionModelo(
                producto_nombre="Sin datos",
                dias_hasta_agotarse=999,
                consumo_promedio=0,
                tendencia="sin datos",
                datos_grafico=[]
            )
        
        # Calcular consumo promedio
        cantidades = [v.cantidad for v in historial]
        consumo_promedio = sum(cantidades) / len(cantidades)
        
        # Calcular tendencia (comparando últimos 5 días vs promedio)
        if len(cantidades) >= 5:
            ultimos_5 = sum(cantidades[-5:]) / 5
            if ultimos_5 > consumo_promedio * 1.2:
                tendencia = "ALTA"
            elif ultimos_5 < consumo_promedio * 0.8:
                tendencia = "BAJA"
            else:
                tendencia = "ESTABLE"
        else:
            tendencia = "ESTABLE"
        
        # Calcular días hasta agotarse (asumiendo stock actual de BD)
        from src.infraestructura.repositorios.repositorios_impl import SQLAlchemyInventarioRepositorio
        inventario_repo = SQLAlchemyInventarioRepositorio()
        inventario = inventario_repo.obtener_por_producto(producto_id)
        stock_actual = inventario.cantidad if inventario else 0
        
        if consumo_promedio > 0:
            dias_hasta = stock_actual / consumo_promedio
        else:
            dias_hasta = 999
        
        # Preparar datos para gráfico
        datos_grafico = [
            {"fecha": v.fecha.strftime("%Y-%m-%d"), "cantidad": v.cantidad}
            for v in historial
        ]
        
        return PrediccionModelo(
            producto_nombre=historial[0].producto.nombre if historial else "Unknown",
            dias_hasta_agotarse=dias_hasta,
            consumo_promedio=consumo_promedio,
            tendencia=tendencia,
            datos_grafico=datos_grafico
        )

    def predecir_todos(self) -> List[PrediccionModelo]:
        """Predice demanda para todos los productos."""
        from src.infraestructura.repositorios.repositorios_impl import SQLAlchemyProductoRepositorio
        from src.dominio.entidades.entidades import Producto
        
        producto_repo = SQLAlchemyProductoRepositorio()
        productos = producto_repo.obtener_todos()
        
        predicciones = []
        for producto in productos:
            pred = self.predecir_demanda(producto.id)
            predicciones.append(pred)
        
        return predicciones

    def generar_pronostico_semanal(self, producto_id: int) -> List[dict]:
        """Genera pronóstico para los próximos 7 días."""
        prediccion = self.predecir_demanda(producto_id)
        
        # Simular预测
        resultados = []
        consumo = prediccion.consumo_promedio
        
        for i in range(7):
            fecha = datetime.utcnow() + timedelta(days=i+1)
            
            # Variación aleatoria pequeña
            if prediccion.tendencia == "ALTA":
                variacion = 1.2
            elif prediccion.tendencia == "BAJA":
                variacion = 0.8
            else:
                variacion = 1.0
            
            cantidad_estimada = consumo * variacion
            
            resultados.append({
                "fecha": fecha.strftime("%Y-%m-%d"),
                "cantidad_estimada": round(cantidad_estimada, 1),
                "tendencia": prediccion.tendencia
            })
        
        return resultados