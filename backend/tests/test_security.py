import jwt
import pytest

from app.core.security import (
    decode_access_token,
    verify_password,
)
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    plain_password = "StrongPass123!"

    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert verify_password(
        plain_password,
        hashed_password,
    )
    assert not verify_password(
        "WrongPassword!",
        hashed_password,
    )


def test_create_and_decode_access_token() -> None:
    token = create_access_token("123")

    payload = decode_access_token(token)

    assert payload["sub"] == "123"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_access_token_rejects_invalid_token() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-valid-token")