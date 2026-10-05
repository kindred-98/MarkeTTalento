"""
Capa de acceso directo a la base de datos para Streamlit Cloud
Reemplaza las llamadas HTTP por acceso directo a SQLite
"""
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.dominio.entidades.entidades import (
    Categoria, Proveedor, Producto, Inventario, Ticket, TicketLinea, Usuario
)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        db_path = os.getenv("DATABASE_PATH", "data/markettalento.db")
        url = f"sqlite:///{db_path}"
        _engine = create_engine(url, connect_args={"check_same_thread": False})
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())
    return _SessionLocal()


class DatabaseAccess:
    def __init__(self):
        self.session = get_session()

    def close(self):
        self.session.close()

    def get_categorias(self):
        return self.session.query(Categoria).filter_by(activo=True).all()

    def get_proveedores(self):
        return self.session.query(Proveedor).filter_by(activo=True).all()

    def get_productos(self):
        return self.session.query(Producto).filter_by(activo=True).all()

    def get_inventario(self):
        return self.session.query(Inventario).all()

    def get_tickets(self, limite=200):
        return self.session.query(Ticket).order_by(Ticket.fecha.desc()).limit(limite).all()

    def get_usuario_por_username(self, username):
        return self.session.query(Usuario).filter_by(username=username).first()

    def crear_producto(self, data):
        prod = Producto(
            sku=data["sku"], nombre=data["nombre"], precio_venta=data["precio_venta"],
            unidad=data["unidad"], stock_maximo=data.get("stock_maximo", 100),
            stock_minimo=data.get("stock_minimo", 0), categoria_id=data["categoria_id"],
            codigo_barras=data.get("codigo_barras"), precio_coste=data.get("precio_coste"),
            proveedor_id=data.get("proveedor_id"), descripcion=data.get("descripcion"),
            imagen_url=data.get("imagen_url"), tiempo_reposicion=data.get("tiempo_reposicion", 3)
        )
        self.session.add(prod)
        self.session.flush()
        inv = Inventario(
            producto_id=prod.id,
            cantidad=data.get("cantidad_inicial", data.get("unidad_ingreso", 0)),
            ubicacion=data.get("ubicacion", "Almacén A")
        )
        self.session.add(inv)
        self.session.commit()
        self.session.refresh(prod)
        return prod

    def actualizar_producto(self, producto_id, data):
        prod = self.session.get(Producto, producto_id)
        if not prod:
            return None
        for key, value in data.items():
            if hasattr(prod, key) and key not in ["id"]:
                setattr(prod, key, value)
        self.session.commit()
        self.session.refresh(prod)
        return prod

    def eliminar_producto(self, producto_id):
        prod = self.session.get(Producto, producto_id)
        if prod:
            prod.activo = False
            self.session.commit()
            return True
        return False

    def crear_categoria(self, data):
        cat = Categoria(**data)
        self.session.add(cat)
        self.session.commit()
        self.session.refresh(cat)
        return cat

    def crear_proveedor(self, data):
        prov = Proveedor(**data)
        self.session.add(prov)
        self.session.commit()
        self.session.refresh(prov)
        return prov

    def crear_ticket(self, data):
        ultimo = self.session.query(Ticket).order_by(Ticket.id.desc()).first()
        if ultimo and ultimo.numero_ticket:
            if "-" in ultimo.numero_ticket:
                nuevo_num = int(ultimo.numero_ticket.split("-")[1]) + 1
            else:
                try:
                    nuevo_num = int(ultimo.numero_ticket) + 1
                except ValueError:
                    nuevo_num = 1
        else:
            nuevo_num = 1
        numero_ticket = f"TKT-{nuevo_num:06d}"
        ticket = Ticket(
            numero_ticket=numero_ticket, cajero=data["cajero"], total=data["total"],
            metodo_pago=data["metodo_pago"], entrega_efectivo=data.get("entrega_efectivo"),
            cambio=data.get("cambio"), estado="completado"
        )
        self.session.add(ticket)
        self.session.flush()
        for linea_data in data.get("lineas", []):
            linea = TicketLinea(
                ticket_id=ticket.id, producto_id=linea_data["producto_id"],
                cantidad=linea_data["cantidad"], precio_unitario=linea_data["precio_unitario"],
                subtotal=linea_data["subtotal"]
            )
            self.session.add(linea)
            inv = self.session.query(Inventario).filter_by(producto_id=linea_data["producto_id"]).first()
            if inv:
                inv.cantidad -= linea_data["cantidad"]
                inv.fecha_ultima_actualizacion = datetime.utcnow()
        self.session.commit()
        self.session.refresh(ticket)
        return ticket

    def obtener_resumen_inventario(self):
        productos = self.session.query(Producto).filter_by(activo=True).all()
        inv_map = {inv.producto_id: inv.cantidad for inv in self.session.query(Inventario).all()}
        return {
            "total_productos": len(productos),
            "total_unidades": sum(inv_map.get(p.id, 0) for p in productos),
            "valor_total": sum(p.precio_venta * inv_map.get(p.id, 0) for p in productos)
        }

    def obtener_estadisticas_resumen(self):
        tickets = self.session.query(Ticket).filter_by(estado="completado").all()
        total_tickets = len(tickets)
        total_ingresos = sum(t.total for t in tickets)
        total_unidades = sum(sum(l.cantidad for l in t.lineas) for t in tickets)
        ticket_promedio = total_ingresos / total_tickets if total_tickets > 0 else 0
        metodos_pago = {}
        for t in tickets:
            metodos_pago[t.metodo_pago] = metodos_pago.get(t.metodo_pago, 0) + 1
        return {
            "total_tickets": total_tickets, "total_ingresos": total_ingresos,
            "total_unidades": total_unidades, "ticket_promedio": ticket_promedio,
            "metodos_pago": metodos_pago
        }


db = DatabaseAccess()