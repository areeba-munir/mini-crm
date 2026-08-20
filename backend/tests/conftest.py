from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import app.models  # noqa: F401
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


settings = get_settings()

if (
    settings.db_test_name == settings.db_name
    or not settings.db_test_name.endswith("_test")
):
    raise RuntimeError(
        "Tests must use a separate database whose name ends with '_test'."
    )


test_engine = create_engine(
    settings.test_database_url,
    pool_pre_ping=True,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> Generator[None, None, None]:
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = test_engine.connect()
    transaction = connection.begin()

    session = Session(
        bind=connection,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(
    db_session: Session,
) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def authenticated_client(
    client: TestClient,
) -> TestClient:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Company Test User",
            "email": "company-tests@example.com",
            "password": "StrongPass123!",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "company-tests@example.com",
            "password": "StrongPass123!",
        },
    )

    assert login_response.status_code == 200

    access_token = login_response.json()["access_token"]

    client.headers["Authorization"] = (
        f"Bearer {access_token}"
    )

    return client
