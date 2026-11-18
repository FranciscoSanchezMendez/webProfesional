from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import Engine

from app.db.health import check_database
from app.db.session import get_engine

router = APIRouter(prefix="/health", tags=["health"])


class LivenessResponse(BaseModel):
    status: Literal["ok"]


class ReadinessResponse(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]


@router.get("", response_model=LivenessResponse)
def liveness() -> LivenessResponse:
    """El proceso está vivo. No consulta dependencias externas."""
    return LivenessResponse(status="ok")


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
)
def readiness(
    response: Response, engine: Annotated[Engine, Depends(get_engine)]
) -> ReadinessResponse:
    """La API puede atender peticiones: PostgreSQL responde."""
    if check_database(engine):
        return ReadinessResponse(status="ok", database="ok")
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(status="error", database="unavailable")
