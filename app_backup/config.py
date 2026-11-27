from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# AP values on the supplied model are weak for several classes. Keep weak
# categories disabled until a better model has been validated.
VIOLATION_CLASS_MAP = {
    "NO-Hardhat": {"label": "No Hardhat", "severity": "High", "enabled": True, "min_conf": 0.30},
    "NO-Safety Vest": {"label": "No Safety Vest", "severity": "Medium", "enabled": True, "min_conf": 0.25},
    "NO-Mask": {"label": "No Mask", "severity": "Low", "enabled": False, "min_conf": 0.30},
    "NO-Gloves": {"label": "No Gloves", "severity": "Low", "enabled": False, "min_conf": 0.30},
    "NO-Goggles": {"label": "No Goggles", "severity": "Low", "enabled": False, "min_conf": 0.30},
    "Fall-Detected": {"label": "Fall Detected", "severity": "Critical", "enabled": False, "min_conf": 0.30},
}


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "siteshield"
    model_path: str = "models/v1/best.pt"
    model_meta_path: str = "models/v1/metadata.json"
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"
    img_size: int = 640
    base_conf: float = 0.20
    cooldown_seconds: int = 30
    max_frame_width: int = 960
    track_timeout_seconds: int = 10

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    def _path(self, value: str) -> Path:
        path = Path(value)
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def model_file(self) -> Path:
        return self._path(self.model_path)

    @property
    def model_meta_file(self) -> Path:
        return self._path(self.model_meta_path)

    @property
    def frames_path(self) -> Path:
        return BASE_DIR / "storage" / "frames"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
