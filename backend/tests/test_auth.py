from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import User, UserSession

pytestmark = pytest.mark.db

PASSWORD = "una-contraseña-larga"


def years_ago(years: int, days: int = 0) -> str:
    today = date.today()
    return (today.replace(year=today.year - years) + timedelta(days=days)).isoformat()


def register_payload(**overrides: Any) -> dict[str, Any]:
    payload = {
        "first_name": "Ana",
        "last_name": "García",
        "nickname": "@Ana-Dev",
        "birth_date": "1990-05-17",
        "location": "Sevilla",
        "job_title": "Desarrolladora",
        "email": "Ana@Example.com",
        "password": PASSWORD,
        "password_confirm": PASSWORD,
    }
    return payload | overrides


def register(client: TestClient, **overrides: Any) -> Any:
    return client.post("/api/v1/auth/register", json=register_payload(**overrides))


def login(client: TestClient, **overrides: Any) -> Any:
    body = {"email": "ana@example.com", "password": PASSWORD} | overrides
    return client.post("/api/v1/auth/login", json=body)


def set_cookie_headers(response: Any) -> dict[str, str]:
    return {h.split("=", 1)[0]: h for h in response.headers.get_list("set-cookie")}


# --- Registro ----------------------------------------------------------------------------------


def test_register_creates_account_and_logs_in(client: TestClient, db_session: Session) -> None:
    response = register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert body["role"] == "user"
    assert body["profile"]["nickname"] == "ana-dev"
    assert body["profile"]["display_name"] == "Ana García"
    assert "birth_date" not in body["profile"] and "password_hash" not in body

    cookies = set_cookie_headers(response)
    assert "HttpOnly" in cookies["pp_session"] and "SameSite=lax" in cookies["pp_session"]
    assert "HttpOnly" not in cookies["pp_csrf"]
    assert "Max-Age" not in cookies["pp_session"]  # sesión de navegador tras el registro
    assert client.get("/api/v1/auth/me").status_code == 200

    user = db_session.scalar(select(User))
    assert user is not None and user.password_hash.startswith("$argon2id$")
    assert PASSWORD not in user.password_hash


@pytest.mark.parametrize(
    ("overrides", "code"),
    [
        ({"email": "ANA@example.com", "nickname": "otra"}, "email_taken"),
        ({"email": "otra@example.com", "nickname": "ANA-DEV"}, "nickname_taken"),
    ],
)
def test_register_rejects_duplicates(
    client: TestClient, overrides: dict[str, str], code: str
) -> None:
    assert register(client).status_code == 201
    response = register(client, **overrides)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == code


@pytest.mark.parametrize(
    "overrides",
    [
        {"birth_date": years_ago(14, days=1)},  # cumple 14 mañana
        {"birth_date": (date.today() + timedelta(days=1)).isoformat()},
        {"password": "x" * 6, "password_confirm": "x" * 6},  # mínimo 7 (D-022)
        {"password": "x" * 31, "password_confirm": "x" * 31},  # máximo 30 (D-022)
        {"password_confirm": "otra-contraseña-larga"},
        {"nickname": "admin"},
        {"nickname": "-ana"},
        {"nickname": "ana_dev"},
        {"email": "no-es-un-email"},
        {"first_name": "   "},
        {"role": "admin"},  # no se puede auto-asignar rol
    ],
)
def test_register_validation_errors(client: TestClient, overrides: dict[str, str]) -> None:
    response = register(client, **overrides)
    assert response.status_code == 422


def test_register_accepts_exactly_minimum_age(client: TestClient) -> None:
    assert register(client, birth_date=years_ago(14)).status_code == 201


@pytest.mark.parametrize("length", [7, 30])
def test_register_accepts_password_length_limits(client: TestClient, length: int) -> None:
    password = "x" * length
    response = register(client, password=password, password_confirm=password)
    assert response.status_code == 201


# --- Disponibilidad de nickname ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("nickname", "expected"),
    [
        ("@Nuevo-Nick", {"nickname": "nuevo-nick", "available": True, "reason": None}),
        ("ANA-DEV", {"nickname": "ana-dev", "available": False, "reason": "taken"}),
        ("login", {"nickname": "login", "available": False, "reason": "reserved"}),
        ("a_b", {"nickname": "a_b", "available": False, "reason": "invalid"}),
    ],
)
def test_nickname_availability(
    client: TestClient, nickname: str, expected: dict[str, object]
) -> None:
    register(client)
    response = client.get("/api/v1/auth/nickname-availability", params={"nickname": nickname})
    assert response.status_code == 200
    assert response.json() == expected


# --- Login, sesión y logout --------------------------------------------------------------------


def test_login_without_remember_me_uses_browser_session_cookie(
    client: TestClient, db_session: Session
) -> None:
    register(client)
    client.cookies.clear()
    response = login(client)

    assert response.status_code == 200
    cookies = set_cookie_headers(response)
    assert "Max-Age" not in cookies["pp_session"]
    # Registro + login = 2 sesiones (now() es constante dentro de la transacción del test).
    records = db_session.scalars(select(UserSession)).all()
    assert len(records) == 2 and not any(r.persistent for r in records)
    ttl = max(r.expires_at for r in records) - datetime.now(UTC)
    assert timedelta(hours=11) < ttl <= timedelta(hours=get_settings().session_ttl_hours)


def test_login_with_remember_me_uses_persistent_cookie(client: TestClient) -> None:
    register(client)
    client.cookies.clear()
    response = login(client, remember_me=True)

    assert response.status_code == 200
    max_age = get_settings().session_remember_days * 86400
    assert f"Max-Age={max_age}" in set_cookie_headers(response)["pp_session"]


def test_login_errors_are_generic(client: TestClient, db_session: Session) -> None:
    register(client)
    client.cookies.clear()
    wrong_password = login(client, password="contraseña-incorrecta")
    unknown_email = login(client, email="nadie@example.com")
    db_session.execute(update(User).values(is_active=False))
    inactive = login(client)

    for response in (wrong_password, unknown_email, inactive):
        assert response.status_code == 401
        assert response.json() == {
            "error": {"code": "invalid_credentials", "message": "Email o contraseña incorrectos."}
        }
        assert "set-cookie" not in response.headers


def test_login_updates_last_login_and_rotates_session(
    client: TestClient, db_session: Session
) -> None:
    register(client)
    old_token = client.cookies.get("pp_session")
    assert login(client).status_code == 200

    assert client.cookies.get("pp_session") != old_token
    assert db_session.scalar(select(User.last_login_at)) is not None
    stale = TestClient(client.app, cookies={"pp_session": old_token or ""})
    assert stale.get("/api/v1/auth/me").status_code == 401


def test_me_requires_valid_unexpired_session(client: TestClient, db_session: Session) -> None:
    assert client.get("/api/v1/auth/me").json()["error"]["code"] == "not_authenticated"

    register(client)
    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.headers["cache-control"] == "private, no-store"

    db_session.execute(update(UserSession).values(expires_at=datetime.now(UTC)))
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_requires_csrf_token(client: TestClient, db_session: Session) -> None:
    register(client)
    csrf = client.cookies.get("pp_csrf")
    assert csrf

    missing = client.post("/api/v1/auth/logout")
    wrong = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "x" * 43})
    for response in (missing, wrong):
        assert response.status_code == 403
        assert response.json()["error"]["code"] == "csrf_failed"

    ok = client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf})
    assert ok.status_code == 204
    assert db_session.scalar(select(UserSession)) is None
    assert client.get("/api/v1/auth/me").status_code == 401


def test_logout_requires_authentication(client: TestClient) -> None:
    assert client.post("/api/v1/auth/logout").status_code == 401


# --- Origin y rate limiting --------------------------------------------------------------------


def test_untrusted_origin_cannot_post(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "ana@example.com", "password": PASSWORD},
        headers={"Origin": "https://evil.example"},
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "origin_not_allowed"


def test_login_is_rate_limited_per_email(client: TestClient) -> None:
    register(client)
    client.cookies.clear()
    for _ in range(10):
        assert login(client, password="contraseña-incorrecta").status_code == 401
    blocked = login(client)  # incluso con la contraseña correcta
    assert blocked.status_code == 429
    assert blocked.json()["error"]["code"] == "rate_limited"
    assert int(blocked.headers["retry-after"]) > 0


def test_register_is_rate_limited_per_ip(client: TestClient) -> None:
    for i in range(5):
        assert register(client, email=f"u{i}@example.com", nickname=f"user-{i}").status_code == 201
    assert register(client, email="u9@example.com", nickname="user-9").status_code == 429


def test_nickname_check_is_rate_limited(client: TestClient) -> None:
    url = "/api/v1/auth/nickname-availability"
    for _ in range(60):
        assert client.get(url, params={"nickname": "libre"}).status_code == 200
    assert client.get(url, params={"nickname": "libre"}).status_code == 429
