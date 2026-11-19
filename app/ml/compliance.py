from app.config import VIOLATION_CLASS_MAP
from app.ml.tracker import tracker
from app.models import Detection


def compute_frame(detections: list[Detection], camera_id: str, timeout_seconds: int) -> tuple[int, int, float | None, list[tuple[Detection, str]]]:
    people = [d for d in detections if d.class_name == "Person"]
    candidates = [d for d in detections if d.class_name in VIOLATION_CLASS_MAP and d.is_violation]
    track_boxes: list[list[float]] = []
    matched_people: list[int | None] = []
    for violation in candidates:
        x1, y1, x2, y2 = violation.bbox
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        person_index = next((i for i, p in enumerate(people) if p.bbox[0] <= cx <= p.bbox[2] and p.bbox[1] <= cy <= p.bbox[3]), None)
        person = people[person_index] if person_index is not None else None
        track_boxes.append(person.bbox if person else violation.bbox)
        matched_people.append(person_index)
    tracker.timeout_seconds = timeout_seconds
    ids = tracker.assign(camera_id, track_boxes)
    linked = [(detection, track_id) for detection, track_id in zip(candidates, ids)]
    workers = len(people)
    violating_workers = {person_index for person_index in matched_people if person_index is not None}
    score = (workers - len(violating_workers)) / workers if workers else None
    return workers, len(candidates), score, linked
