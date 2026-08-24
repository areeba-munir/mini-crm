from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import (
    OAuth2PasswordRequestForm,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import (
    create_access_token,
    verify_password,
)
from app.crud.user import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    change_user_password as change_user_password_record,
    create_user,
    get_user_by_email,
    update_user as update_user_record,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import (
    UserCreate,
    UserPasswordChange,
    UserRead,
    UserUpdate,
)


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


@router.patch(
    "/me",
    response_model=UserRead,
)
def update_current_user(
    user_data: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    if user_data.email is not None:
        normalized_email = str(user_data.email)

        if normalized_email != current_user.email:
            existing_user = get_user_by_email(
                db,
                normalized_email,
            )

            if (
                existing_user is not None
                and existing_user.id
                != current_user.id
            ):
                raise HTTPException(
                    status_code=(
                        status.HTTP_409_CONFLICT
                    ),
                    detail=(
                        "Email is already registered"
                    ),
                )

    try:
        return update_user_record(
            db,
            current_user,
            user_data,
        )
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        ) from error


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
)
def change_current_user_password(
    password_data: UserPasswordChange,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> None:
    current_password = (
        password_data.current_password.get_secret_value()
    )

    if not verify_password(
        current_password,
        current_user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    change_user_password_record(
        db,
        current_user,
        password_data.new_password.get_secret_value(),
    )