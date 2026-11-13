"""
Alerts router: store and retrieve raw alert documents from MongoDB.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
import uuid
from datetime import datetime, timezone

from app.db.models.user import User
from app.db.mongo import get_mongo_db
from app.dependencies import get_current_user
from app.alerts.schemas import AlertOut

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[dict])
async def list_alerts(
    skip: int = 0,
    limit: int = 50,
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    cursor = mongo["alerts"].find(
        {},
        {"_id": 1, "label": 1, "submitted_by": 1, "submitted_at": 1}
    ).sort("submitted_at", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]


@router.get("/{alert_id}", response_model=dict)
async def get_alert(
    alert_id: str,
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    doc = await mongo["alerts"].find_one({"_id": alert_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Alert not found")
    return doc
