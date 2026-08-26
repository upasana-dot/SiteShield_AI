"""Post sampled video frames to SiteShield's /predict endpoint."""
import argparse
import time
from pathlib import Path

import cv2
import requests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path, help="Path to a local video")
    parser.add_argument("--api-url", default="http://localhost:8000/predict")
    parser.add_argument("--interval-ms", type=int, default=1000, help="Milliseconds between posted frames")
    parser.add_argument("--site-location", default="Demo Site")
    args = parser.parse_args()
    if args.interval_ms <= 0 or not args.video.is_file():
        parser.error("Provide an existing video and a positive --interval-ms.")

    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video: {args.video}")
    video_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_step = max(1, round(video_fps * args.interval_ms / 1000))
    frame_number = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_number % frame_step == 0:
                encoded, jpg = cv2.imencode(".jpg", frame)
                if encoded:
                    response = requests.post(
                        args.api_url,
                        files={"file": (f"frame_{frame_number}.jpg", jpg.tobytes(), "image/jpeg")},
                        data={"site_location": args.site_location},
                        timeout=30,
                    )
                    print(response.status_code, response.text)
                time.sleep(args.interval_ms / 1000)
            frame_number += 1
    finally:
        capture.release()


if __name__ == "__main__":
    main()
