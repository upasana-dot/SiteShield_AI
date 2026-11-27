from datetime import datetime, timezone

from fastapi import APIRouter,File,Form, HTTPException,UploadFile
from pymongo.errors import PyMongoError


from app.config import get_settings
from app.db import get_frame_stats_collection
from app.ml.compliance import compute_frame
from app.ml.detector import detector
from app.models import PredictionResponse
from app.services.violation_service import log_new_violations


router = APIRouter(tags=["prediction"])


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    file: UploadFile = File(...),
    camera_id: str = Form("default-camera"),
    site_location: str = Form("Unknown"),
) -> PredictionResponse:
    try:
        image_bytes = await file.read()

        if not image_bytes:
            raise ValueError("Image is empty.")

        detections, annotated, frame_size, inference_ms = detector.predict(image_bytes)

        workers, violation_count, compliance_score, tracked = compute_frame(
            detections,
            camera_id,
            get_settings().track_timeout_seconds,
        )

    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    # Save frame statistics in MongoDB.
    try:
        frame_stats = get_frame_stats_collection()

        frame_stats.insert_one({
            "timestamp": datetime.now(timezone.utc),
            "camera_id": camera_id,
            "total_workers": workers,
            "violation_count": violation_count,
            "compliance_score": compliance_score,
        })

    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"MongoDB unavailable: {exc}",
        ) from exc

    # Log new PPE violations and broadcast alerts.
    violations = await log_new_violations(
        detections,
        tracked,
        camera_id,
        site_location,
        annotated,
        str(getattr(detector, "metadata", {}).get("model_name", "unknown")),
    )

    return PredictionResponse(
        detections=detections,
        new_violations=violations,
        total_workers=workers,
        violation_count=violation_count,
        compliance_score=compliance_score,
        inference_ms=inference_ms,
        frame_size={
            "width": frame_size[0],
            "height": frame_size[1],
        },
    )
