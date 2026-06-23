"""
SAGE - Chat endpoints.

POST /api/v1/chat
    Blocking. Returns Claude's full reply as JSON once the agentic
    loop completes. Used by the Streamlit frontend.

POST /api/v1/chat/stream
    Streaming via Server-Sent Events (SSE). Emits token/tool/done/error
    events as Claude produces them. Used by the Next.js frontend.

Both delegate to backend.assistant.client, which owns the actual
Claude + MCP + RAG + DB orchestration.

Owner: Tanjid (Backend) + Abrar (assistant logic)
"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.assistant.client import chat, chat_stream
from backend.database.connection import AsyncSessionLocal
from backend.schemas.chat import ChatRequest, ChatResponse, ErrorEvent

router = APIRouter(prefix="/chat", tags=["chat"])


async def get_db() -> AsyncSession:
    """Yield a database session for the duration of one request."""
    async with AsyncSessionLocal() as session:
        yield session


# ----------------------------------------------------------------------
# BLOCKING ENDPOINT (unchanged)
# ----------------------------------------------------------------------

@router.post(
    "",
    response_model=ChatResponse,
    summary="Send a message to SAGE (blocking)",
    description=(
        "Sends a student's message to the SAGE assistant. The assistant "
        "may call MCP tools (search_materials, generate_quiz, "
        "summarize_document) autonomously to compose its reply. "
        "Conversation history is loaded from the database, and both the "
        "user message and Claude's reply are persisted. If the optional "
        "'collection_name' is provided, Claude will route document searches "
        "to that ChromaDB collection. Returns the full reply once the "
        "agentic loop completes — use /chat/stream for token-by-token UX."
    ),
)
async def chat_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Body: {user_id, session_id, message, collection_name?}"""
    try:
        result = await chat(
            db=db,
            user_id=payload.user_id,
            session_id=payload.session_id,
            user_message=payload.message,
            collection_name=payload.collection_name,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Assistant error: {type(exc).__name__}: {exc}",
        )

    return ChatResponse(
        reply=result["reply"],
        tools_used=result["tools_used"],
        iterations=result["iterations"],
    )


# ----------------------------------------------------------------------
# STREAMING ENDPOINT (new — SSE)
# ----------------------------------------------------------------------

def _format_sse(event: dict) -> bytes:
    """Wrap one event dict as an SSE 'data:' line + blank-line separator."""
    return f"data: {json.dumps(event)}\n\n".encode("utf-8")


async def _sse_generator(
    db: AsyncSession,
    payload: ChatRequest,
) -> AsyncGenerator[bytes, None]:
    """
    Consume events from chat_stream() and yield SSE-formatted bytes.

    Wraps the whole thing in a try/except so that even an exception
    inside chat_stream's setup phase still emits a final error event
    to the client instead of dropping the connection silently.
    """
    try:
        async for event in chat_stream(
            db=db,
            user_id=payload.user_id,
            session_id=payload.session_id,
            user_message=payload.message,
            collection_name=payload.collection_name,
        ):
            yield _format_sse(event)
    except Exception as exc:
        # chat_stream catches most things internally, but if the generator
        # itself can't start (e.g. DB failure), surface it as a final event.
        error = ErrorEvent(message=f"{type(exc).__name__}: {exc}").model_dump()
        yield _format_sse(error)


@router.post(
    "/stream",
    summary="Send a message to SAGE (streaming via SSE)",
    description=(
        "Same semantics as POST /chat, but the response is a Server-Sent "
        "Events stream. Each event is JSON of type 'token', 'tool_start', "
        "'tool_end', 'done', or 'error'. The frontend reads the stream "
        "and updates the UI incrementally for a Claude.ai-style typing "
        "experience. Stream ends with exactly one 'done' or 'error' event."
    ),
    response_class=StreamingResponse,
)
async def chat_stream_endpoint(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Body: same as /chat. Response: text/event-stream."""
    return StreamingResponse(
        _sse_generator(db, payload),
        media_type="text/event-stream",
        headers={
            # Critical: tell proxies/browsers not to buffer the stream.
            # Without this, events accumulate and flush only at the end,
            # defeating the entire point of streaming.
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )