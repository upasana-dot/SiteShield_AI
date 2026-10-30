from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pymongo.errors import PyMongoError
from starlette.datastructures import UploadFile

from app.config import get_settings
from app.db import get_violations_collection
from app.ml.compliance import compute_frame
from app.ml.detector import detector
from app.models import PredictionResponse
from app.services.violation_service import log_new_violations


router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
async def predict(request: Request) -> PredictionResponse:
    try:
        form = await request.form()
        file = form.get("file")
        camera_id = str(form.get("camera_id", "default-camera"))
        site_location = str(form.get("site_location", "Unknown"))
        if not isinstance(file, UploadFile):
            raise ValueError("Provide an image in the multipart 'file' field.")
        image_bytes = await file.read()
        if not image_bytes:
            raise ValueError("Image is empty.")
        detections, annotated, frame_size, inference_ms = detector.predict(image_bytes)
        workers, violation_count, compliance_score, tracked = compute_frame(detections, camera_id, get_settings().track_timeout_seconds)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    try:
        collection = get_violations_collection()
        collection.database.client.admin.command("ping")
        collection.database["frame_stats"].insert_one({"timestamp": datetime.now(timezone.utc), "camera_id": camera_id, "total_workers": workers, "violation_count": violation_count, "compliance_score": compliance_score})
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB unavailable: {exc}") from exc

    violations = await log_new_violations(detections, tracked, camera_id, site_location, annotated, str(getattr(detector, "metadata", {}).get("model_name", "unknown")))

    return PredictionResponse(detections=detections, new_violations=violations, total_workers=workers, violation_count=violation_count, compliance_score=compliance_score, inference_ms=inference_ms, frame_size={"width": frame_size[0], "height": frame_size[1]})
