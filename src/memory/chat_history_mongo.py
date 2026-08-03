"""
Chat history storage using MongoDB backend.
"""

from datetime import datetime
from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from datetime import datetime
from typing import List, Dict

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage

from src.db.mongo_client import db

collection = db["chat_history"]

# In-memory store for chat history to bypass MongoDB connection errors
_memory_store: Dict[str, List[BaseMessage]] = {}

class ResilientMongoDBChatMessageHistory(BaseChatMessageHistory):
    """Chat history backed by MongoDB with automatic in-memory fallback."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        if session_id not in _memory_store:
            _memory_store[session_id] = []

    async def add_message(self, message: BaseMessage) -> None:
        """Save a message, trying MongoDB first and falling back to memory."""
        # Always save to memory for consistency in the current session
        _memory_store[self.session_id].append(message)
        
        try:
            await collection.insert_one({
                "session_id": self.session_id,
                "type": message.type,
                "content": message.content,
                "additional_kwargs": message.additional_kwargs,
                "timestamp": datetime.utcnow(),
            })
        except Exception as e:
            print(f"MongoDB write failed, relying on in-memory fallback: {e}")

    async def get_messages(self) -> List[BaseMessage]:
        """Load messages, trying MongoDB first and falling back to memory."""
        try:
            from langchain_core.messages import messages_from_dict
            cursor = collection.find({"session_id": self.session_id}).sort("timestamp", 1)
            docs = await cursor.to_list(length=1000)
            
            if docs:
                return messages_from_dict([
                    {
                        "type": d["type"],
                        "data": {
                            "content": d["content"],
                            "additional_kwargs": d.get("additional_kwargs", {}),
                        }
                    }
                    for d in docs
                ])
        except Exception as e:
            print(f"MongoDB read failed, relying on in-memory fallback: {e}")
            
        return _memory_store.get(self.session_id, [])

    async def clear(self) -> None:
        """Delete all messages for a session."""
        if self.session_id in _memory_store:
            _memory_store[self.session_id] = []
            
        try:
            await collection.delete_many({"session_id": self.session_id})
        except Exception as e:
            print(f"MongoDB clear failed: {e}")

class ChatHistory:
    """Factory for resilient chat history."""

    @classmethod
    def get_session_history(
        cls,
        session_id: str,
        config: dict = None
    ) -> ResilientMongoDBChatMessageHistory:
        """Get or create chat history for a session."""
        return ResilientMongoDBChatMessageHistory(session_id)
