import base64
from datetime import datetime, timezone
from uuid import uuid4

import cv2
from fastapi import APIRouter, HTTPException, Request, status
from pymongo.errors import PyMongoError
from starlette.datastructures import UploadFile

from app.config import get_settings
from app.db import get_violations_collection
from app.ml.detector import VIOLATION_CLASS_MAP, detector
from app.models import PredictionResponse, Violation
from app.ws.manager import manager


router = APIRouter(tags=["prediction"])


def serialize_violation(document: dict) -> Violation:
    document["_id"] = str(document["_id"])
    return Violation.model_validate(document)


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: Request,
) -> PredictionResponse:
    try:
        content_type = request.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            payload = await request.json()
            frame_base64 = payload.get("frame_base64")
            site_location = payload.get("site_location", "Unknown")
            file = None
        else:
            form = await request.form()
            file = form.get("file")
            frame_base64 = form.get("frame_base64")
            site_location = str(form.get("site_location", "Unknown"))
        if file is not None and isinstance(file, UploadFile):
            image_bytes = await file.read()
        elif frame_base64:
            encoded = frame_base64.split(",", 1)[-1]
            image_bytes = base64.b64decode(encoded, validate=True)
        else:
            raise ValueError("Provide an image 'file' or 'frame_base64' value.")
        if not image_bytes:
            raise ValueError("Image is empty.")
        detections, annotated = detector.predict(image_bytes)
    except (ValueError, base64.binascii.Error) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    settings = get_settings()
    settings.annotations_path.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}_{uuid4().hex}.jpg"
    annotation_file = settings.annotations_path / filename
    if not cv2.imwrite(str(annotation_file), annotated):
        raise HTTPException(status_code=500, detail="Could not save annotated image.")
    image_url = f"/static/annotations/{filename}"

    violations: list[Violation] = []
    try:
        collection = get_violations_collection()
        for detection in detections:
            if not detection.is_violation:
                continue
            document = {
                "timestamp": datetime.now(timezone.utc),
                "site_location": site_location,
                "violation_type": VIOLATION_CLASS_MAP[detection.class_name],
                "confidence_score": detection.confidence_score,
                "image_url": image_url,
                "status": "Unresolved",
            }
            insert = collection.insert_one(document)
            document["_id"] = insert.inserted_id
            violation = serialize_violation(document)
            violations.append(violation)
            await manager.broadcast({"event": "new_violation", "violation": violation.model_dump(by_alias=True, mode="json")})
    except PyMongoError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"MongoDB error: {exc}") from exc

    return PredictionResponse(detections=detections, violations=violations, annotated_image_url=image_url)
