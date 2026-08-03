"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI

from src.api.routes import router
from src.api.auth import router as auth_router

from fastapi.responses import JSONResponse
import traceback

app = FastAPI(title="Adaptive RAG API")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    print(f"Global Exception: {exc}")
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "traceback": traceback.format_exc()}
    )

app.include_router(router)
app.include_router(auth_router)
app.state.description_ = ""


@app.get("/")
async def root():
    """Root endpoint to verify API is running."""
    return {"message": "Adaptive RAG API is running"}
