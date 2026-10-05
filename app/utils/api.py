"""
Capa de acceso directo a SQLite para Streamlit
Reemplaza las llamadas HTTP por acceso directo a BD
"""
import time
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import DatabaseAccess
from src.dominio.entidades.entidades import (
    Categoria, Proveedor, Producto, Inventario, Ticket
)

db = DatabaseAccess()

STOCK_MAXIMO_POR_DEFECTO = 100
UBICACION_POR_DEFECTO = "Almacén A"


def _estado_inventario(cantidad: int, stock_minimo: int) -> str:
    """Clasifica el stock de una fila de inventario según su stock mínimo."""
    if cantidad == 0:
        return "Agotado"
    if cantidad < stock_minimo:
        return "Crítico"
    return "Saludable"


def _producto_to_dict(prod, inv=None):
    cat = prod.categoria
    prov = prod.proveedor
    if inv:
        stock = inv.cantidad
    elif prod.inventario:
        stock = prod.inventario.cantidad
    else:
        stock = None
    return {
        "id": prod.id, "sku": prod.sku, "codigo_barras": prod.codigo_barras,
        "nombre": prod.nombre, "descripcion": prod.descripcion,
        "precio_venta": prod.precio_venta, "precio_coste": prod.precio_coste,
        "unidad": prod.unidad, "stock_minimo": prod.stock_minimo,
        "stock_maximo": prod.stock_maximo, "tiempo_reposicion": prod.tiempo_reposicion,
        "imagen_url": prod.imagen_url, "activo": prod.activo, "stock": stock,
        "fecha_creacion": prod.fecha_creacion.isoformat() if prod.fecha_creacion else None,
        "categoria": {"id": cat.id, "nombre": cat.nombre} if cat else None,
        "categoria_id": prod.categoria_id,
        "proveedor": {"id": prov.id, "nombre": prov.nombre} if prov else None,
        "proveedor_id": prod.proveedor_id
    }


def _ticket_to_dict(ticket) -> Dict[str, Any]:
    lineas = [
        {
            "id": linea.id, "producto_id": linea.producto_id, "cantidad": linea.cantidad,
            "precio_unitario": linea.precio_unitario, "subtotal": linea.subtotal,
            "producto": {"nombre": linea.producto.nombre} if linea.producto else {"nombre": "N/A"}
        }
        for linea in ticket.lineas
    ]
    return {
        "id": ticket.id, "numero_ticket": ticket.numero_ticket, "cajero": ticket.cajero,
        "fecha": ticket.fecha.isoformat() if ticket.fecha else "", "total": ticket.total,
        "metodo_pago": ticket.metodo_pago, "entrega_efectivo": ticket.entrega_efectivo,
        "cambio": ticket.cambio, "estado": ticket.estado, "lineas": lineas
    }


def _inventario_to_dict(inv):
    prod = inv.producto
    if prod is None:
        return {"id": inv.id, "producto_id": inv.producto_id, "stock": inv.cantidad}

    cat = prod.categoria
    return {
        "id": inv.id, "producto_id": prod.id,
        "producto": {
            "id": prod.id, "sku": prod.sku, "nombre": prod.nombre,
            "descripcion": prod.descripcion, "precio_venta": prod.precio_venta,
            "precio_coste": prod.precio_coste, "unidad": prod.unidad,
            "stock_minimo": prod.stock_minimo, "stock_maximo": prod.stock_maximo,
            "tiempo_reposicion": prod.tiempo_reposicion, "codigo_barras": prod.codigo_barras,
            "imagen_url": prod.imagen_url,
            "categoria": {"id": cat.id, "nombre": cat.nombre} if cat else None,
            "categoria_id": prod.categoria_id, "proveedor": None, "proveedor_id": prod.proveedor_id
        },
        "stock": inv.cantidad,
        "max_s": prod.stock_maximo or STOCK_MAXIMO_POR_DEFECTO,
        "estado": _estado_inventario(inv.cantidad, prod.stock_minimo),
        "ubicacion": inv.ubicacion or UBICACION_POR_DEFECTO
    }


def api_get(endpoint: str) -> Any:
    """Lee datos de la BD local según el endpoint indicado."""
    session = db.session

    if "/categorias" in endpoint:
        cats = session.query(Categoria).filter_by(activo=True).all()
        return [{"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion} for c in cats]

    if "/proveedores" in endpoint:
        provs = session.query(Proveedor).filter_by(activo=True).all()
        return [{"id": p.id, "nombre": p.nombre, "email": p.email, "telefono": p.telefono} for p in provs]

    if "/productos" in endpoint:
        prods = session.query(Producto).filter_by(activo=True).all()
        invs = {i.producto_id: i for i in session.query(Inventario).all()}
        return [_producto_to_dict(p, invs.get(p.id)) for p in prods]

    if "/inventario" in endpoint:
        if "/resumen" in endpoint:
            return db.obtener_resumen_inventario()
        return [_inventario_to_dict(i) for i in session.query(Inventario).all()]

    if "/tickets" in endpoint:
        if "/estadisticas/resumen" in endpoint:
            return db.obtener_estadisticas_resumen()
        tickets = session.query(Ticket).order_by(Ticket.fecha.desc()).limit(200).all()
        return [_ticket_to_dict(t) for t in tickets]

    if "/prediccion" in endpoint:
        return {"alertas": []}

    if "/salud" in endpoint:
        return {"estado": "saludable"}

    return []


def api_post(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Crea un recurso en la BD local según el endpoint indicado."""
    try:
        if "/productos" in endpoint and "auth" not in endpoint:
            prod = db.crear_producto(data)
            return {"id": prod.id, "mensaje": "Producto creado"}
        if "/proveedores" in endpoint:
            prov = db.crear_proveedor(data)
            return {"id": prov.id, "nombre": prov.nombre}
        if "/inventario/" in endpoint:
            pid = int(endpoint.split("/")[-1])
            inv = db.session.query(Inventario).filter_by(producto_id=pid).first()
            if inv:
                inv.cantidad = data.get("cantidad", inv.cantidad)
                db.session.commit()
                return {"id": inv.id, "mensaje": "Inventario actualizado"}
            return {"error": "Inventario no encontrado"}
        if "/tickets" in endpoint:
            ticket = db.crear_ticket(data)
            return {"id": ticket.id, "numero_ticket": ticket.numero_ticket, "total": ticket.total}
        return None
    except (KeyError, ValueError, TypeError, SQLAlchemyError) as exc:
        return {"error": str(exc)}


def api_put(endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Actualiza un recurso de la BD local según el endpoint indicado."""
    try:
        if "/productos/" in endpoint:
            pid = int(endpoint.split("/")[-1])
            result = db.actualizar_producto(pid, data)
            if result:
                return {"id": result.id, "mensaje": "Producto actualizado"}
            return {"error": "Producto no encontrado"}
        return {"error": "Endpoint no soportado"}
    except (ValueError, TypeError, SQLAlchemyError) as exc:
        return {"error": str(exc)}


def api_delete(endpoint: str) -> bool:
    """Baja lógica de un producto. Devuelve False si no existe o no está soportado."""
    try:
        if "/productos/" in endpoint:
            pid = int(endpoint.split("/")[-1])
            return db.eliminar_producto(pid)
        return False
    except (ValueError, TypeError, SQLAlchemyError):
        return False


def verificar_api() -> bool:
    """Health check local: la BD responde a una consulta trivial."""
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        db.session.rollback()
        return False


def esperar_api(intentos: int = 15, espera_s: float = 1.0) -> bool:
    """Reintenta verificar_api hasta `intentos` veces, esperando `espera_s` entre ellas."""
    total = max(1, intentos)
    for intento in range(1, total + 1):
        if verificar_api():
            return True
        if intento < total:
            time.sleep(espera_s)
    return False