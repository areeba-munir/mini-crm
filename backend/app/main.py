from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.core.activity  # noqa: F401

from app.api.routes import (
    activities,
    auth,
    companies,
    contacts,
    dashboard,
    leads,
    meetings,
    notes,
    search,
    tasks,
    users,
)
from app.core.config import get_settings


app = FastAPI(
    title="Mini CRM API",
    version="0.2.0",
)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth.router,
    prefix="/api/v1",
)
app.include_router(
    users.router,
    prefix="/api/v1",
)
app.include_router(
    companies.router,
    prefix="/api/v1",
)
app.include_router(
    contacts.router,
    prefix="/api/v1",
)
app.include_router(
    leads.router,
    prefix="/api/v1",
)
app.include_router(
    tasks.router,
    prefix="/api/v1",
)
app.include_router(
    meetings.router,
    prefix="/api/v1",
)
app.include_router(
    notes.router,
    prefix="/api/v1",
)
app.include_router(
    search.router,
    prefix="/api/v1",
)
app.include_router(
    dashboard.router,
    prefix="/api/v1",
)
app.include_router(
    activities.router,
    prefix="/api/v1",
)

@app.get(
    "/health",
    tags=["Health"],
)
def health_check() -> dict[str, str]:
    return {"status": "ok"}