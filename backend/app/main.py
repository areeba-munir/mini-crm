from app.api.routes import auth, companies, contacts
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


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}