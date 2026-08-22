from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.crud.search import search_crm
from app.db.session import get_db
from app.schemas.search import SearchResults


router = APIRouter(
    prefix="/search",
    tags=["Search"],
    dependencies=[
        Depends(get_current_user),
    ],
)


@router.get(
    "",
    response_model=SearchResults,
)
def search_records(
    db: Annotated[Session, Depends(get_db)],
    q: str = Query(
        min_length=2,
        max_length=100,
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
) -> SearchResults:
    normalized_query = q.strip()

    if len(normalized_query) < 2:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_CONTENT
            ),
            detail=(
                "Search query must contain "
                "at least 2 characters"
            ),
        )

    companies, contacts, leads = search_crm(
        db,
        query=normalized_query,
        limit=limit,
    )

    return SearchResults(
        companies=companies,
        contacts=contacts,
        leads=leads,
    )