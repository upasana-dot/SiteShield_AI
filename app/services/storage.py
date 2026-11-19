from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import cv2
import numpy as np


def save_frame(image: np.ndarray, directory: Path) -> str:
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{datetime.now(timezone.utc):%Y%m%dT%H%M%S}_{uuid4().hex}.jpg"
    if not cv2.imwrite(str(directory / filename), image):
        raise OSError("Could not save annotated violation frame.")
    return f"/storage/frames/{filename}"
