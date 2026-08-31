from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_admin
from app.crud.user import (
    get_user_by_id,
    list_users as list_user_records,
    update_user_administration,
)
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    UserAdminUpdate,
    UserRead,
)


router = APIRouter(
    prefix="/users",
    tags=["User Management"],
)


@router.get(
    "",
    response_model=list[UserRead],
)
def read_users(
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        User,
        Depends(get_current_admin),
    ],
) -> list[User]:
    del current_admin

    return list_user_records(db)


@router.patch(
    "/{user_id}",
    response_model=UserRead,
)
def update_user_administration_record(
    user_id: int,
    user_data: UserAdminUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_admin: Annotated[
        User,
        Depends(get_current_admin),
    ],
) -> User:
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_admin.id:
        if (
            user_data.role is not None
            and user_data.role
            != UserRole.ADMIN
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "You cannot remove your own "
                    "administrator role"
                ),
            )

        if user_data.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "You cannot deactivate your "
                    "own account"
                ),
            )

    return update_user_administration(
        db,
        user,
        user_data,
    )
