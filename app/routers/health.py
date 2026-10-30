from fastapi import APIRouter

from app.db import is_mongo_connected
from app.ml.detector import detector

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    return {"api": "ok", "model_loaded": detector.model is not None, "db_connected": is_mongo_connected()}
