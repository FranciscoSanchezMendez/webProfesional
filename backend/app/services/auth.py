"""Registro, credenciales y sesiones opacas (D-015)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import ApiError
from app.core.security import (
    hash_password,
    hash_token,
    new_token,
    password_needs_rehash,
    verify_password,
)
from app.models import Profile, User, UserSession
from app.repositories.users import add_user_with_profile, get_user_by_email, nickname_exists
from app.schemas.auth import RegisterRequest

EMAIL_TAKEN = ApiError(
    status.HTTP_409_CONFLICT, "email_taken", "Ya existe una cuenta con este email."
)
NICKNAME_TAKEN = ApiError(
    status.HTTP_409_CONFLICT, "nickname_taken", "Este nickname ya está en uso."
)
INVALID_CREDENTIALS = ApiError(
    status.HTTP_401_UNAUTHORIZED, "invalid_credentials", "Email o contraseña incorrectos."
)


def register_user(session: Session, data: RegisterRequest) -> User:
    if get_user_by_email(session, data.email) is not None:
        raise EMAIL_TAKEN
    if nickname_exists(session, data.nickname):
        raise NICKNAME_TAKEN
    user = User(email=data.email, password_hash=hash_password(data.password))
    profile = Profile(
        nickname=data.nickname,
        first_name=data.first_name,
        last_name=data.last_name,
        # El formulario no pide nombre visible: se deriva y será editable en Fase 4.
        display_name=f"{data.first_name} {data.last_name}"[:100],
        birth_date=data.birth_date,
        location=data.location,
        job_title=data.job_title,
        visibility=data.visibility,
        preferred_language=data.preferred_language,
    )
    try:
        add_user_with_profile(session, user, profile)
    except IntegrityError as exc:
        # Carrera entre la comprobación previa y el INSERT: la restricción UNIQUE decide.
        session.rollback()
        detail = str(exc.orig)
        if "uq_users_email" in detail:
            raise EMAIL_TAKEN from None
        if "uq_profiles_nickname" in detail:
            raise NICKNAME_TAKEN from None
        raise
    return user


def authenticate(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email)
    # verify_password se ejecuta aunque el usuario no exista: mismo tiempo de respuesta.
    valid = verify_password(user.password_hash if user else None, password)
    if user is None or not valid or not user.is_active:
        raise INVALID_CREDENTIALS
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
    return user


@dataclass(frozen=True)
class IssuedSession:
    token: str
    csrf_token: str
    record: UserSession


def create_session(
    session: Session, user: User, *, persistent: bool, settings: Settings
) -> IssuedSession:
    ttl = (
        timedelta(days=settings.session_remember_days)
        if persistent
        else timedelta(hours=settings.session_ttl_hours)
    )
    token, csrf_token = new_token(), new_token()
    record = UserSession(
        user_id=user.id,
        token_hash=hash_token(token),
        csrf_token_hash=hash_token(csrf_token),
        persistent=persistent,
        expires_at=datetime.now(UTC) + ttl,
    )
    session.add(record)
    session.flush()
    return IssuedSession(token=token, csrf_token=csrf_token, record=record)


def get_valid_session(session: Session, token: str) -> UserSession | None:
    stmt = (
        select(UserSession)
        .join(UserSession.user)
        .where(
            UserSession.token_hash == hash_token(token),
            UserSession.expires_at > datetime.now(UTC),
            User.is_active.is_(True),
        )
    )
    return session.scalar(stmt)


def revoke_session_token(session: Session, token: str) -> None:
    session.execute(delete(UserSession).where(UserSession.token_hash == hash_token(token)))


def purge_expired_sessions(session: Session) -> int:
    """Pensado para una tarea programada (Fase 10)."""
    result = session.execute(delete(UserSession).where(UserSession.expires_at <= datetime.now(UTC)))
    return result.rowcount
