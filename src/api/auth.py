import jwt
import datetime
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.models.auth import AuthRequest
from src.db.user_repo import UserRepository

router = APIRouter()

SECRET_KEY = "super_secret_key_for_adaptive_rag" # In production, this should be in .env

def create_jwt_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/auth/signup")
async def signup(req: AuthRequest):
    # Check if user already exists
    existing_user = await UserRepository.get_user_by_username(req.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    success = await UserRepository.create_user(req.username, req.password, req.api_token)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create user")
        
    return {"message": "User created successfully"}

@router.post("/auth/login")
async def login(req: AuthRequest):
    user = await UserRepository.get_user_by_username(req.username)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    if not UserRepository.verify_password(req.password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
        
    # Generate JWT Token
    token = create_jwt_token(req.username)
    return {"jwt": token, "username": req.username}

class VerifyRequest(BaseModel):
    token: str

@router.post("/auth/verify")
async def verify_token(req: VerifyRequest):
    try:
        payload = jwt.decode(req.token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        
        # Verify the user still exists in the database
        user = await UserRepository.get_user_by_username(username)
        if not user:
            raise HTTPException(status_code=401, detail="User no longer exists")
            
        return {"username": username, "valid": True}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
