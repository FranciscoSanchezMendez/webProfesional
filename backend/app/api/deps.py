"""Dependencias compartidas: BD, sesión autenticada, CSRF y cookies."""

from typing import Annotated

from fastapi import Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import ApiError
from app.core.security import hash_token, tokens_match
from app.db.session import get_db
from app.models import User, UserSession
from app.services.auth import IssuedSession, get_valid_session

DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]

CSRF_HEADER = "X-CSRF-Token"

NOT_AUTHENTICATED = ApiError(
    status.HTTP_401_UNAUTHORIZED, "not_authenticated", "Necesitas iniciar sesión."
)
CSRF_FAILED = ApiError(status.HTTP_403_FORBIDDEN, "csrf_failed", "Token CSRF ausente o inválido.")


def cookie_names(settings: Settings) -> tuple[str, str]:
    """El prefijo __Host- (exige Secure, Path=/ y sin Domain) solo es posible bajo HTTPS."""
    prefix = "__Host-" if settings.cookie_secure else ""
    return f"{prefix}pp_session", f"{prefix}pp_csrf"


def read_session_token(request: Request, settings: Settings) -> str | None:
    return request.cookies.get(cookie_names(settings)[0])


def set_session_cookies(response: Response, issued: IssuedSession, settings: Settings) -> None:
    session_name, csrf_name = cookie_names(settings)
    max_age = settings.session_remember_days * 86400 if issued.record.persistent else None
    common = {"max_age": max_age, "path": "/", "secure": settings.cookie_secure, "samesite": "lax"}
    response.set_cookie(session_name, issued.token, httponly=True, **common)
    # Legible por JavaScript: el frontend lo reenvía en la cabecera X-CSRF-Token.
    response.set_cookie(csrf_name, issued.csrf_token, httponly=False, **common)


def clear_session_cookies(response: Response, settings: Settings) -> None:
    for name in cookie_names(settings):
        response.delete_cookie(name, path="/", secure=settings.cookie_secure, samesite="lax")


def get_current_session(request: Request, db: DbSession, settings: AppSettings) -> UserSession:
    token = read_session_token(request, settings)
    record = get_valid_session(db, token) if token else None
    if record is None:
        raise NOT_AUTHENTICATED
    return record


CurrentSession = Annotated[UserSession, Depends(get_current_session)]


def get_current_user(current: CurrentSession) -> User:
    return current.user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_csrf(request: Request, current: CurrentSession) -> None:
    """Para operaciones autenticadas que modifican datos (POST/PUT/PATCH/DELETE)."""
    header = request.headers.get(CSRF_HEADER)
    if not header or not tokens_match(hash_token(header), current.csrf_token_hash):
        raise CSRF_FAILED
