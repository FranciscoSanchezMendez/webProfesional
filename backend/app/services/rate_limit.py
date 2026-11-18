"""Rate limiting de ventana fija sobre PostgreSQL (D-017).

Funciona con varias instancias porque el contador vive en la BD. El sujeto (IP, email) se guarda
como SHA-256: no se almacenan IPs ni emails en claro.
"""

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import status
from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.errors import ApiError
from app.models import RateLimitCounter


@dataclass(frozen=True)
class Limit:
    action: str
    max_requests: int
    window: timedelta


LOGIN_PER_IP = Limit("login_ip", 20, timedelta(minutes=15))
LOGIN_PER_EMAIL = Limit("login_email", 10, timedelta(minutes=15))
REGISTER_PER_IP = Limit("register_ip", 5, timedelta(hours=1))
NICKNAME_CHECK_PER_IP = Limit("nickname_ip", 60, timedelta(minutes=1))


def _window_start(now: datetime, window: timedelta) -> datetime:
    seconds = int(window.total_seconds())
    return datetime.fromtimestamp(int(now.timestamp()) // seconds * seconds, tz=UTC)


def hit(session: Session, limit: Limit, subject: str, now: datetime | None = None) -> None:
    """Cuenta un intento y lanza 429 si se supera el límite.

    Hace commit inmediato: el intento debe contar aunque la petición falle después
    (p. ej. un login con contraseña incorrecta).
    """
    now = now or datetime.now(UTC)
    window_start = _window_start(now, limit.window)
    key = f"{limit.action}:{hashlib.sha256(subject.encode()).hexdigest()}"
    stmt = (
        insert(RateLimitCounter)
        .values(key=key, window_start=window_start, count=1)
        .on_conflict_do_update(
            index_elements=[RateLimitCounter.key, RateLimitCounter.window_start],
            set_={"count": RateLimitCounter.count + 1},
        )
        .returning(RateLimitCounter.count)
    )
    count = session.scalar(stmt)
    session.commit()
    if count is not None and count > limit.max_requests:
        retry_after = int((window_start + limit.window - now).total_seconds()) + 1
        raise ApiError(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "rate_limited",
            "Demasiados intentos. Inténtalo más tarde.",
            headers={"Retry-After": str(retry_after)},
        )


def purge_expired(session: Session, older_than: timedelta = timedelta(days=1)) -> int:
    """Borra contadores antiguos. Pensado para una tarea programada (Fase 10)."""
    cutoff = datetime.now(UTC) - older_than
    result = session.execute(delete(RateLimitCounter).where(RateLimitCounter.window_start < cutoff))
    return result.rowcount
