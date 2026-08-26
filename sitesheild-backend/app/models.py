from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ViolationStatus = Literal["Unresolved", "Resolved"]


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Detection(BaseModel):
    class_name: str
    confidence_score: float
    bounding_box: BoundingBox
    is_violation: bool
    color: Literal["red", "green"]


class Violation(BaseModel):
    id: str = Field(alias="_id")
    timestamp: datetime
    site_location: str
    violation_type: str
    confidence_score: float
    image_url: str
    status: ViolationStatus

    model_config = ConfigDict(populate_by_name=True)


class ViolationPage(BaseModel):
    items: list[Violation]
    total: int
    limit: int
    skip: int


class PredictionResponse(BaseModel):
    detections: list[Detection]
    violations: list[Violation]
    annotated_image_url: str


class ViolationStatusUpdate(BaseModel):
    status: ViolationStatus


class HourlyCount(BaseModel):
    hour: datetime
    count: int


class ViolationTypeCount(BaseModel):
    violation_type: str
    count: int
