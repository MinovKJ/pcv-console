"""
PCV Console – FastAPI application entrypoint.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.mysql import create_all_tables
from app.db.mongo import close_mongo

from app.auth.router import router as auth_router
from app.users.router import router as users_router
from app.cases.router import router as cases_router
from app.alerts.router import router as alerts_router
from app.triage.router import router as triage_router
from app.dashboard.router import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create MySQL tables (dev mode; use Alembic in production)
    await create_all_tables()
    yield
    # Shutdown: close Mongo connection pool
    await close_mongo()


app = FastAPI(
    title="PCV Console",
    description=(
        "Alert triage and case management backend powered by the "
        "Provenance Claim Verifier (PCV). "
        "Runs LLM-assisted triage, verifies claims against the provenance graph, "
        "and stores everything for analyst review."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(cases_router)
app.include_router(alerts_router)
app.include_router(triage_router)
app.include_router(dashboard_router)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "service": "pcv-console"}

