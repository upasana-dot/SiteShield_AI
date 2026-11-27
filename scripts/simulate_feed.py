"""Post sampled video frames to SiteShield's /predict endpoint."""
import argparse
import time
from pathlib import Path

import cv2
import requests


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path, help="Path to a local video")
    parser.add_argument("--url", default="http://localhost:8000/predict")
    parser.add_argument("--camera-id", default="demo-camera")
    parser.add_argument("--site", default="Demo Site")
    parser.add_argument("--every-ms", type=int, default=500)
    parser.add_argument("--max-width", type=int, default=640)
    args = parser.parse_args()
    if args.every_ms <= 0 or args.max_width <= 0 or not args.video.is_file():
        parser.error("Provide an existing video, positive --every-ms, and positive --max-width.")

    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise RuntimeError(f"Cannot open video: {args.video}")
    video_fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    frame_step = max(1, round(video_fps * args.every_ms / 1000))
    frame_number = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if frame_number % frame_step == 0:
                if frame.shape[1] > args.max_width:
                    scale = args.max_width / frame.shape[1]
                    frame = cv2.resize(frame, (args.max_width, max(1, round(frame.shape[0] * scale))), interpolation=cv2.INTER_AREA)
                encoded, jpg = cv2.imencode(".jpg", frame)
                if encoded:
                    response = requests.post(
                        args.url,
                        files={"file": (f"frame_{frame_number}.jpg", jpg.tobytes(), "image/jpeg")},
                        data={"camera_id": args.camera_id, "site_location": args.site},
                        timeout=30,
                    )
                    response.raise_for_status()
                    result = response.json()
                    score = result.get("compliance_score")
                    print(f"violations={len(result.get('new_violations', []))} compliance={score if score is not None else 'n/a'} inference_ms={result.get('inference_ms', 'n/a')}")
                time.sleep(args.every_ms / 1000)
            frame_number += 1
    finally:
        capture.release()


if __name__ == "__main__":
    main()
