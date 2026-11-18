from datetime import date

import pytest
from sqlalchemy import delete, select, text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models import Language, Profile, ProfileVisibility, User, UserRole
from app.repositories.users import (
    add_user_with_profile,
    get_profile_by_nickname,
    get_user_by_email,
    nickname_exists,
)

pytestmark = pytest.mark.db


def make_user(email: str = "Ana@Example.com ", nickname: str = "@Ana-Dev") -> tuple[User, Profile]:
    user = User(email=email, password_hash="argon2id$placeholder")
    profile = Profile(
        nickname=nickname,
        first_name="Ana",
        last_name="García",
        display_name="Ana G.",
        birth_date=date(1990, 5, 17),
    )
    return user, profile


def test_add_user_with_profile_normalizes_and_applies_defaults(db_session: Session) -> None:
    user = add_user_with_profile(db_session, *make_user())
    db_session.refresh(user)

    assert user.email == "ana@example.com"
    assert user.role is UserRole.USER
    assert user.is_active is True
    assert user.created_at is not None and user.updated_at is not None
    assert user.profile.nickname == "ana-dev"
    assert user.profile.visibility is ProfileVisibility.PUBLIC
    assert user.profile.preferred_language is Language.ES
    assert user.profile.show_age is False
    assert user.profile.is_deactivated is False


def test_lookups_are_case_insensitive(db_session: Session) -> None:
    add_user_with_profile(db_session, *make_user())

    assert get_user_by_email(db_session, "  ANA@example.COM") is not None
    assert get_user_by_email(db_session, "otra@example.com") is None
    profile = get_profile_by_nickname(db_session, "@ANA-dev")
    assert profile is not None and profile.display_name == "Ana G."
    assert nickname_exists(db_session, "Ana-Dev")
    assert not nickname_exists(db_session, "nadie")


def test_duplicate_email_is_rejected(db_session: Session) -> None:
    add_user_with_profile(db_session, *make_user())
    with pytest.raises(IntegrityError, match="uq_users_email"):
        add_user_with_profile(db_session, *make_user(email="ANA@example.com", nickname="otra"))


def test_duplicate_nickname_is_rejected(db_session: Session) -> None:
    add_user_with_profile(db_session, *make_user())
    with pytest.raises(IntegrityError, match="uq_profiles_nickname"):
        add_user_with_profile(db_session, *make_user(email="otra@example.com", nickname="ANA-DEV"))


def test_user_has_at_most_one_profile(db_session: Session) -> None:
    user = add_user_with_profile(db_session, *make_user())
    _, second = make_user(nickname="segundo")
    second.user_id = user.id
    db_session.add(second)
    with pytest.raises(IntegrityError, match="uq_profiles_user_id"):
        db_session.flush()


def test_database_rejects_non_normalized_email(db_session: Session) -> None:
    user, profile = make_user()
    user.profile = profile
    profile.nickname = "ana"
    db_session.add(user)  # sin pasar por el repositorio: email con mayúsculas
    with pytest.raises(IntegrityError, match="ck_users_email_normalized"):
        db_session.flush()


@pytest.mark.parametrize("nickname", ["ab", "-abc", "abc-", "Abc", "a_b", "ab c", "ñandú"])
def test_database_rejects_invalid_nickname(db_session: Session, nickname: str) -> None:
    user, profile = make_user(email="x@example.com")
    profile.nickname = nickname
    user.profile = profile
    db_session.add(user)
    with pytest.raises(IntegrityError, match="ck_profiles_nickname_format"):
        db_session.flush()


def test_database_rejects_nickname_longer_than_30(db_session: Session) -> None:
    user, profile = make_user(email="x@example.com")
    profile.nickname = "a" * 31
    user.profile = profile
    db_session.add(user)
    with pytest.raises(DataError):
        db_session.flush()


@pytest.mark.parametrize("nickname", ["abc", "a-b", "a--b", "0x1", "a" * 30])
def test_database_accepts_valid_nickname(db_session: Session, nickname: str) -> None:
    user, profile = make_user(email="x@example.com", nickname=nickname)
    add_user_with_profile(db_session, user, profile)
    assert nickname_exists(db_session, nickname)


def test_database_rejects_unknown_role(db_session: Session) -> None:
    user = add_user_with_profile(db_session, *make_user())
    with pytest.raises(IntegrityError, match="ck_users_role"):
        db_session.execute(text("UPDATE users SET role = 'root' WHERE id = :id"), {"id": user.id})


def test_deleting_user_cascades_to_profile(db_session: Session) -> None:
    user = add_user_with_profile(db_session, *make_user())
    db_session.execute(delete(User).where(User.id == user.id))
    db_session.expunge_all()
    assert db_session.scalar(select(Profile).where(Profile.user_id == user.id)) is None
