import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import UserRole
from app.models.types import str_enum

if TYPE_CHECKING:
    from app.models.profile import Profile


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # El email se guarda normalizado; la BD lo garantiza aunque falle la capa de aplicación.
        CheckConstraint("email = lower(btrim(email))", name="email_normalized"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        str_enum(UserRole, "role"), default=UserRole.USER, server_default=UserRole.USER.value
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    profile: Mapped["Profile"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan", passive_deletes=True
    )

    def __repr__(self) -> str:  # sin email ni hash: no filtrar datos en logs
        return f"User(id={self.id}, role={self.role})"
