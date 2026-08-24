from collections.abc import Callable
from typing import Annotated

import jwt
from fastapi import (
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User, UserRole


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


def authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer",
        },
    )


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise ValueError(
                "Token subject is missing"
            )

        user_id = int(subject)
    except (
        jwt.InvalidTokenError,
        ValueError,
    ) as error:
        raise authentication_error() from error

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        raise authentication_error()

    return user


def require_roles(
    *allowed_roles: UserRole,
) -> Callable[..., User]:
    def role_dependency(
        current_user: Annotated[
            User,
            Depends(get_current_user),
        ],
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "You do not have permission "
                    "to perform this action"
                ),
            )

        return current_user

    return role_dependency


get_current_admin = require_roles(
    UserRole.ADMIN,
)

get_current_manager = require_roles(
    UserRole.ADMIN,
    UserRole.MANAGER,
)