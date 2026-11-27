from datetime import datetime, time, timezone

from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError

from app.db import get_violations_collection
from app.config import VIOLATION_CLASS_MAP
from app.models import AnalyticsSummary, HourlyCount, ViolationTypeCount


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/hourly", response_model=list[HourlyCount])
def hourly_analytics(start_date: datetime | None = None, end_date: datetime | None = None) -> list[HourlyCount]:
    match = {}
    if start_date or end_date:
        match["timestamp"] = {}
        if start_date: match["timestamp"]["$gte"] = start_date
        if end_date: match["timestamp"]["$lte"] = end_date
    pipeline = [
        *([{"$match": match}] if match else []),
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
    severity = {entry["label"]: entry["severity"] for entry in VIOLATION_CLASS_MAP.values()}
    return [ViolationTypeCount(violation_type=name, count=count, severity=severity.get(name, "Unknown")) for name, count in counts.items()]


@router.get("/summary", response_model=AnalyticsSummary)
def summary() -> AnalyticsSummary:
    try:
        collection = get_violations_collection()
        now = datetime.now(timezone.utc)
        midnight = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)
        total = collection.count_documents({})
        unresolved = collection.count_documents({"status": "Unresolved"})
        today = collection.count_documents({"timestamp": {"$gte": midnight}})
        top = next(iter(collection.aggregate([{"$group": {"_id": "$violation_type", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": 1}])), None)
        avg = collection.database["frame_stats"].aggregate([{"$group": {"_id": None, "value": {"$avg": "$compliance_score"}}}])
        avg_item = next(iter(avg), None)
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}") from exc
    return AnalyticsSummary(total_violations=total, unresolved_count=unresolved, today_count=today, average_compliance_score=avg_item.get("value") if avg_item else None, top_violation_type=top["_id"] if top else None)
