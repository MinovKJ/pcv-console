"""
Async MongoDB client via Motor.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.config import get_settings

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        cfg = get_settings()
        _client = AsyncIOMotorClient(cfg.mongo_uri, serverSelectionTimeoutMS=5000)
    return _client


def get_mongo_db() -> AsyncIOMotorDatabase:
    cfg = get_settings()
    return get_mongo_client()[cfg.mongo_db]


async def close_mongo() -> None:
    global _client
    if _client:
        _client.close()
        _client = None
