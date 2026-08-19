from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings


def test_uses_separate_test_database(
    db_session: Session,
) -> None:
    settings = get_settings()

    database_name = db_session.scalar(
        text("SELECT current_database()")
    )

    assert database_name == settings.db_test_name
    assert database_name != settings.db_name