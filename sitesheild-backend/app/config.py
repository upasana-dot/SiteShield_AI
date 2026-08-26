from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017"
    db_name: str = "siteshield"
    model_path: str = "app/ml/weights/best.pt"
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"
    annotations_dir: str = "app/static/annotations"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", extra="ignore")

    @property
    def model_file(self) -> Path:
        path = Path(self.model_path)
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def annotations_path(self) -> Path:
        path = Path(self.annotations_dir)
        return path if path.is_absolute() else BASE_DIR / path

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
