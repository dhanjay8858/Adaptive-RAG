"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI

from src.api.routes import router
from src.api.auth import router as auth_router

app = FastAPI(title="Adaptive RAG API")
app.include_router(router)
app.include_router(auth_router)
app.state.description_ = ""


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "Adaptive RAG API is running"}
