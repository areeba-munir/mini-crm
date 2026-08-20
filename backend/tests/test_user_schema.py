import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserRead


def test_user_create_normalizes_name_and_email() -> None:
    user = UserCreate(
        full_name="  Alex Morgan  ",
        email="ALEX@EXAMPLE.COM",
        password="StrongPass123!",
    )

    assert user.full_name == "Alex Morgan"
    assert str(user.email) == "alex@example.com"


def test_user_create_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            full_name="Alex Morgan",
            email="not-an-email",
            password="StrongPass123!",
        )


def test_user_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            full_name="Alex Morgan",
            email="alex@example.com",
            password="short",
        )


def test_user_read_never_contains_password_fields() -> None:
    assert "password" not in UserRead.model_fields
    assert "password_hash" not in UserRead.model_fields