"""Acceso a datos de usuarios y perfiles. Las búsquedas normalizan la entrada."""

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.normalization import normalize_email, normalize_nickname
from app.models import Profile, User


def add_user_with_profile(session: Session, user: User, profile: Profile) -> User:
    """Añade ambos en la transacción actual. Las restricciones UNIQUE resuelven carreras."""
    user.email = normalize_email(user.email)
    profile.nickname = normalize_nickname(profile.nickname)
    user.profile = profile
    session.add(user)
    session.flush()
    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == normalize_email(email)))


def get_profile_by_nickname(session: Session, nickname: str) -> Profile | None:
    return session.scalar(select(Profile).where(Profile.nickname == normalize_nickname(nickname)))


def nickname_exists(session: Session, nickname: str) -> bool:
    stmt = select(exists().where(Profile.nickname == normalize_nickname(nickname)))
    return bool(session.scalar(stmt))
