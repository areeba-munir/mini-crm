from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.dashboard import get_dashboard_summary
from app.db.session import get_db
from app.schemas.dashboard import DashboardSummary


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get(
    "/summary",
    response_model=DashboardSummary,
)
def read_dashboard_summary(
    db: Annotated[Session, Depends(get_db)],
) -> DashboardSummary:
    return get_dashboard_summary(db)