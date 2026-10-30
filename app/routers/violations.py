from datetime import datetime, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from app.db import get_violations_collection
from app.models import Violation, ViolationPage, ViolationStatus, ViolationStatusUpdate


router = APIRouter(prefix="/violations", tags=["violations"])


def as_violation(document: dict) -> Violation:
    document["_id"] = str(document["_id"])
    return Violation.model_validate(document)


@router.get("", response_model=ViolationPage)
def list_violations(
    status: ViolationStatus | None = None,
    violation_type: str | None = None,
    severity: str | None = None,
    camera_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    skip: int = Query(default=0, ge=0),
) -> ViolationPage:
    query: dict = {}
    if status:
        query["status"] = status
    if violation_type:
        query["violation_type"] = violation_type
    if severity:
        query["severity"] = severity
    if camera_id:
        query["camera_id"] = camera_id
    if start_date or end_date:
        query["timestamp"] = {}
        if start_date:
            query["timestamp"]["$gte"] = start_date
        if end_date:
            query["timestamp"]["$lte"] = end_date
    try:
        collection = get_violations_collection()
        total = collection.count_documents(query)
        documents = list(collection.find(query).sort("timestamp", -1).skip(skip).limit(limit))
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}") from exc
    return ViolationPage(items=[as_violation(doc) for doc in documents], total=total, limit=limit, skip=skip)


@router.patch("/{violation_id}", response_model=Violation)
def update_violation_status(violation_id: str, payload: ViolationStatusUpdate) -> Violation:
    if not ObjectId.is_valid(violation_id):
        raise HTTPException(status_code=400, detail="Invalid violation id.")
    try:
        update = {"status": payload.status, "resolved_at": datetime.now(timezone.utc) if payload.status == "Resolved" else None}
        document = get_violations_collection().find_one_and_update(
            {"_id": ObjectId(violation_id)}, {"$set": update}, return_document=True
        )
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}") from exc
    if document is None:
        raise HTTPException(status_code=404, detail="Violation not found.")
    return as_violation(document)


@router.get("/{violation_id}", response_model=Violation)
def get_violation(violation_id: str) -> Violation:
    if not ObjectId.is_valid(violation_id):
        raise HTTPException(status_code=400, detail="Invalid violation id.")
    try:
        document = get_violations_collection().find_one({"_id": ObjectId(violation_id)})
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}") from exc
    if document is None:
        raise HTTPException(status_code=404, detail="Violation not found.")
    return as_violation(document)
