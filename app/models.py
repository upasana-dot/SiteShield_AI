from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ViolationStatus = Literal["Unresolved", "Resolved"]


class Detection(BaseModel):
    class_name: str
    confidence_score: float
    bbox: list[float]
    is_violation: bool
    color: Literal["red", "green"]


class Violation(BaseModel):
    id: str = Field(alias="_id")
    timestamp: datetime
    camera_id: str
    site_location: str
    violation_type: str
    class_name: str
    severity: str
    confidence_score: float
    bbox: list[float]
    track_id: str
    image_url: str
    status: ViolationStatus
    resolved_at: datetime | None = None
    model_version: str = "unknown"

    model_config = ConfigDict(populate_by_name=True)


class ViolationPage(BaseModel):
    items: list[Violation]
    total: int
    limit: int
    skip: int


class PredictionResponse(BaseModel):
    detections: list[Detection]
    new_violations: list[Violation]
    total_workers: int
    violation_count: int
    compliance_score: float | None
    inference_ms: float
    frame_size: dict[str, int]


class ViolationStatusUpdate(BaseModel):
    status: ViolationStatus


class HourlyCount(BaseModel):
    hour: datetime
    count: int


class ViolationTypeCount(BaseModel):
    violation_type: str
    count: int
    severity: str


class AnalyticsSummary(BaseModel):
    total_violations: int
    unresolved_count: int
    today_count: int
    average_compliance_score: float | None
    top_violation_type: str | None
