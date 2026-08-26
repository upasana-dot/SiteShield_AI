from pathlib import Path
from threading import Lock

import cv2
import numpy as np
from ultralytics import YOLO

from app.models import BoundingBox, Detection


VIOLATION_CLASS_MAP = {
    "NO-Hardhat": "No Hardhat",
    "NO-Safety Vest": "No Safety Vest",
    "NO-Gloves": "No Gloves",
    "NO-Goggles": "No Goggles",
    "NO-Mask": "No Mask",
    "Fall-Detected": "Fall Detected",
}


class PPEViolationDetector:
    """A single CPU-resident YOLO model shared by all requests."""

    def __init__(self) -> None:
        self.model: YOLO | None = None
        self._lock = Lock()

    def load(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(
                f"YOLO weights not found at '{model_path}'. Copy Colab's best.pt there or set MODEL_PATH."
            )
        self.model = YOLO(str(model_path))

    def predict(self, image_bytes: bytes) -> tuple[list[Detection], np.ndarray]:
        if self.model is None:
            raise RuntimeError("YOLO model is not loaded.")
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("The uploaded file is not a valid image.")

        # Ultralytics/PyTorch inference is guarded so one low-spec CPU is not overloaded.
        with self._lock:
            result = self.model.predict(source=image, device="cpu", verbose=False)[0]

        names = result.names
        detections: list[Detection] = []
        annotated = image.copy()
        if result.boxes is None:
            return detections, annotated

        for box in result.boxes:
            class_id = int(box.cls[0].item())
            class_name = str(names[class_id])
            confidence = round(float(box.conf[0].item()), 4)
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
            is_violation = class_name in VIOLATION_CLASS_MAP
            color = "red" if is_violation else "green"
            detections.append(
                Detection(
                    class_name=class_name,
                    confidence_score=confidence,
                    bounding_box=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    is_violation=is_violation,
                    color=color,
                )
            )
            draw_color = (0, 0, 255) if is_violation else (0, 180, 0)
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), draw_color, 2)
            cv2.putText(annotated, f"{class_name} {confidence:.2f}", (int(x1), max(18, int(y1) - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, draw_color, 2)
        return detections, annotated


detector = PPEViolationDetector()
