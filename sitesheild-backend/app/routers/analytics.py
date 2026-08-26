from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError

from app.db import get_violations_collection
from app.ml.detector import VIOLATION_CLASS_MAP
from app.models import HourlyCount, ViolationTypeCount


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/hourly", response_model=list[HourlyCount])
def hourly_analytics() -> list[HourlyCount]:
    pipeline = [
        {"$group": {"_id": {"$dateTrunc": {"date": "$timestamp", "unit": "hour"}}, "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    try:
        results = list(get_violations_collection().aggregate(pipeline))
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}") from exc
    return [HourlyCount(hour=item["_id"], count=item["count"]) for item in results]


@router.get("/by-type", response_model=list[ViolationTypeCount])
def violations_by_type() -> list[ViolationTypeCount]:
    try:
        counts = {item["_id"]: item["count"] for item in get_violations_collection().aggregate([{"$group": {"_id": "$violation_type", "count": {"$sum": 1}}}])}
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}") from exc
    return [ViolationTypeCount(violation_type=name, count=counts.get(name, 0)) for name in VIOLATION_CLASS_MAP.values()]
