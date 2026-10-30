import json
from pathlib import Path
from threading import Lock

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import VIOLATION_CLASS_MAP, get_settings
from app.models import Detection


class PPEViolationDetector:
    """A single CPU-resident YOLO model shared by all requests."""

    def __init__(self) -> None:
        self.model: YOLO | None = None
        self._lock = Lock()

    def load(self, model_path: Path, metadata_path: Path) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(f"YOLO weights not found at '{model_path}'. Set MODEL_PATH to the trained best.pt file.")
        if not metadata_path.is_file():
            raise FileNotFoundError(f"Model metadata not found at '{metadata_path}'. Set MODEL_META_PATH.")
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        expected = {str(k): str(v) for k, v in metadata.get("classes", {}).items()}
        loaded = YOLO(str(model_path))
        actual = {str(k): str(v) for k, v in loaded.names.items()} if isinstance(loaded.names, dict) else {str(i): str(v) for i, v in enumerate(loaded.names)}
        if expected != actual:
            raise ValueError(f"Model classes in {model_path} do not match {metadata_path}. Metadata={expected}; model={actual}")
        self.metadata = metadata
        self.model = loaded

    def predict(self, image_bytes: bytes) -> tuple[list[Detection], np.ndarray, tuple[int, int], float]:
        if self.model is None:
            raise RuntimeError("YOLO model is not loaded.")
        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("The uploaded file is not a valid image.")

        # Ultralytics/PyTorch inference is guarded so one low-spec CPU is not overloaded.
        original_height, original_width = image.shape[:2]
        settings = get_settings()
        if original_width > settings.max_frame_width:
            scale = settings.max_frame_width / original_width
            image = cv2.resize(image, (settings.max_frame_width, max(1, round(original_height * scale))), interpolation=cv2.INTER_AREA)
        height, width = image.shape[:2]
        import time
        started = time.perf_counter()
        with self._lock:
            result = self.model.predict(source=image, device="cpu", imgsz=settings.img_size, conf=settings.base_conf, verbose=False)[0]
        inference_ms = round((time.perf_counter() - started) * 1000, 2)

        names = result.names
        detections: list[Detection] = []
        annotated = image.copy()
        if result.boxes is None:
            return detections, annotated, (width, height), inference_ms

        for box in result.boxes:
            class_id = int(box.cls[0].item())
            class_name = str(names[class_id])
            confidence = round(float(box.conf[0].item()), 4)
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0].tolist())
            config = VIOLATION_CLASS_MAP.get(class_name)
            is_violation = bool(config and config["enabled"] and confidence >= config["min_conf"])
            color = "red" if is_violation else "green"
            detections.append(
                Detection(
                    class_name=class_name,
                    confidence_score=confidence,
                    bbox=[x1, y1, x2, y2],
                    is_violation=is_violation,
                    color=color,
                )
            )
            draw_color = (0, 0, 255) if is_violation else (0, 180, 0)
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), draw_color, 2)
            cv2.putText(annotated, f"{class_name} {confidence:.2f}", (int(x1), max(18, int(y1) - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, draw_color, 2)
        return detections, annotated, (width, height), inference_ms


detector = PPEViolationDetector()
