"""create users and profiles

Revision ID: f9b83d8d5ca7
Revises:
Create Date: 2026-11-18 21:07:15.896259

Tablas users y profiles (ver docs/DATABASE.md). Revisada manualmente.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f9b83d8d5ca7"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="role", native_enum=False, create_constraint=True),
            server_default="user",
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("email = lower(btrim(email))", name=op.f("ck_users_email_normalized")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_table(
        "profiles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("nickname", sa.String(length=30), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=False),
        sa.Column("last_name", sa.String(length=100), nullable=False),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("birth_date", sa.Date(), nullable=False),
        sa.Column("location", sa.String(length=120), nullable=True),
        sa.Column("job_title", sa.String(length=120), nullable=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("avatar_key", sa.String(length=255), nullable=True),
        sa.Column("cover_key", sa.String(length=255), nullable=True),
        sa.Column(
            "visibility",
            sa.Enum(
                "public", "private", name="visibility", native_enum=False, create_constraint=True
            ),
            server_default="public",
            nullable=False,
        ),
        sa.Column("show_age", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("is_deactivated", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "preferred_language",
            sa.Enum(
                "es", "en", name="preferred_language", native_enum=False, create_constraint=True
            ),
            server_default="es",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "nickname ~ '^[a-z0-9]([a-z0-9-]{1,28})[a-z0-9]$'",
            name=op.f("ck_profiles_nickname_format"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_profiles_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_profiles")),
        sa.UniqueConstraint("nickname", name=op.f("uq_profiles_nickname")),
        sa.UniqueConstraint("user_id", name=op.f("uq_profiles_user_id")),
    )


def downgrade() -> None:
    op.drop_table("profiles")
    op.drop_table("users")
