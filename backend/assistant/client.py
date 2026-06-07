"""
SAGE - Assistant Client.

This is the production orchestration layer. It exposes ONE function -
chat() - which is what the FastAPI endpoint will call.

What it does:
  1. Loads the conversation history from the database (so Claude remembers
     what the student said earlier in this session).
  2. Saves the new user message to the database.
  3. Runs the agentic Claude+MCP loop with all available tools.
  4. Saves Claude's final response (and which tools it used) to the database.
  5. Returns the final answer + metadata.

The ~80-line loop here replaces what would otherwise be hundreds of lines
of orchestration framework code (LangGraph / CrewAI). Claude itself
decides which tools to call.

Owner: Abrar (AI/MCP Lead)
"""

import json
import os
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Message, Session as DBSession
from backend.mcp_servers.exam_prep_server import EXAM_PREP_TOOLS, execute_tool

load_dotenv()

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

_client = Anthropic()
_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
_MAX_TOOL_ITERATIONS = 6  # safety cap to prevent infinite tool-call loops

SYSTEM_PROMPT_TEMPLATE = (
    "You are SAGE (Student Academic Guidance Engine), an AI study assistant. "
    "You help university students prepare for exams, search their uploaded "
    "documents, generate quizzes, and plan their studies.\n\n"
    "{collection_hint}"
    "You have access to MCP tools - use them when relevant. In particular:\n"
    "- When the student references their own materials, ALWAYS call "
    "search_materials first to ground your answer in their documents.\n"
    "- When asked to quiz them on their materials, call search_materials "
    "first, then generate_quiz with the retrieved context.\n"
    "- When the student wants an overview of what they uploaded, "
    "call summarize_document.\n\n"
    "Be warm, encouraging, and pedagogically minded - you're a tutor, "
    "not just a search engine."
)


def _build_system_prompt(collection_name: str | None) -> str:
    """Inject the active collection name into the system prompt so Claude
    knows which collection to pass to search_materials / summarize_document."""
    if collection_name:
        hint = (
            f"IMPORTANT: The student's active document collection is "
            f"'{collection_name}'. ALWAYS use this exact value for the "
            f"'collection_name' parameter when calling search_materials or "
            f"summarize_document.\n\n"
        )
    else:
        hint = (
            "Note: The student has not uploaded any documents yet. If they "
            "ask about 'their materials', politely tell them to upload a "
            "PDF using the sidebar first.\n\n"
        )
    return SYSTEM_PROMPT_TEMPLATE.format(collection_hint=hint)


# ----------------------------------------------------------------------
# DATABASE HELPERS
# ----------------------------------------------------------------------

async def _load_history(db: AsyncSession, session_id: str) -> list[dict]:
    """
    Load past messages from this session in Claude's expected format.
    Returns a list of {"role": ..., "content": ...} dicts.
    """
    stmt = (
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    result = await db.execute(stmt)
    messages = result.scalars().all()

    return [{"role": m.role, "content": m.content} for m in messages]


async def _save_message(
    db: AsyncSession,
    session_id: str,
    role: str,
    content: str,
    tools_used: dict | None = None,
) -> None:
    """Persist a single message to the database."""
    msg = Message(
        session_id=session_id,
        role=role,
        content=content,
        tools_used=tools_used or {},
    )
    db.add(msg)
    await db.commit()


# ----------------------------------------------------------------------
# THE MAIN CHAT FUNCTION (this is what the API endpoint will call)
# ----------------------------------------------------------------------

async def chat(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    user_message: str,
    collection_name: str | None = None,
) -> dict[str, Any]:
    """
    Handle one full chat turn: load history, run agentic loop, save messages,
    return the result.

    Args:
        db:              Async SQLAlchemy session.
        user_id:         The student's UUID.
        session_id:      The chat session (conversation thread) UUID.
        user_message:    What the student just typed.
        collection_name: The active document collection (if any). Tells Claude
                         which ChromaDB collection to search.

    Returns:
        {
          "reply": str,          # Claude's final text response
          "tools_used": list,    # which MCP tools fired this turn
          "iterations": int,     # how many Claude calls it took
        }
    """
    # 1. Load history and save the new user message
    history = await _load_history(db, session_id)
    await _save_message(db, session_id, role="user", content=user_message)

    # Build the conversation in Claude's expected format
    messages: list[dict] = history + [{"role": "user", "content": user_message}]

    # 2. The agentic loop. Each iteration is one call to Claude.
    tools_used: list[str] = []
    final_text = ""

    for iteration in range(1, _MAX_TOOL_ITERATIONS + 1):
        response = _client.messages.create(
            model=_MODEL,
            max_tokens=2048,
            system=_build_system_prompt(collection_name),
            tools=EXAM_PREP_TOOLS,
            messages=messages,
        )

        # Case A: Claude wants to use one or more tools
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_used.append(block.name)
                    result = execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            messages.append({"role": "user", "content": tool_results})
            continue  # loop again so Claude can use the results

        # Case B: Claude produced a final text answer - we're done
        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            break

        # Anything else (rare): bail out cleanly
        final_text = "[The assistant stopped unexpectedly.]"
        break
    else:
        # Hit the iteration cap
        final_text += "\n\n[Stopped after reaching tool-call limit.]"

    # 3. Save Claude's final response
    await _save_message(
        db,
        session_id,
        role="assistant",
        content=final_text,
        tools_used={"tools": tools_used},
    )

    return {
        "reply": final_text,
        "tools_used": tools_used,
        "iterations": iteration,
    }