# SiteShield AI backend

This is the Python API for SiteShield AI. YOLO training is done separately on Google Colab with a GPU; this repository only loads the resulting `best.pt` and serves inference on CPU.

## Setup

1. Open a terminal in this `sitesheild-backend` directory and create Python 3.11 virtual environment:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env`, then set `MONGO_URI` (local MongoDB or Atlas) and the other values as needed.
3. Copy the model trained in Colab to `app/ml/weights/best.pt`. This file is intentionally not committed.
4. Ensure MongoDB is running, then start the API:
   ```powershell
   uvicorn app.main:app --reload
   ```

The API is available at `http://localhost:8000`; interactive docs are at `/docs`. React development origins on ports 3000 and 5173 are allowed by default. A client can subscribe to `ws://localhost:8000/ws/alerts` for new violation events.

## Live-demo simulation

With the API running, submit one sampled frame every second from a local video:

```powershell
python scripts/simulate_feed.py path\to\construction-video.mp4 --interval-ms 1000 --site-location "College Demo Site"
```

The simulator JPEG-encodes each sampled frame, posts it to `/predict`, and prints each response. Inference is explicitly CPU-only and requests are serialized around the model to keep an i3-class laptop responsive. The response includes all detected classes and bounding boxes; only the six `NO-*`/fall classes create MongoDB violation records and WebSocket alerts.
