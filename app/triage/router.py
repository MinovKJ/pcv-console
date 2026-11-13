"""
Triage router: submit graphs, run pipeline, fetch run history.
"""
from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.models.user import User
from app.db.mongo import get_mongo_db
from app.dependencies import get_current_user
from app.triage.schemas import TriageRequest, TriageRunOut
from app.triage.service import run_triage

router = APIRouter(prefix="/triage", tags=["triage"])


@router.post("/run", response_model=TriageRunOut)
async def triage_run(
    body: TriageRequest,
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Submit a provenance graph for the full PCV triage pipeline."""
    return await run_triage(body, submitted_by=user.id, mongo=mongo)


@router.get("/runs", response_model=list[dict])
async def list_runs(
    alert_id: str | None = Query(None),
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """List triage run summaries with optional filter by alert_id."""
    filt = {}
    if alert_id:
        filt["alert_id"] = alert_id
    cursor = mongo["triage_runs"].find(
        filt,
        {
            "_id": 1, "alert_id": 1, "format": 1, "model": 1,
            "duration_ms": 1, "created_at": 1, "llm_success": 1,
            "llm_blocked": 1, "metrics": 1, "verifier_result.source": 1,
        },
    ).sort("created_at", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]


@router.get("/runs/{run_id}", response_model=dict)
async def get_run(
    run_id: str,
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Get the full detail of a single triage run."""
    doc = await mongo["triage_runs"].find_one({"_id": run_id})
    if not doc:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Run not found")
    return doc
