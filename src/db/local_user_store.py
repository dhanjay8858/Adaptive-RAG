"""
SQLite-backed local user store — fallback when MongoDB is unavailable.

Users registered here are stored in a local SQLite file (fallback_users.db)
which persists across server restarts on Render as long as the server is
not redeployed. This is far more resilient than the previous in-memory dict.
"""

import sqlite3
import logging
import os
import bcrypt

logger = logging.getLogger(__name__)

# Store the DB file next to this module
_DB_PATH = os.path.join(os.path.dirname(__file__), "fallback_users.db")


def _get_conn() -> sqlite3.Connection:
    """Open (or create) the SQLite database and ensure the users table exists."""
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username        TEXT PRIMARY KEY,
            hashed_password TEXT NOT NULL,
            api_token       TEXT
        )
    """)
    conn.commit()
    return conn


class LocalUserStore:
    """SQLite-backed user store used when MongoDB is down."""

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
        try:
            conn = _get_conn()
            row = conn.execute(
                "SELECT * FROM users WHERE username = ?", (username,)
            ).fetchone()
            conn.close()
            return dict(row) if row else None
        except Exception as e:
            logger.error(f"[LocalUserStore] Error reading user: {e}")
            return None

    @staticmethod
    def create_user(username: str, password: str, api_token: str) -> bool:
        try:
            conn = _get_conn()
            # Check if already exists
            existing = conn.execute(
                "SELECT username FROM users WHERE username = ?", (username,)
            ).fetchone()
            if existing:
                conn.close()
                return False  # duplicate username

            hashed = LocalUserStore.get_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, hashed_password, api_token) VALUES (?, ?, ?)",
                (username, hashed, api_token),
            )
            conn.commit()
            conn.close()
            logger.warning(
                f"[LocalUserStore] User '{username}' saved to SQLite (MongoDB unavailable)."
            )
            return True
        except Exception as e:
            logger.error(f"[LocalUserStore] Error creating user: {e}")
            return False
