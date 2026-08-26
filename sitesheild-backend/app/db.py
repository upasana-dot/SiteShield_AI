from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.config import get_settings


_client: MongoClient | None = None


def connect_to_mongo() -> None:
    """Create and verify the MongoDB connection once at application startup."""
    global _client
    settings = get_settings()
    _client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=4_000)
    _client.admin.command("ping")
    get_violations_collection().create_index([("timestamp", -1)])
    get_violations_collection().create_index([("status", 1), ("timestamp", -1)])


def close_mongo_connection() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None


def get_violations_collection() -> Collection:
    if _client is None:
        raise PyMongoError("MongoDB is not connected. Check MONGO_URI and start MongoDB.")
    settings = get_settings()
    return _client[settings.db_name]["violations"]
