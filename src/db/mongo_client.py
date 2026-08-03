"""
MongoDB client initialization.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from src.core.config import settings

MONGO_URL = settings.MONGODB_URL
DB_NAME = "adaptive_rag"

client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=2000)
db = client[DB_NAME]
