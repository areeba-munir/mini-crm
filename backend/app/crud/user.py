from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
)


class EmailAlreadyRegisteredError(Exception):
    pass


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    statement = select(User).where(
        User.email == email.lower()
    )

    return db.scalar(statement)


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    user = User(
        full_name=user_data.full_name,
        email=str(user_data.email),
        password_hash=hash_password(
            user_data.password.get_secret_value()
        ),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise EmailAlreadyRegisteredError from error
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user


def update_user(
    db: Session,
    user: User,
    user_data: UserUpdate,
) -> User:
    update_data = user_data.model_dump(
        exclude_unset=True
    )

    if "full_name" in update_data:
        user.full_name = update_data["full_name"]

    if "email" in update_data:
        user.email = str(update_data["email"])

    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise EmailAlreadyRegisteredError from error
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user


def change_user_password(
    db: Session,
    user: User,
    new_password: str,
) -> None:
    user.password_hash = hash_password(new_password)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    user = get_user_by_email(db, email)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user