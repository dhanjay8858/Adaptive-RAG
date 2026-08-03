"""
API client for communicating with backend services.
"""

import logging
import os

import requests

logger = logging.getLogger(__name__)

# Backend service URLs
RUST_BASE_URL = "http://localhost:8080/api"
PYTHON_BASE_URL = os.getenv("PYTHON_BASE_URL", "http://127.0.0.1:8000")


def create_user(username: str, password: str, api_token: str) -> bool:
    """Create a user on the FastAPI backend."""
    logger.info("Calling real create_user")
    url = f"{PYTHON_BASE_URL}/auth/signup"
    try:
        response = requests.post(
            url,
            json={"username": username, "password": password, "api_token": api_token}
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False


def login_user(username: str, password: str, api_token: str) -> dict:
    """Login a user via the FastAPI backend."""
    logger.info("Calling real login_user")
    url = f"{PYTHON_BASE_URL}/auth/login"
    try:
        response = requests.post(
            url,
            json={"username": username, "password": password, "api_token": api_token}
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Error logging in: {e}")
    return {}


def verify_jwt_token(token: str) -> dict:
    """Verify a JWT token with the FastAPI backend."""
    url = f"{PYTHON_BASE_URL}/auth/verify"
    try:
        response = requests.post(
            url,
            json={"token": token}
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
    return {}


def get_api_token() -> str:
    """Mock API token retrieval since Rust backend is missing."""
    logger.info("Mock get_api_token called")
    return "mock_api_token"


def query_backend(query: str, session_id: str) -> str:
    """
    Send a query to the RAG backend.

    Args:
        query: The user's query text.
        session_id: Session identifier for tracking conversation.

    Returns:
        Response text from the backend or error message.
    """
    url = f"{PYTHON_BASE_URL}/rag/query"
    print(f"[query_backend] Calling: {url}")

    response = requests.post(
        url,
        json={"query": query, "session_id": session_id},
        allow_redirects=False
    )

    if response.status_code == 200:
        return response.json()["result"]["content"]
    else:
        return f"Error: {response.status_code} - {response.text}"


def get_chat_history(jwt_token: str) -> list:
    """
    Fetch the complete chat history for a logged-in user.
    """
    url = f"{PYTHON_BASE_URL}/rag/history"
    try:
        response = requests.get(url, headers={"Authorization": f"Bearer {jwt_token}"})
        if response.status_code == 200:
            return response.json().get("history", [])
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
    return []


def document_upload_rag(file, description: str) -> bool:
    """
    Upload a document to the RAG system.

    Args:
        file: File object to upload.
        description: Description of the document.

    Returns:
        True if upload succeeds, False otherwise.
    """
    headers = {
        "X-Description": description
    }
    url = f"{PYTHON_BASE_URL}/rag/documents/upload"

    if file:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(url, files=files, headers=headers)
        print(response)

        if response.status_code == 200:
            return True

    return False
