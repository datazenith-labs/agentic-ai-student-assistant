"""
SAGE - Chat endpoint.

POST /api/v1/chat
    Accepts a student message; returns Claude's reply.
    Under the hood: runs the assistant client's chat() function
    which orchestrates Claude + MCP tools + RAG + DB persistence.

Owner: Tanjid (Backend) + Abrar (assistant logic)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.assistant.client import chat
from backend.database.connection import AsyncSessionLocal
from backend.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_db() -> AsyncSession:
    """Yield a database session for the duration of one request."""
    async with AsyncSessionLocal() as session:
        yield session


@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a message to SAGE",
    description=(
        "Sends a student's message to the SAGE assistant. The assistant "
        "may call MCP tools (search_materials, generate_quiz, "
        "summarize_document) autonomously to compose its reply. "
        "Conversation history is loaded from the database, and both the "
        "user message and Claude's reply are persisted."
    ),
)
async def chat_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    The main chat endpoint.

    Body shape: {user_id, session_id, message}
    Returns:    {reply, tools_used, iterations}
    """
    try:
        result = await chat(
            db=db,
            user_id=payload.user_id,
            session_id=payload.session_id,
            user_message=payload.message,
        )
    except Exception as exc:
        # Surface the error to the client without leaking internals
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant error: {type(exc).__name__}: {exc}",
        )

    return ChatResponse(
        reply=result["reply"],
        tools_used=result["tools_used"],
        iterations=result["iterations"],
    )