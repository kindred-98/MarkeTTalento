from typing import List, Optional
from datetime import datetime, timedelta
from src.dominio.entidades.entidades import Producto, Inventario, Venta
from src.dominio.repositorios.repositorios import InventarioRepositorio, VentaRepositorio


class InventarioAnalisis:
    """Resultado del análisis de inventario."""
    
    def __init__(self, producto: Producto, inventario: Optional[Inventario], historial_ventas: List[Venta]):
        self.producto = producto
        self.inventario = inventario
        self.historial_ventas = historial_ventas
        self.stock_actual = inventario.cantidad if inventario else 0
    
    @property
    def consumo_promedio_diario(self) -> float:
        if not self.historial_ventas:
            return 0
        total = sum(v.cantidad for v in self.historial_ventas)
        return total / len(self.historial_ventas)
    
    @property
    def dias_hasta_agotarse(self) -> float:
        if self.consumo_promedio_diario == 0:
            return 999
        return self.stock_actual / self.consumo_promedio_diario
    
    @property
    def estado(self) -> str:
        """Calcula el estado basado en el porcentaje del stock máximo."""
        stock_maximo = self.producto.stock_maximo or 100
        
        if self.stock_actual <= 0:
            return "AGOTADO"
        
        if stock_maximo > 0:
            pct = (self.stock_actual / stock_maximo) * 100
            if pct <= 25:
                return "CRÍTICO"
            elif pct <= 50:
                return "BAJO"
            elif pct <= 75:
                return "MODERADO"
        
        return "ADECUADO"
    
    @property
    def necesita_reposicion(self) -> bool:
        """Determina si necesita reposición basado en el porcentaje del stock."""
        stock_maximo = self.producto.stock_maximo or 100
        
        if stock_maximo > 0:
            pct = (self.stock_actual / stock_maximo) * 100
            return pct <= 25  # Necesita reposición si está en 25% o menos
        
        return False
    
    @property
    def cantidad_recomendada(self) -> int:
        """Cantidad recomendada para 10 días de stock."""
        return int(self.consumo_promedio_diario * 10)


class InventarioServicio:
    """Servicio para análisis y gestión de inventario."""

    def __init__(self, inventario_repo: InventarioRepositorio, venta_repo: VentaRepositorio):
        self.inventario_repo = inventario_repo
        self.venta_repo = venta_repo

    def obtener_inventario(self, producto_id: int) -> Optional[Inventario]:
        """Obtiene el inventario de un producto."""
        return self.inventario_repo.obtener_por_producto(producto_id)

    def obtener_todos_inventarios(self) -> List[Inventario]:
        """Lista todos los inventarios."""
        return self.inventario_repo.obtener_todos()

    def actualizar_stock(self, producto_id: int, cantidad: int, ubicacion: Optional[str] = None) -> Inventario:
        """Actualiza el stock de un producto."""
        return self.inventario_repo.actualizar_stock(producto_id, cantidad, ubicacion)

    def obtener_bajo_stock(self, limite: int = 10) -> List[Inventario]:
        """Lista productos con stock bajo."""
        return self.inventario_repo.obtener_bajo_stock(limite)

    def analizar_todo_el_inventario(self) -> List[InventarioAnalisis]:
        """Analiza todos los productos del inventario."""
        inventarios = self.obtener_todos_inventarios()
        resultados = []
        
        for inventario in inventarios:
            producto = inventario.producto
            historial = self.venta_repo.obtener_por_producto(producto.id, limite=20)
            analisis = InventarioAnalisis(producto, inventario, historial)
            resultados.append(analisis)
        
        return resultados

    def generar_recomendaciones(self) -> List[dict]:
        """Genera recomendaciones de reposición."""
        analisis = self.analizar_todo_el_inventario()
        recomendaciones = []
        
        for a in analisis:
            if a.necesita_reposicion:
                prioridad = "ALTA" if a.estado == "CRÍTICO" else "MEDIA"
                recomendaciones.append({
                    "producto": a.producto.nombre,
                    "stock_actual": a.stock_actual,
                    "stock_minimo": a.producto.stock_minimo,
                    "dias_restantes": round(a.dias_hasta_agotarse, 1),
                    "cantidad_recomendada": a.cantidad_recomendada,
                    "prioridad": prioridad,
                    "estado": a.estado
                })
        
        # Ordenar por prioridad
        recomendaciones.sort(key=lambda x: (
            0 if x["prioridad"] == "ALTA" else 1,
            x["dias_restantes"]
        ))
        
        return recomendaciones

    def calcular_valor_inventario(self, lista_analisis: List[InventarioAnalisis]) -> float:
        """Calcula el valor total del inventario."""
        total = 0
        for a in lista_analisis:
            total += a.stock_actual * a.producto.precio_venta
        return round(total, 2)

    def obtener_resumen(self) -> dict:
        """Obtiene un resumen general del inventario."""
        analisis = self.analizar_todo_el_inventario()
        
        return {
            "total_productos": len(analisis),
            "total_unidades": sum(a.stock_actual for a in analisis),
            "productos_criticos": sum(1 for a in analisis if a.estado == "CRÍTICO"),
            "productos_bajos": sum(1 for a in analisis if a.estado == "BAJO"),
            "productos_adecuados": sum(1 for a in analisis if a.estado in ["MODERADO", "ADECUADO"]),
            "valor_total": self.calcular_valor_inventario(analisis),
            "recomendaciones": self.generar_recomendaciones()
        }
