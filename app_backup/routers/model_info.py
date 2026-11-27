import json

from fastapi import APIRouter, HTTPException

from app.config import VIOLATION_CLASS_MAP, get_settings
from app.ml.detector import detector

router = APIRouter(prefix="/model", tags=["model"])
CLASS_AP50 = {"Hardhat": 0.75, "Person": 0.65, "Ladder": 0.53, "Mask": 0.41, "NO-Hardhat": 0.37, "Safety Cone": 0.30, "Safety Vest": 0.25, "NO-Safety Vest": 0.08, "NO-Mask": 0.01, "Fall-Detected": 0.0, "Gloves": 0.0, "Goggles": 0.0, "NO-Gloves": 0.0, "NO-Goggles": 0.0}


@router.get("/info")
def model_info() -> dict:
    settings = get_settings()
    if not settings.model_meta_file.is_file():
        raise HTTPException(status_code=503, detail=f"Model metadata unavailable at {settings.model_meta_file}")
    metadata = json.loads(settings.model_meta_file.read_text(encoding="utf-8"))
    metrics_path = settings.model_meta_file.with_name("metrics.json")
    metrics = json.loads(metrics_path.read_text(encoding="utf-8")) if metrics_path.is_file() else metadata.get("metrics", {})
    return {"model_name": metadata.get("model_name"), "dataset": metadata.get("dataset"), "epochs": metadata.get("epochs"), "metrics": metrics, "per_class_ap50": CLASS_AP50, "violation_classes": {name: cfg for name, cfg in VIOLATION_CLASS_MAP.items()}, "loaded": detector.model is not None}
