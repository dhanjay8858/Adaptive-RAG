import bcrypt
from src.db.mongo_client import db
import logging

logger = logging.getLogger(__name__)

users_collection = db["users"]

class UserRepository:
    @staticmethod
    def get_password_hash(password: str) -> str:
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        # Store as string for MongoDB
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        # Check password against hash
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )

    @staticmethod
    async def get_user_by_username(username: str) -> dict:
        try:
            return await users_collection.find_one({"username": username})
        except Exception as e:
            logger.error(f"Error fetching user: {e}")
            return None

    @staticmethod
    async def create_user(username: str, password: str, api_token: str) -> bool:
        try:
            hashed_password = UserRepository.get_password_hash(password)
            user = {
                "username": username,
                "hashed_password": hashed_password,
                "api_token": api_token
            }
            await users_collection.insert_one(user)
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
