from pydantic import BaseModel
from typing import Optional

class AuthRequest(BaseModel):
    username: str
    password: str
    api_token: Optional[str] = None
