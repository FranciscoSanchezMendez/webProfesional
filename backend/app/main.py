from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import register_error_handlers

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="PersonalProfile API",
        version="0.1.0",
        docs_url="/api/docs" if settings.docs_enabled else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if settings.docs_enabled else None,
    )
    register_error_handlers(app)

    trusted_origins = frozenset(settings.cors_origins)

    @app.middleware("http")
    async def check_origin(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Defensa CSRF complementaria: un navegador en otro origen no puede modificar datos."""
        origin = request.headers.get("origin")
        if request.method in UNSAFE_METHODS and origin and origin not in trusted_origins:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": {"code": "origin_not_allowed", "message": "Origen no permitido."}
                },
            )
        return await call_next(request)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Content-Type", "X-CSRF-Token"],
        )
    app.include_router(api_router)
    return app


app = create_app()
