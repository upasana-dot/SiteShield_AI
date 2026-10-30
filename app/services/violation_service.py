from datetime import datetime, timezone

from fastapi import HTTPException
from pymongo.errors import PyMongoError

from app.config import VIOLATION_CLASS_MAP, get_settings
from app.db import get_violations_collection
from app.ml.tracker import cooldown
from app.models import Detection, Violation
from app.services.storage import save_frame
from app.ws.manager import manager


async def log_new_violations(detections: list[Detection], tracked: list[tuple[Detection, str]], camera_id: str, site_location: str, annotated, model_version: str) -> list[Violation]:
    settings = get_settings()
    pending = []
    for detection, track_id in tracked:
        config = VIOLATION_CLASS_MAP[detection.class_name]
        label = config["label"]
        if cooldown.allow(camera_id, track_id, label, settings.cooldown_seconds):
            pending.append((detection, track_id, config))
    if not pending:
        return []
    image_url = save_frame(annotated, settings.frames_path)
    collection = get_violations_collection()
    output = []
    try:
        for detection, track_id, config in pending:
            document = {
                "timestamp": datetime.now(timezone.utc), "camera_id": camera_id,
                "site_location": site_location, "violation_type": config["label"],
                "class_name": detection.class_name, "severity": config["severity"],
                "confidence_score": detection.confidence_score, "bbox": detection.bbox,
                "track_id": track_id, "image_url": image_url, "status": "Unresolved",
                "resolved_at": None, "model_version": model_version,
            }
            inserted = collection.insert_one(document)
            document["_id"] = str(inserted.inserted_id)
            violation = Violation.model_validate(document)
            output.append(violation)
            await manager.broadcast({"event": "new_violation", "violation": violation.model_dump(by_alias=True, mode="json")})
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail=f"MongoDB error: {exc}") from exc
    return output
