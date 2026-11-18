"""Contraseñas (Argon2id) y tokens opacos."""

import hashlib
import hmac
import secrets
import unicodedata

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# Valores por defecto de argon2-cffi: Argon2id, perfil RFC 9106 baja memoria (64 MiB, t=3, p=4).
_hasher = PasswordHasher()
# Hash de referencia para igualar el tiempo de respuesta cuando el email no existe.
_DUMMY_HASH = _hasher.hash("timing-equalizer-not-a-real-password")


def _normalize(password: str) -> str:
    # NFKC: la misma contraseña escrita con distintas formas Unicode produce el mismo hash.
    return unicodedata.normalize("NFKC", password)


def hash_password(password: str) -> str:
    return _hasher.hash(_normalize(password))


def verify_password(password_hash: str | None, password: str) -> bool:
    """Siempre ejecuta una verificación Argon2, aunque no haya hash (anti user-enumeration)."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, _normalize(password)) and (
            password_hash is not None
        )
    except (VerificationError, InvalidHashError):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    return _hasher.check_needs_rehash(password_hash)


def new_token() -> str:
    """256 bits aleatorios, URL-safe."""
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """En BD solo se guarda el SHA-256: una fuga de la tabla no permite suplantar sesiones."""
    return hashlib.sha256(token.encode()).hexdigest()


def tokens_match(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
