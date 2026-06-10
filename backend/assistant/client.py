"""
SAGE - Assistant Client.

This is the production orchestration layer. It exposes ONE function -
chat() - which is what the FastAPI endpoint will call.

What it does:
  1. Loads the conversation history from the database (so Claude remembers
     what the student said earlier in this session).
  2. Saves the new user message to the database.
  3. Runs the agentic Claude+MCP loop with tools from ALL registered MCP servers.
  4. Saves Claude's final response (and which tools it used) to the database.
  5. Returns the final answer + metadata.

The ~80-line loop here replaces what would otherwise be hundreds of lines
of orchestration framework code (LangGraph / CrewAI). Claude itself
decides which tools to call.

Multi-server design:
  - exam_prep_server   : RAG, quizzes, confidence tracking, revision plans
  - advisor_server     : profile, course recommendations, prerequisites

Adding a new MCP server is now a 3-line change: import its TOOLS and
execute_*_tool function, append, and dispatch.

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

# Each MCP server exports a TOOLS list and an execute function.
from backend.mcp_servers.exam_prep_server import (
    EXAM_PREP_TOOLS,
    execute_tool as execute_exam_prep_tool,
)
from backend.mcp_servers.advisor_server import (
    ADVISOR_TOOLS,
    execute_advisor_tool,
)

load_dotenv()

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

_client = Anthropic()
_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
_MAX_TOOL_ITERATIONS = 8  # bumped from 6 — multi-server chains can be longer


# ----------------------------------------------------------------------
# TOOL REGISTRY (built once at import time)
# ----------------------------------------------------------------------
# Combine all server tools into one menu for Claude.
# Build a dispatch table keyed by tool name so we know which server
# implements each tool.

ALL_TOOLS = EXAM_PREP_TOOLS + ADVISOR_TOOLS

_TOOL_DISPATCH = {}
for tool in EXAM_PREP_TOOLS:
    _TOOL_DISPATCH[tool["name"]] = execute_exam_prep_tool
for tool in ADVISOR_TOOLS:
    _TOOL_DISPATCH[tool["name"]] = execute_advisor_tool


def _execute_any_tool(tool_name: str, tool_input: dict) -> dict:
    """Route a tool call to whichever MCP server owns it."""
    dispatcher = _TOOL_DISPATCH.get(tool_name)
    if dispatcher is None:
        return {"status": "error", "message": f"Unknown tool: {tool_name}"}
    return dispatcher(tool_name, tool_input)


# ----------------------------------------------------------------------
# SYSTEM PROMPT
# ----------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = (
    "You are SAGE (Student Academic Guidance Engine), an AI study assistant. "
    "You help university students with three things:\n"
    "  1. Studying: RAG over their uploaded materials, quizzes, summaries.\n"
    "  2. Adaptive learning: tracking confidence, identifying weak topics, "
    "building revision plans.\n"
    "  3. Academic advising: reading their profile, recommending courses, "
    "checking prerequisites.\n\n"
    "IMPORTANT IDENTIFIERS:\n"
    "- The student's user_id is: '{user_id}'\n"
    "- ALWAYS use this exact user_id for tools that need it "
    "(log_confidence, identify_weak_topics, get_student_profile, "
    "recommend_courses).\n\n"
    "{collection_hint}"
    "Tool behavior guidelines:\n"
    "- For 'what does my document say...' → search_materials first.\n"
    "- For 'quiz me on my materials' → search_materials then generate_quiz.\n"
    "- For 'summarize what I uploaded' → summarize_document.\n"
    "- For self-ratings ('I'm confident on X', 'I'm weak on Y') → "
    "log_confidence (once per topic).\n"
    "- For 'what should I focus on?' or 'my weak areas?' → "
    "identify_weak_topics.\n"
    "- For 'upcoming exam, plan it' → identify_weak_topics first (if no topics "
    "given), then generate_revision_plan.\n"
    "- For 'what's my profile?' or 'what do you know about me?' → "
    "get_student_profile.\n"
    "- For 'what should I take next semester?' or 'recommend courses' → "
    "get_student_profile first (to know background), then recommend_courses.\n"
    "- For 'can I take CS401?' or 'am I ready for X?' → check_prerequisites.\n"
    "- For deeper questions like 'based on my profile AND weak topics, what "
    "should I focus on?' → chain get_student_profile + identify_weak_topics + "
    "synthesize. This cross-server chaining is encouraged.\n\n"
    "Be warm, encouraging, and pedagogically minded - you're a tutor and "
    "advisor, not just a search engine."
)


def _build_system_prompt(user_id: str, collection_name: str | None) -> str:
    """Inject the user_id and active collection name into the system prompt."""
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
    return SYSTEM_PROMPT_TEMPLATE.format(user_id=user_id, collection_hint=hint)


# ----------------------------------------------------------------------
# DATABASE HELPERS
# ----------------------------------------------------------------------

async def _load_history(db: AsyncSession, session_id: str) -> list[dict]:
    """Load past messages from this session in Claude's expected format."""
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
# THE MAIN CHAT FUNCTION
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
        collection_name: The active document collection (if any).

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
            system=_build_system_prompt(user_id, collection_name),
            tools=ALL_TOOLS,
            messages=messages,
        )

        # Case A: Claude wants to use one or more tools
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tools_used.append(block.name)
                    result = _execute_any_tool(block.name, block.input)
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