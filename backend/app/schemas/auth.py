import re
import uuid
from datetime import date
from typing import Annotated, Literal, Self

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    StringConstraints,
    model_validator,
)

from app.core.config import get_settings
from app.core.normalization import normalize_email, normalize_nickname
from app.core.reserved import is_reserved
from app.models import Language, ProfileVisibility, UserRole
from app.models.profile import NICKNAME_PATTERN

NICKNAME_RE = re.compile(NICKNAME_PATTERN)
PASSWORD_MIN_LENGTH = 7
PASSWORD_MAX_LENGTH = 30  # limita el coste de Argon2 ante entradas enormes

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
ShortText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Password = Annotated[str, Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)]


def nickname_problem(nickname: str) -> Literal["invalid", "reserved"] | None:
    """Comprueba un nickname ya normalizado. No consulta la BD."""
    if not NICKNAME_RE.fullmatch(nickname):
        return "invalid"
    if is_reserved(nickname):
        return "reserved"
    return None


def _valid_nickname(value: str) -> str:
    nickname = normalize_nickname(value)
    match nickname_problem(nickname):
        case "invalid":
            raise ValueError(
                "3-30 caracteres: letras, números y guion; sin guion al principio ni al final"
            )
        case "reserved":
            raise ValueError("Este nickname no está disponible")
    return nickname


def age_on(birth_date: date, today: date) -> int:
    before_birthday = (today.month, today.day) < (birth_date.month, birth_date.day)
    return today.year - birth_date.year - before_birthday


def _valid_birth_date(value: date) -> date:
    today = date.today()
    if value >= today:
        raise ValueError("La fecha de nacimiento debe ser anterior a hoy")
    if age_on(value, today) > 120:
        raise ValueError("Fecha de nacimiento no válida")
    min_age = get_settings().min_registration_age
    if age_on(value, today) < min_age:
        raise ValueError(f"Debes tener al menos {min_age} años")
    return value


Nickname = Annotated[str, Field(max_length=64), AfterValidator(_valid_nickname)]
NormalizedEmail = Annotated[EmailStr, Field(max_length=254), AfterValidator(normalize_email)]


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: Name
    last_name: Name
    nickname: Nickname
    birth_date: Annotated[date, AfterValidator(_valid_birth_date)]
    location: ShortText
    job_title: ShortText
    email: NormalizedEmail
    password: Password
    password_confirm: str = Field(max_length=PASSWORD_MAX_LENGTH)
    visibility: ProfileVisibility = ProfileVisibility.PUBLIC
    preferred_language: Language = Language.ES

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.password_confirm:
            raise ValueError("Las contraseñas no coinciden")
        return self


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: NormalizedEmail
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)
    remember_me: bool = False


class ProfileSummary(BaseModel):
    """Datos del propio perfil para la sesión. Sin birth_date."""

    model_config = ConfigDict(from_attributes=True)

    nickname: str
    display_name: str
    first_name: str
    last_name: str
    visibility: ProfileVisibility
    preferred_language: Language


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    role: UserRole
    profile: ProfileSummary


class NicknameAvailability(BaseModel):
    nickname: str
    available: bool
    reason: Literal["invalid", "reserved", "taken"] | None = None
