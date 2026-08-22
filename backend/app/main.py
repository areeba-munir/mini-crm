from app.api.routes import auth, companies, contacts, leads, tasks, meetings, notes, search
from fastapi import FastAPI

app = FastAPI(
    title="Mini CRM API",
    version="0.1.0",
)
app.include_router(
    auth.router,
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
@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}