"""
Capa de acceso directo a SQLite para Streamlit
Reemplaza las llamadas HTTP por acceso directo a BD
"""
import streamlit as st
import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from app.db import DatabaseAccess
from src.dominio.entidades.entidades import (
    Categoria, Proveedor, Producto, Inventario, Ticket, TicketLinea
)

db = DatabaseAccess()


def _producto_to_dict(prod, inv=None):
    cat = prod.categoria
    prov = prod.proveedor
    stock = None
    if inv:
        stock = inv.cantidad
    elif prod.inventario:
        stock = prod.inventario.cantidad
    return {
        "id": prod.id, "sku": prod.sku, "codigo_barras": prod.codigo_barras,
        "nombre": prod.nombre, "descripcion": prod.descripcion,
        "precio_venta": prod.precio_venta, "precio_coste": prod.precio_coste,
        "unidad": prod.unidad, "stock_minimo": prod.stock_minimo,
        "stock_maximo": prod.stock_maximo, "tiempo_reposicion": prod.tiempo_reposicion,
        "imagen_url": prod.imagen_url, "activo": prod.activo,
        "fecha_creacion": prod.fecha_creacion.isoformat() if prod.fecha_creacion else None,
        "categoria": {"id": cat.id, "nombre": cat.nombre} if cat else None,
        "categoria_id": prod.categoria_id,
        "proveedor": {"id": prov.id, "nombre": prov.nombre} if prov else None,
        "proveedor_id": prod.proveedor_id
    }


def _inventario_to_dict(inv):
    prod = inv.producto
    cat = prod.categoria if prod else None
    if prod:
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
            "stock": inv.cantidad, "max_s": prod.stock_maximo or 100,
            "estado": "Agotado" if inv.cantidad == 0 else "Crítico" if inv.cantidad < prod.stock_minimo else "Saludable",
            "ubicacion": inv.ubicacion or "Almacén A"
        }
    return {"id": inv.id, "producto_id": inv.producto_id, "stock": inv.cantidad}


def api_get(endpoint: str, use_cache: bool = True, authenticated: bool = True) -> List[Dict[str, Any]]:
    session = db.session
    try:
        if "/categorias" in endpoint:
            cats = session.query(Categoria).filter_by(activo=True).all()
            return [{"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion} for c in cats]
        elif "/proveedores" in endpoint:
            provs = session.query(Proveedor).filter_by(activo=True).all()
            return [{"id": p.id, "nombre": p.nombre, "email": p.email, "telefono": p.telefono} for p in provs]
        elif "/productos" in endpoint:
            prods = session.query(Producto).filter_by(activo=True).all()
            invs = {i.producto_id: i for i in session.query(Inventario).all()}
            return [_producto_to_dict(p, invs.get(p.id)) for p in prods]
        elif "/inventario" in endpoint:
            if "/resumen" in endpoint:
                return db.obtener_resumen_inventario()
            return [_inventario_to_dict(i) for i in session.query(Inventario).all()]
        elif "/tickets" in endpoint:
            if "/estadisticas/resumen" in endpoint:
                return db.obtener_estadisticas_resumen()
            tickets = session.query(Ticket).order_by(Ticket.fecha.desc()).limit(200).all()
            result = []
            for t in tickets:
                lineas = []
                for l in t.lineas:
                    prod = session.query(Producto).get(l.producto_id)
                    lineas.append({
                        "id": l.id, "producto_id": l.producto_id, "cantidad": l.cantidad,
                        "precio_unitario": l.precio_unitario, "subtotal": l.subtotal,
                        "producto": {"nombre": prod.nombre} if prod else {"nombre": "N/A"}
                    })
                result.append({
                    "id": t.id, "numero_ticket": t.numero_ticket, "cajero": t.cajero,
                    "fecha": t.fecha.isoformat() if t.fecha else "", "total": t.total,
                    "metodo_pago": t.metodo_pago, "entrega_efectivo": t.entrega_efectivo,
                    "cambio": t.cambio, "estado": t.estado, "lineas": lineas
                })
            return result
        elif "/prediccion" in endpoint:
            return {"alertas": []}
        elif "/salud" in endpoint:
            return {"estado": "saludable"}
        return []
    finally:
        pass


def api_post(endpoint: str, data: Dict[str, Any], authenticated: bool = True) -> Optional[Dict[str, Any]]:
    try:
        if "/productos" in endpoint and "auth" not in endpoint:
            prod = db.crear_producto(data)
            return {"id": prod.id, "mensaje": "Producto creado"}
        elif "/proveedores" in endpoint:
            prov = db.crear_proveedor(data)
            return {"id": prov.id, "nombre": prov.nombre}
        elif "/inventario/" in endpoint:
            pid = int(endpoint.split("/")[-1])
            inv = db.session.query(Inventario).filter_by(producto_id=pid).first()
            if inv:
                inv.cantidad = data.get("cantidad", inv.cantidad)
                db.session.commit()
                return {"id": inv.id, "mensaje": "Inventario actualizado"}
            return {"error": "Inventario no encontrado"}
        elif "/tickets" in endpoint:
            return db.crear_ticket(data)
        return None
    except Exception as e:
        return {"error": str(e)}


def api_put(endpoint: str, data: Dict[str, Any], authenticated: bool = True) -> Optional[Dict[str, Any]]:
    try:
        if "/productos/" in endpoint:
            pid = int(endpoint.split("/")[-1])
            result = db.actualizar_producto(pid, data)
            if result:
                return {"id": result.id, "mensaje": "Producto actualizado"}
            return {"error": "Producto no encontrado"}
        return {"error": "Endpoint no soportado"}
    except Exception as e:
        return {"error": str(e)}


def api_delete(endpoint: str, authenticated: bool = True) -> bool:
    try:
        if "/productos/" in endpoint:
            pid = int(endpoint.split("/")[-1])
            return db.eliminar_producto(pid)
        return False
    except Exception:
        return False


def api_post_form(endpoint: str, data: dict, files: dict = None, authenticated: bool = True) -> Optional[Dict[str, Any]]:
    return api_post(endpoint, data, authenticated)


def verificar_api() -> bool:
    return True


def esperar_api(intentos: int = 15) -> bool:
    return True