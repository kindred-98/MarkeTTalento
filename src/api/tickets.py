"""
Router de Tickets - TPV MarkeTTalento
Transacciones atómicas con control de concurrencia
"""
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, extract

from src.core.database.database import get_db
from src.core.security.auth import get_current_user
from src.dominio.entidades.entidades import Ticket, TicketLinea, Producto, Inventario
from src.aplicacion.schemas.schemas import TicketCreate, TicketResponse

router = APIRouter()


# ============================================================================
# HELPERS
# ============================================================================

def _generar_numero_ticket(db: Session) -> str:
    """Genera número de ticket autoincremental con formato 000001."""
    ultimo = db.query(func.max(Ticket.id)).scalar()
    siguiente = (ultimo or 0) + 1
    return str(siguiente).zfill(6)


def _calcular_total_lineas(lineas_data: list) -> float:
    """Calcula el total de un ticket a partir de sus líneas."""
    total = 0.0
    for linea in lineas_data:
        total += linea.cantidad * linea.precio_unitario
    return round(total, 2)


# ============================================================================
# CRUD TICKETS
# ============================================================================

def _validar_lineas_no_vacias(lineas) -> None:
    """El ticket debe incluir al menos una línea."""
    if not lineas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ticket debe tener al menos una línea"
        )


def _cargar_y_validar_productos(db: Session, productos_ids: list) -> dict:
    """Carga los productos del ticket y verifica que todos existan."""
    productos = db.query(Producto).filter(Producto.id.in_(productos_ids)).all()
    productos_dict = {p.id: p for p in productos}

    for pid in productos_ids:
        if pid not in productos_dict:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Producto {pid} no encontrado"
            )

    return productos_dict


def _bloquear_inventarios(db: Session, productos_ids: list) -> dict:
    """Bloquea los inventarios (FOR UPDATE) para evitar ventas simultáneas."""
    inventarios = db.query(Inventario).filter(
        Inventario.producto_id.in_(productos_ids)
    ).with_for_update().all()
    return {inv.producto_id: inv for inv in inventarios}


def _validar_stock(lineas, inv_dict: dict, productos_dict: dict) -> None:
    """Verifica que cada línea tenga inventario registrado y stock suficiente."""
    for linea in lineas:
        inv = inv_dict.get(linea.producto_id)
        if not inv:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Producto {linea.producto_id} sin inventario registrado"
            )
        if inv.cantidad < linea.cantidad:
            prod = productos_dict[linea.producto_id]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock insuficiente para '{prod.nombre}'. Disponible: {inv.cantidad}, Solicitado: {linea.cantidad}"
            )


def _calcular_cambio(ticket_data, total: float):
    """Devuelve el cambio a devolver, o None si el pago no es en efectivo."""
    if ticket_data.metodo_pago != "efectivo" or ticket_data.entrega_efectivo is None:
        return None

    cambio = round(ticket_data.entrega_efectivo - total, 2)
    if cambio < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El monto entregado (€{ticket_data.entrega_efectivo}) es menor al total (€{total})"
        )
    return cambio


def _crear_lineas_y_descontar_stock(db: Session, db_ticket, lineas, inv_dict: dict) -> None:
    """Crea las líneas del ticket y descuenta el stock de cada producto."""
    ahora = datetime.now(timezone.utc)

    for linea in lineas:
        db.add(TicketLinea(
            ticket_id=db_ticket.id,
            producto_id=linea.producto_id,
            cantidad=linea.cantidad,
            precio_unitario=linea.precio_unitario,
            subtotal=round(linea.cantidad * linea.precio_unitario, 2)
        ))

        inv = inv_dict[linea.producto_id]
        inv.cantidad -= linea.cantidad
        inv.fecha_ultima_actualizacion = ahora


@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def crear_ticket(ticket_data: TicketCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Crea un ticket completo con transacción atómica.
    Bloquea filas de inventario para evitar race conditions.
    """
    _validar_lineas_no_vacias(ticket_data.lineas)

    try:
        # Iniciar transacción manualmente
        db.begin_nested()

        productos_ids = [linea.producto_id for linea in ticket_data.lineas]
        productos_dict = _cargar_y_validar_productos(db, productos_ids)
        inv_dict = _bloquear_inventarios(db, productos_ids)
        _validar_stock(ticket_data.lineas, inv_dict, productos_dict)

        total = _calcular_total_lineas(ticket_data.lineas)
        cambio = _calcular_cambio(ticket_data, total)

        db_ticket = Ticket(
            numero_ticket=_generar_numero_ticket(db),
            cajero=ticket_data.cajero,
            fecha=datetime.now(timezone.utc),
            total=total,
            metodo_pago=ticket_data.metodo_pago,
            entrega_efectivo=ticket_data.entrega_efectivo,
            cambio=cambio,
            estado="completado"
        )
        db.add(db_ticket)
        db.flush()  # Para obtener el ID del ticket

        _crear_lineas_y_descontar_stock(db, db_ticket, ticket_data.lineas, inv_dict)

        db.commit()
        db.refresh(db_ticket)

        # Cargar relaciones para la respuesta
        for linea in db_ticket.lineas:
            db.refresh(linea)

        return db_ticket

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al crear el ticket. Contacte al administrador."
        )


SUFIJO_UTC_ISO = "+00:00"


def _parsear_fecha_iso(valor: str, nombre_campo: str) -> datetime:
    """Parsea una fecha ISO 8601 aceptando el sufijo 'Z' de UTC."""
    try:
        return datetime.fromisoformat(valor.replace("Z", SUFIJO_UTC_ISO))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formato de {nombre_campo} invalido: {valor}. Use ISO 8601"
        )


@router.get("", response_model=List[TicketResponse])
async def listar_tickets(
    limite: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    cajero: Optional[str] = Query(None),
    metodo_pago: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Lista tickets con filtros opcionales."""
    query = db.query(Ticket)

    if fecha_desde:
        query = query.filter(Ticket.fecha >= _parsear_fecha_iso(fecha_desde, "fecha_desde"))

    if fecha_hasta:
        query = query.filter(Ticket.fecha <= _parsear_fecha_iso(fecha_hasta, "fecha_hasta"))

    if cajero:
        query = query.filter(Ticket.cajero == cajero)

    if metodo_pago:
        query = query.filter(Ticket.metodo_pago == metodo_pago)

    if estado:
        query = query.filter(Ticket.estado == estado)

    return query.order_by(Ticket.fecha.desc()).offset(offset).limit(limite).all()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def obtener_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Obtiene un ticket por su ID."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} no encontrado"
        )
    return ticket


@router.delete("/{ticket_id}", status_code=status.HTTP_200_OK)
async def anular_ticket(ticket_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Anula un ticket y reintegra el stock al inventario.
    Solo permite anular tickets del día actual.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket {ticket_id} no encontrado"
        )

    if ticket.estado == "anulado":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El ticket ya está anulado"
        )

    # Solo permitir anular tickets del día actual
    hoy = datetime.now(timezone.utc).date()
    fecha_ticket = ticket.fecha.date() if ticket.fecha.tzinfo else ticket.fecha.replace(tzinfo=timezone.utc).date()

    if fecha_ticket != hoy:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden anular tickets del día actual"
        )

    try:
        db.begin_nested()

        # Bloquear inventarios
        productos_ids = [linea.producto_id for linea in ticket.lineas]
        inventarios = db.query(Inventario).filter(
            Inventario.producto_id.in_(productos_ids)
        ).with_for_update().all()
        inv_dict = {inv.producto_id: inv for inv in inventarios}

        # Reintegrar stock
        for linea in ticket.lineas:
            inv = inv_dict.get(linea.producto_id)
            if inv:
                inv.cantidad += linea.cantidad
                inv.fecha_ultima_actualizacion = datetime.now(timezone.utc)

        # Marcar ticket como anulado
        ticket.estado = "anulado"

        db.commit()
        return {"message": f"Ticket {ticket.numero_ticket} anulado correctamente", "ticket_id": ticket_id}

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al anular ticket: {str(e)}"
        )


# ============================================================================
# ESTADÍSTICAS Y DASHBOARD
# ============================================================================

def _parsear_fecha_iso_opcional(valor: Optional[str]):
    """Como _parsear_fecha_iso, pero devuelve None si la fecha no es válida."""
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor.replace("Z", SUFIJO_UTC_ISO))
    except Exception:
        return None


@router.get("/estadisticas/resumen")
async def resumen_estadisticas(
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Resumen de métricas clave para el dashboard."""
    query = db.query(Ticket).filter(Ticket.estado == "completado")

    fd = _parsear_fecha_iso_opcional(fecha_desde)
    if fd:
        query = query.filter(Ticket.fecha >= fd)

    fh = _parsear_fecha_iso_opcional(fecha_hasta)
    if fh:
        query = query.filter(Ticket.fecha <= fh)

    tickets = query.all()

    total_ingresos = sum(t.total for t in tickets)
    total_tickets = len(tickets)
    ticket_promedio = total_ingresos / total_tickets if total_tickets > 0 else 0

    # Unidades vendidas (sumar cantidades de líneas)
    total_unidades = 0
    for t in tickets:
        for linea in t.lineas:
            total_unidades += linea.cantidad

    # Métodos de pago
    metodos = {}
    for t in tickets:
        metodos[t.metodo_pago] = metodos.get(t.metodo_pago, 0) + 1

    return {
        "total_ingresos": round(total_ingresos, 2),
        "total_tickets": total_tickets,
        "ticket_promedio": round(ticket_promedio, 2),
        "total_unidades": total_unidades,
        "metodos_pago": metodos
    }


@router.get("/estadisticas/tendencia")
async def tendencia_ventas(
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Tendencia de ventas por día (últimos N días)."""
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    tickets = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= fecha_limite
    ).all()

    datos = {}
    for t in tickets:
        fecha_str = t.fecha.strftime("%Y-%m-%d")
        if fecha_str not in datos:
            datos[fecha_str] = {"fecha": fecha_str, "ingresos": 0, "tickets": 0, "unidades": 0}
        datos[fecha_str]["ingresos"] += t.total
        datos[fecha_str]["tickets"] += 1
        for linea in t.lineas:
            datos[fecha_str]["unidades"] += linea.cantidad

    return sorted(datos.values(), key=lambda x: x["fecha"])


@router.get("/estadisticas/por-categoria")
async def ventas_por_categoria(
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Ventas agrupadas por categoría de producto."""
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    tickets = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= fecha_limite
    ).all()

    datos = {}
    for t in tickets:
        for linea in t.lineas:
            if linea.producto and linea.producto.categoria:
                cat_nombre = linea.producto.categoria.nombre
                if cat_nombre not in datos:
                    datos[cat_nombre] = {"categoria": cat_nombre, "ingresos": 0, "unidades": 0}
                datos[cat_nombre]["ingresos"] += linea.subtotal
                datos[cat_nombre]["unidades"] += linea.cantidad

    return sorted(datos.values(), key=lambda x: x["ingresos"], reverse=True)


@router.get("/estadisticas/por-hora")
async def ventas_por_hora(
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Distribución de ventas por hora del día."""
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    tickets = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= fecha_limite
    ).all()

    horas = {h: {"hora": h, "ventas": 0, "ingresos": 0} for h in range(24)}
    for t in tickets:
        hora = t.fecha.hour
        horas[hora]["ventas"] += 1
        horas[hora]["ingresos"] += t.total

    return list(horas.values())


@router.get("/estadisticas/mapa-calor")
async def mapa_calor(
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Mapa de calor: ventas por día de semana (0=lunes) y hora."""
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    tickets = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= fecha_limite
    ).all()

    # Inicializar matriz 7 días x 24 horas
    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    matriz = []
    for d in range(7):
        fila = {"dia": dias_semana[d], "dia_num": d, "horas": []}
        for h in range(24):
            fila["horas"].append({"hora": h, "ventas": 0, "ingresos": 0})
        matriz.append(fila)

    for t in tickets:
        # weekday(): 0=lunes, 6=domingo
        dia = t.fecha.weekday()
        hora = t.fecha.hour
        matriz[dia]["horas"][hora]["ventas"] += 1
        matriz[dia]["horas"][hora]["ingresos"] += t.total

    return matriz


@router.get("/estadisticas/comparativa-mes")
async def comparativa_mes(db: Session = Depends(get_db)):
    """Compara mes actual vs mes anterior."""
    hoy = datetime.now(timezone.utc)

    # Mes actual
    inicio_mes_actual = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    tickets_actual = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= inicio_mes_actual
    ).all()

    # Mes anterior
    if inicio_mes_actual.month == 1:
        inicio_mes_anterior = inicio_mes_actual.replace(year=inicio_mes_actual.year - 1, month=12)
    else:
        inicio_mes_anterior = inicio_mes_actual.replace(month=inicio_mes_actual.month - 1)

    fin_mes_anterior = inicio_mes_actual - timedelta(microseconds=1)
    tickets_anterior = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= inicio_mes_anterior,
        Ticket.fecha <= fin_mes_anterior
    ).all()

    def calcular_metricas(tickets):
        ingresos = sum(t.total for t in tickets)
        unidades = sum(l.cantidad for t in tickets for l in t.lineas)
        return {
            "ingresos": round(ingresos, 2),
            "tickets": len(tickets),
            "unidades": unidades,
            "ticket_promedio": round(ingresos / len(tickets), 2) if tickets else 0
        }

    return {
        "mes_actual": calcular_metricas(tickets_actual),
        "mes_anterior": calcular_metricas(tickets_anterior),
        "nombre_mes_actual": inicio_mes_actual.strftime("%B %Y"),
        "nombre_mes_anterior": inicio_mes_anterior.strftime("%B %Y")
    }


@router.get("/estadisticas/top-productos")
async def top_productos(
    dias: int = Query(30, ge=1, le=365),
    por: str = Query("unidades", regex="^(unidades|ingresos)$"),
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Top productos por unidades vendidas o ingresos generados."""
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    tickets = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= fecha_limite
    ).all()

    datos = {}
    for t in tickets:
        for linea in t.lineas:
            nombre = linea.producto.nombre if linea.producto else f"Producto {linea.producto_id}"
            if nombre not in datos:
                datos[nombre] = {"producto": nombre, "unidades": 0, "ingresos": 0}
            datos[nombre]["unidades"] += linea.cantidad
            datos[nombre]["ingresos"] += linea.subtotal

    ordenar_por = "unidades" if por == "unidades" else "ingresos"
    resultado = sorted(datos.values(), key=lambda x: x[ordenar_por], reverse=True)[:limite]
    return resultado


@router.get("/estadisticas/ticket-promedio")
async def evolucion_ticket_promedio(
    dias: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Evolución del ticket promedio por día."""
    fecha_limite = datetime.now(timezone.utc) - timedelta(days=dias)

    tickets = db.query(Ticket).filter(
        Ticket.estado == "completado",
        Ticket.fecha >= fecha_limite
    ).all()

    datos = {}
    for t in tickets:
        fecha_str = t.fecha.strftime("%Y-%m-%d")
        if fecha_str not in datos:
            datos[fecha_str] = {"fecha": fecha_str, "total": 0, "tickets": 0}
        datos[fecha_str]["total"] += t.total
        datos[fecha_str]["tickets"] += 1

    resultado = []
    for fecha_str in sorted(datos.keys()):
        d = datos[fecha_str]
        resultado.append({
            "fecha": fecha_str,
            "ticket_promedio": round(d["total"] / d["tickets"], 2),
            "total_ingresos": round(d["total"], 2),
            "total_tickets": d["tickets"]
        })

    return resultado


@router.get("/historial/{producto_id}")
async def historial_producto(
    producto_id: int,
    limite: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Obtiene los últimos tickets donde apareció un producto."""
    lineas = db.query(TicketLinea).join(Ticket).filter(
        TicketLinea.producto_id == producto_id,
        Ticket.estado == "completado"
    ).order_by(Ticket.fecha.desc()).limit(limite).all()

    resultado = []
    for linea in lineas:
        ticket = linea.ticket
        resultado.append({
            "ticket_id": ticket.id,
            "numero_ticket": ticket.numero_ticket,
            "fecha": ticket.fecha.isoformat() if hasattr(ticket.fecha, 'isoformat') else str(ticket.fecha),
            "cajero": ticket.cajero,
            "cantidad": linea.cantidad,
            "precio_unitario": linea.precio_unitario,
            "subtotal_linea": linea.subtotal,
            "total_ticket": ticket.total,
            "metodo_pago": ticket.metodo_pago,
        })

    return resultado
