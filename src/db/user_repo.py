"""
User repository — tries MongoDB first, falls back to in-memory store.
"""

import bcrypt
import logging
from src.db.mongo_client import db
from src.db.local_user_store import LocalUserStore

logger = logging.getLogger(__name__)

users_collection = db["users"]


class UserRepository:
    # ------------------------------------------------------------------ #
    # Password helpers                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def get_password_hash(password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )

    # ------------------------------------------------------------------ #
    # Read user                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def get_user_by_username(username: str) -> dict | None:
        # 1. Try MongoDB
        try:
            user = await users_collection.find_one({"username": username})
            if user is not None:
                return user
            # MongoDB is alive but user not found — also check local store
            # (user may have registered while Mongo was down)
            return LocalUserStore.get_user(username)
        except Exception as e:
            logger.warning(f"[UserRepo] MongoDB read failed, using local store: {e}")
            return LocalUserStore.get_user(username)

    # ------------------------------------------------------------------ #
    # Create user                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    async def create_user(username: str, password: str, api_token: str) -> bool:
        hashed_password = UserRepository.get_password_hash(password)
        user_doc = {
            "username": username,
            "hashed_password": hashed_password,
            "api_token": api_token,
        }

        # 1. Try MongoDB
        try:
            await users_collection.insert_one(user_doc)
            logger.info(f"[UserRepo] User '{username}' created in MongoDB.")
            return True
        except Exception as e:
            logger.warning(
                f"[UserRepo] MongoDB write failed, falling back to local store: {e}"
            )

        # 2. Fallback — save in local in-memory store
        return LocalUserStore.create_user(username, password, api_token)
