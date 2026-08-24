from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
)
from app.models.user import User, UserRole
from app.schemas.user import (
    UserAdminUpdate,
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


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return db.get(User, user_id)


def list_users(
    db: Session,
) -> list[User]:
    statement = select(User).order_by(User.id)

    return list(db.scalars(statement))


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    existing_user_count = db.scalar(
        select(func.count(User.id))
    ) or 0

    role = (
        UserRole.ADMIN
        if existing_user_count == 0
        else UserRole.MEMBER
    )

    user = User(
        full_name=user_data.full_name,
        email=str(user_data.email),
        password_hash=hash_password(
            user_data.password.get_secret_value()
        ),
        role=role,
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


def update_user_administration(
    db: Session,
    user: User,
    user_data: UserAdminUpdate,
) -> User:
    update_data = user_data.model_dump(
        exclude_unset=True
    )

    if "role" in update_data:
        user.role = update_data["role"]

    if "is_active" in update_data:
        user.is_active = update_data["is_active"]

    try:
        db.commit()
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