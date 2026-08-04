"""
API routes for RAG operations.
"""

from fastapi import APIRouter, UploadFile, File, Header
from langchain_core.messages import HumanMessage, AIMessage

from src.memory.chat_history_mongo import ChatHistory
from src.models.query_request import QueryRequest
from src.rag.document_upload import documents
from src.rag.graph_builder import builder

router = APIRouter()


@router.post("/rag/query")
async def rag_query(req: QueryRequest):
    """
    Process a RAG query and return the result.

    Args:
        req: The query request containing query text and session_id.

    Returns:
        The generated response from the RAG pipeline.
    """
    # Try to decode JWT to use username as the stable session ID
    actual_session_id = req.session_id
    try:
        import jwt
        from src.api.auth import SECRET_KEY
        payload = jwt.decode(req.session_id, SECRET_KEY, algorithms=["HS256"])
        if "sub" in payload:
            actual_session_id = payload["sub"]
    except Exception:
        pass # Fallback to original string if not a valid JWT
        
    chat_history = ChatHistory.get_session_history(actual_session_id)
    await chat_history.add_message(HumanMessage(content=req.query))

    # Fetch full history
    all_messages = await chat_history.get_messages()
    
    # Sliding window memory: only send the last 5 messages to the AI
    # This keeps API costs down and prevents context window limits from being exceeded
    recent_messages = all_messages[-5:] if len(all_messages) > 5 else all_messages
    
    result = builder.invoke({
        "messages": recent_messages
    })
    output_text = result["messages"][-1].content

    # Save assistant message
    await chat_history.add_message(AIMessage(content=output_text))

    return {"result": result["messages"][-1]}


@router.get("/rag/history")
async def get_history(authorization: str = Header(...)):
    """
    Fetch the complete chat history for a logged-in user.
    """
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    actual_session_id = token
    try:
        import jwt
        from src.api.auth import SECRET_KEY
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        if "sub" in payload:
            actual_session_id = payload["sub"]
    except Exception:
        pass # Fallback to original string if not a valid JWT
        
    chat_history = ChatHistory.get_session_history(actual_session_id)
    all_messages = await chat_history.get_messages()
    
    # Convert LangChain messages to a simple format for the frontend
    formatted_messages = []
    for msg in all_messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        formatted_messages.append({"role": role, "content": msg.content})
        
    return {"history": formatted_messages}


@router.post("/rag/documents/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Header(..., alias="X-Description")
):
    """
    Upload a document for RAG processing.

    Args:
        file: The file to upload (PDF or TXT).
        description: Document description provided via header.

    Returns:
        Upload status.
    """
    status_upload = documents(description, file)
    if not status_upload:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Failed to embed and store document. Please check your embedding API keys.")
    return {"status": status_upload}

