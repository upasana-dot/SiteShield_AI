# SiteShield AI backend

SiteShield AI is a CPU-only FastAPI backend for construction-site PPE compliance monitoring. It loads the existing YOLOv8 model; training stays in Google Colab and is not part of this backend.

## Setup

1. Open a terminal in the project root and create a Python 3.11 virtual environment:
   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   New-Item -ItemType Directory -Force .tmp | Out-Null
   $env:TEMP = Join-Path (Get-Location) ".tmp"
   $env:TMP = $env:TEMP
   python -m pip install --no-cache-dir -r requirements.txt
   ```
2. Create local settings with `Copy-Item .env.example .env`; set `MONGO_URI` and other values as needed.
3. Start MongoDB Community locally, or create a MongoDB Atlas cluster and use its connection URI in `MONGO_URI`. Atlas requires network access and a database user configured in Atlas.
4. The default weights and metadata are `models/v1/best.pt` and `models/v1/metadata.json`. Set `MODEL_PATH` and `MODEL_META_PATH` to change them. Startup validates the model classes against metadata and fails clearly if they differ.
5. Start the API from the project root:
   ```powershell
   python -m uvicorn app.main:app --reload
   ```

The API is available at `http://localhost:8000`; interactive docs are at `/docs`. The default CORS origins are `http://localhost:5173` and `http://localhost:3000`. A client can subscribe to `ws://localhost:8000/ws/alerts` for new violation events. Annotated frames are served from `/storage/frames/`.

## Live-demo simulation

With the API running, submit sampled frames from a local video:

```powershell
python scripts/simulate_feed.py --video path\to\construction-video.mp4 --every-ms 500 --camera-id demo-camera --site "College Demo Site"
```

The simulator JPEG-encodes each sampled frame, posts it to `/predict`, and prints violation count, compliance score, and inference time. You can try the API in this order: start MongoDB, run Uvicorn, open `/docs`, upload an image to `POST /predict` with `camera_id` and `site_location`, then run the simulator on a video.

##Known limitations

Current test-set AP50 is weak for `NO-Safety Vest` (0.08), `NO-Mask` (0.01), `Fall-Detected`, `Gloves`, `Goggles`, `NO-Gloves`, and `NO-Goggles` (0.00). Those low-performing violation categories are disabled by default in `app/config.py`; `NO-Hardhat` and `NO-Safety Vest` have configurable confidence gates. Retrain and validate a v2 model, then replace `models/v1/best.pt` and its metadata together.
