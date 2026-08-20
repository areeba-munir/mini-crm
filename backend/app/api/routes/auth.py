from typing import Annotated
from app.api.dependencies import get_current_user

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud.user import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    create_user,
    get_user_by_email,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserRead


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    existing_user = get_user_by_email(
        db,
        str(user_data.email),
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    try:
        return create_user(db, user_data)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from error


@router.post(
    "/login",
    response_model=Token,
)
def login_user(
    form_data: Annotated[
        OAuth2PasswordRequestForm,
        Depends(),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    return Token(
        access_token=create_access_token(str(user.id))
    )
@router.get(
    "/me",
    response_model=UserRead,
)
def read_current_user(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    return current_user