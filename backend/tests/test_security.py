from datetime import UTC, datetime, timedelta

from app.core.security import hash_password, hash_token, new_token, verify_password
from app.schemas.auth import age_on
from app.services.rate_limit import _window_start


def test_password_hash_is_argon2id_and_verifies() -> None:
    hashed = hash_password("contraseña-segura-123")
    assert hashed.startswith("$argon2id$")
    assert verify_password(hashed, "contraseña-segura-123")
    assert not verify_password(hashed, "otra-contraseña-123")


def test_password_unicode_is_normalized() -> None:
    composed = "contraseña-larga"  # ñ como un único carácter
    decomposed = "contraseña-larga"  # n + tilde combinada
    assert verify_password(hash_password(composed), decomposed)


def test_verify_without_hash_is_false() -> None:
    assert not verify_password(None, "lo-que-sea")


def test_tokens_are_random_and_only_hash_is_stored() -> None:
    a, b = new_token(), new_token()
    assert a != b and len(a) >= 43
    assert len(hash_token(a)) == 64 and hash_token(a) != a


def test_age_on_birthday_boundaries() -> None:
    from datetime import date

    assert age_on(date(2010, 6, 15), date(2024, 6, 14)) == 13
    assert age_on(date(2010, 6, 15), date(2024, 6, 15)) == 14
    assert age_on(date(2008, 2, 29), date(2022, 2, 28)) == 13  # bisiesto


def test_rate_limit_window_is_aligned() -> None:
    now = datetime(2026, 1, 1, 10, 7, 42, tzinfo=UTC)
    assert _window_start(now, timedelta(minutes=15)) == datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
    assert _window_start(now, timedelta(hours=1)) == datetime(2026, 1, 1, 10, 0, tzinfo=UTC)
