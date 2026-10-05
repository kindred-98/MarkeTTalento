"""
Utilidades de fecha y hora.

Las columnas de fecha de la base de datos almacenan UTC naive (sin zona
horaria), por lo que todas las escrituras deben generarse con `utcnow_naive()`
en lugar de `datetime.utcnow()` (obsoleto desde Python 3.12) o
`datetime.now(timezone.utc)` (que produciria datetimes con zona horaria y
romperia las columnas DateTime).
"""
from datetime import date, datetime, timezone


def utcnow_naive() -> datetime:
    """Devuelve la hora actual en UTC como datetime naive (sin tzinfo)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def hoy_utc() -> date:
    """Devuelve la fecha actual en UTC."""
    return utcnow_naive().date()