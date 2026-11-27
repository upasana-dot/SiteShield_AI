
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import PyMongoError

from app.config import get_settings


# Global MongoDB client and database
_client: MongoClient | None = None
_database: Database | None = None


def connect_to_mongo() -> None:
    """
    Establish MongoDB connection and initialize collections.
    Called when FastAPI starts.
    """
    global _client, _database

    if _client is not None:
        return

    settings = get_settings()

    client = MongoClient(
        settings.mongo_uri,
        serverSelectionTimeoutMS=5000,
    )

    try:
        # Verify MongoDB server connection
        client.admin.command("ping")

        database = client[settings.db_name]

        # Create useful indexes
        database["violations"].create_index(
            [("timestamp", -1)]
        )
        database["violations"].create_index(
            [("status", 1)]
        )
        database["violations"].create_index(
            [("violation_type", 1)]
        )
        database["frame_stats"].create_index(
            [("timestamp", -1)]
        )
        database["frame_stats"].create_index(
            [("camera_id", 1)]
        )

        _client = client
        _database = database

        print(
            f"MongoDB connected successfully: {settings.db_name}"
        )

    except Exception:
        client.close()
        raise


def get_database() -> Database:
    """Return the connected MongoDB database."""
    if _database is None:
        raise PyMongoError(
            "MongoDB is not connected. Check MONGO_URI."
        )

    return _database


def get_violations_collection() -> Collection:
    """Return violations collection."""
    return get_database()["violations"]


def get_frame_stats_collection() -> Collection:
    """Return frame statistics collection."""
    return get_database()["frame_stats"]


def is_mongo_connected() -> bool:
    """Check MongoDB server availability."""
    if _client is None:
        return False

    try:
        _client.admin.command("ping")
        return True

    except PyMongoError:
        return False


def close_mongo_connection() -> None:
    """Close MongoDB connection during application shutdown."""
    global _client, _database

    if _client is not None:
        _client.close()

    _client = None
    _database = None

    print("MongoDB connection closed.")

