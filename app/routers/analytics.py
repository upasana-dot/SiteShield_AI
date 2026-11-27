
from datetime import datetime, time, timezone

from fastapi import APIRouter, HTTPException
from pymongo.errors import PyMongoError

from app.db import (
    get_violations_collection,
    get_frame_stats_collection,
)
from app.config import VIOLATION_CLASS_MAP
from app.models import (
    AnalyticsSummary,
    HourlyCount,
    ViolationTypeCount,
)


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/hourly", response_model=list[HourlyCount])
def hourly_analytics(
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> list[HourlyCount]:

    match = {}

    if start_date or end_date:
        match["timestamp"] = {}

        if start_date:
            match["timestamp"]["$gte"] = start_date

        if end_date:
            match["timestamp"]["$lte"] = end_date

    pipeline = [
        *([{"$match": match}] if match else []),
        {
            "$group": {
                "_id": {
                    "$dateTrunc": {
                        "date": "$timestamp",
                        "unit": "hour",
                    }
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
    ]

    try:
        collection = get_violations_collection()
        results = list(collection.aggregate(pipeline))

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"MongoDB error: {exc}",
        ) from exc

    return [
        HourlyCount(hour=item["_id"], count=item["count"])
        for item in results
    ]


@router.get("/by-type", response_model=list[ViolationTypeCount])
def violations_by_type() -> list[ViolationTypeCount]:

    pipeline = [
        {
            "$group": {
                "_id": "$violation_type",
                "count": {"$sum": 1},
            }
        }
    ]

    try:
        collection = get_violations_collection()
        results = list(collection.aggregate(pipeline))

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"MongoDB error: {exc}",
        ) from exc

    severity = {
        entry["label"]: entry["severity"]
        for entry in VIOLATION_CLASS_MAP.values()
    }

    return [
        ViolationTypeCount(
            violation_type=item["_id"],
            count=item["count"],
            severity=severity.get(item["_id"], "Unknown"),
        )
        for item in results
    ]


@router.get("/summary", response_model=AnalyticsSummary)
def summary() -> AnalyticsSummary:

    try:
        violations_collection = get_violations_collection()
        frame_stats_collection = get_frame_stats_collection()

        now = datetime.now(timezone.utc)
        midnight = datetime.combine(
            now.date(),
            time.min,
            tzinfo=timezone.utc,
        )

        total = violations_collection.count_documents({})

        unresolved = violations_collection.count_documents({
            "status": "Unresolved"
        })

        today = violations_collection.count_documents({
            "timestamp": {"$gte": midnight}
        })

        top_pipeline = [
            {
                "$group": {
                    "_id": "$violation_type",
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": 1},
        ]

        top = next(
            iter(violations_collection.aggregate(top_pipeline)),
            None,
        )

        avg_pipeline = [
            {
                "$group": {
                    "_id": None,
                    "value": {"$avg": "$compliance_score"},
                }
            }
        ]

        avg = next(
            iter(frame_stats_collection.aggregate(avg_pipeline)),
            None,
        )

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"MongoDB error: {exc}",
        ) from exc

    return AnalyticsSummary(
        total_violations=total,
        unresolved_count=unresolved,
        today_count=today,
        average_compliance_score=(
            avg.get("value") if avg else None
        ),
        top_violation_type=(
            top["_id"] if top else None
        ),
    )
