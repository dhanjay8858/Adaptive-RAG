"""
In-memory local user store — fallback when MongoDB is unavailable.

Users registered here persist for the lifetime of the server process.
On the next restart, if MongoDB is back online, it will be used again.
"""

import logging
import bcrypt

logger = logging.getLogger(__name__)

# In-memory dict: { username: { "hashed_password": str, "api_token": str } }
_local_users: dict = {}


class LocalUserStore:
    """Thread-safe in-memory user store used when MongoDB is down."""

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

    @staticmethod
    def get_user(username: str) -> dict | None:
        return _local_users.get(username)

    @staticmethod
    def create_user(username: str, password: str, api_token: str) -> bool:
        if username in _local_users:
            return False  # already exists
        _local_users[username] = {
            "username": username,
            "hashed_password": LocalUserStore.get_password_hash(password),
            "api_token": api_token,
        }
        logger.warning(
            f"[LocalUserStore] User '{username}' saved in-memory (MongoDB unavailable)."
        )
        return True
