from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.api.deps import (
    AppSettings,
    CurrentUser,
    DbSession,
    clear_session_cookies,
    read_session_token,
    require_csrf,
    set_session_cookies,
)
from app.core.normalization import normalize_nickname
from app.repositories.users import nickname_exists
from app.schemas.auth import (
    LoginRequest,
    MeResponse,
    NicknameAvailability,
    RegisterRequest,
    nickname_problem,
)
from app.services import rate_limit
from app.services.auth import (
    authenticate,
    create_session,
    register_user,
    revoke_session_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _client_ip(request: Request) -> str:
    # Detrás de un proxy, uvicorn --proxy-headers rellena request.client desde X-Forwarded-For.
    return request.client.host if request.client else "unknown"


@router.get("/nickname-availability", response_model=NicknameAvailability)
def nickname_availability(
    request: Request, db: DbSession, nickname: Annotated[str, Query(max_length=64)]
) -> NicknameAvailability:
    """Informativo: no reserva el nickname; la restricción UNIQUE decide al registrar."""
    rate_limit.hit(db, rate_limit.NICKNAME_CHECK_PER_IP, _client_ip(request))
    normalized = normalize_nickname(nickname)
    problem = nickname_problem(normalized)
    if problem is None and nickname_exists(db, normalized):
        problem = "taken"
    return NicknameAvailability(nickname=normalized, available=problem is None, reason=problem)


@router.post("/register", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> MeResponse:
    rate_limit.hit(db, rate_limit.REGISTER_PER_IP, _client_ip(request))
    user = register_user(db, data)
    # Tras el registro se inicia sesión automáticamente (sesión de navegador).
    issued = create_session(db, user, persistent=False, settings=settings)
    db.commit()
    set_session_cookies(response, issued, settings)
    return MeResponse.model_validate(user)


@router.post("/login", response_model=MeResponse)
def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
    settings: AppSettings,
) -> MeResponse:
    rate_limit.hit(db, rate_limit.LOGIN_PER_IP, _client_ip(request))
    rate_limit.hit(db, rate_limit.LOGIN_PER_EMAIL, data.email)
    user = authenticate(db, data.email, data.password)
    # Evita la fijación de sesión: la sesión previa de este navegador deja de ser válida.
    if previous := read_session_token(request, settings):
        revoke_session_token(db, previous)
    user.last_login_at = datetime.now(UTC)
    issued = create_session(db, user, persistent=data.remember_me, settings=settings)
    db.commit()
    set_session_cookies(response, issued, settings)
    return MeResponse.model_validate(user)


@router.post(
    "/logout", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_csrf)]
)
def logout(request: Request, response: Response, db: DbSession, settings: AppSettings) -> None:
    if token := read_session_token(request, settings):
        revoke_session_token(db, token)
        db.commit()
    clear_session_cookies(response, settings)


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser, response: Response) -> MeResponse:
    response.headers["Cache-Control"] = "private, no-store"
    return MeResponse.model_validate(user)
