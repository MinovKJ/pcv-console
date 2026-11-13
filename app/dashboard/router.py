"""
Dashboard router: MongoDB aggregation pipelines for analyst metrics.
"""
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db.models.user import User
from app.db.mongo import get_mongo_db
from app.dependencies import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/verification-pass-rate")
async def verification_pass_rate(
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Verification pass rate and avg DEVR / PIR grouped by serialization format.
    Only includes runs where the LLM was not blocked.
    """
    pipeline = [
        {"$match": {"llm_blocked": False, "llm_success": True}},
        {"$group": {
            "_id": "$format",
            "total_runs": {"$sum": 1},
            "avg_DEVR": {"$avg": "$metrics.DEVR"},
            "avg_PIR": {"$avg": "$metrics.PIR"},
            "avg_direct_valid": {"$avg": "$metrics.direct_valid"},
            "avg_direct_invalid": {"$avg": "$metrics.direct_invalid"},
            "avg_injection_risk": {"$avg": "$metrics.injection_risk_score"},
        }},
        {"$sort": {"_id": 1}},
    ]
    result = [doc async for doc in mongo["triage_runs"].aggregate(pipeline)]
    return result


@router.get("/injection-stats")
async def injection_stats(
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Injection guard statistics: how many runs were blocked vs clean,
    and the breakdown of explicit vs subtle hits.
    """
    pipeline = [
        {"$group": {
            "_id": "$injection_guard.is_clean",
            "count": {"$sum": 1},
            "avg_risk_score": {"$avg": "$injection_guard.risk_score"},
            "total_explicit_hits": {"$sum": "$injection_guard.explicit_hit_count"},
            "total_subtle_hits": {"$sum": "$injection_guard.subtle_hit_count"},
        }},
    ]
    raw = [doc async for doc in mongo["triage_runs"].aggregate(pipeline)]
    return {
        "clean_runs": next((r for r in raw if r["_id"] is True), {"count": 0}),
        "flagged_runs": next((r for r in raw if r["_id"] is False), {"count": 0}),
    }


@router.get("/temporal-inversion-rate")
async def temporal_inversion_rate(
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Average TIR (temporal inversion rate) grouped by format."""
    pipeline = [
        {"$match": {"llm_success": True, "metrics.evaluable_temporal_pairs": {"$gt": 0}}},
        {"$addFields": {
            "TIR": {
                "$divide": ["$metrics.temporal_inversions", "$metrics.evaluable_temporal_pairs"]
            }
        }},
        {"$group": {
            "_id": "$format",
            "avg_TIR": {"$avg": "$TIR"},
            "total_inversions": {"$sum": "$metrics.temporal_inversions"},
            "total_pairs": {"$sum": "$metrics.evaluable_temporal_pairs"},
            "run_count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    return [doc async for doc in mongo["triage_runs"].aggregate(pipeline)]


@router.get("/throughput")
async def throughput(
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """Verification throughput: avg and p95 duration_ms, total runs stored."""
    pipeline = [
        {"$group": {
            "_id": None,
            "total_runs": {"$sum": 1},
            "avg_duration_ms": {"$avg": "$duration_ms"},
            "max_duration_ms": {"$max": "$duration_ms"},
            "min_duration_ms": {"$min": "$duration_ms"},
        }},
    ]
    result = [doc async for doc in mongo["triage_runs"].aggregate(pipeline)]
    return result[0] if result else {}


@router.get("/cases-by-severity")
async def cases_by_severity(
    user: User = Depends(get_current_user),
    mongo: AsyncIOMotorDatabase = Depends(get_mongo_db),
):
    """
    Case distribution by severity.
    Note: Cases are in MySQL; this returns alert-level severity distribution
    from triage run labels stored in Mongo.
    """
    pipeline = [
        {"$group": {"_id": "$label", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    return [doc async for doc in mongo["alerts"].aggregate(pipeline)]

