from dataclasses import dataclass
from threading import Lock
from time import time


def iou(a: list[float], b: list[float]) -> float:
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - intersection
    return intersection / union if union else 0.0


@dataclass
class Track:
    track_id: str
    bbox: list[float]
    seen_at: float


class IoUTracker:
    def __init__(self, timeout_seconds: int = 10, threshold: float = 0.25):
        self.timeout_seconds = timeout_seconds
        self.threshold = threshold
        self._tracks: dict[str, list[Track]] = {}
        self._next_id = 1
        self._lock = Lock()

    def assign(self, camera_id: str, boxes: list[list[float]]) -> list[str]:
        now = time()
        with self._lock:
            tracks = [t for t in self._tracks.get(camera_id, []) if now - t.seen_at <= self.timeout_seconds]
            assignments: list[str] = []
            for box in boxes:
                options = [(iou(box, t.bbox), t) for t in tracks]
                score, match = max(options, key=lambda pair: pair[0], default=(0.0, None))
                if match is None or score < self.threshold:
                    match = Track(str(self._next_id), box, now)
                    self._next_id += 1
                    tracks.append(match)
                else:
                    match.bbox = box
                    match.seen_at = now
                assignments.append(match.track_id)
            self._tracks[camera_id] = tracks
            return assignments


tracker = IoUTracker()


class Cooldown:
    def __init__(self):
        self._last: dict[tuple[str, str, str], float] = {}
        self._lock = Lock()

    def allow(self, camera_id: str, track_id: str, violation_type: str, seconds: int) -> bool:
        now = time()
        key = (camera_id, track_id, violation_type)
        with self._lock:
            if now - self._last.get(key, 0) < seconds:
                return False
            self._last[key] = now
            return True


cooldown = Cooldown()
