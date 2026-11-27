import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pymongo.errors import PyMongoError

from app.config import get_settings
from app.db import close_mongo_connection, connect_to_mongo
from app.ml.detector import detector
from app.routers import analytics, health, model_info, predict, violations
from app.ws.manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    detector.load(settings.model_file, settings.model_meta_file)
    try:
        connect_to_mongo()
    except PyMongoError as exc:
        # The server remains available and each DB endpoint returns a clear 503.
        logger.warning("MongoDB unavailable at startup: %s", exc)
    yield
    close_mongo_connection()


settings = get_settings()
settings.frames_path.mkdir(parents=True, exist_ok=True)
app = FastAPI(title="SiteShield AI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/storage/frames", StaticFiles(directory=str(settings.frames_path)), name="frames")
app.include_router(predict.router)
app.include_router(violations.router)
app.include_router(analytics.router)
app.include_router(model_info.router)
app.include_router(health.router)


@app.websocket("/ws/alerts")
async def alert_socket(websocket: WebSocket) -> None:
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
