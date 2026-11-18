import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Date, ForeignKey, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import Language, ProfileVisibility
from app.models.types import str_enum

if TYPE_CHECKING:
    from app.models.user import User

# 3-30 caracteres: minúsculas ASCII, dígitos y guion; sin guion al inicio ni al final.
NICKNAME_PATTERN = r"^[a-z0-9]([a-z0-9-]{1,28})[a-z0-9]$"


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"
    __table_args__ = (CheckConstraint(f"nickname ~ '{NICKNAME_PATTERN}'", name="nickname_format"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    nickname: Mapped[str] = mapped_column(String(30), unique=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    display_name: Mapped[str] = mapped_column(String(100))
    # Dato privado: nunca debe aparecer en DTO públicos, SSR ni metadatos.
    birth_date: Mapped[date] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(String(120))
    job_title: Mapped[str | None] = mapped_column(String(120))
    biography: Mapped[str | None] = mapped_column(Text)
    avatar_key: Mapped[str | None] = mapped_column(String(255))
    cover_key: Mapped[str | None] = mapped_column(String(255))
    visibility: Mapped[ProfileVisibility] = mapped_column(
        str_enum(ProfileVisibility, "visibility"),
        default=ProfileVisibility.PUBLIC,
        server_default=ProfileVisibility.PUBLIC.value,
    )
    show_age: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    # Desactivación temporal por el propio usuario: perfil no visible, datos conservados.
    is_deactivated: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=text("false")
    )
    preferred_language: Mapped[Language] = mapped_column(
        str_enum(Language, "preferred_language"),
        default=Language.ES,
        server_default=Language.ES.value,
    )

    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"Profile(id={self.id}, nickname={self.nickname!r})"
