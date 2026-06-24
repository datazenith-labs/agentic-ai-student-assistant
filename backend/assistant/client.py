"""
SAGE - Assistant Client.

This module exposes TWO entry points:

  * chat()         — blocking; returns final result as a dict.
                     Used by POST /api/v1/chat.
  * chat_stream()  — async generator; yields SSE events as Claude
                     produces tokens and uses tools.
                     Used by POST /api/v1/chat/stream.

Both share the same agentic loop logic, MCP tool registry, system
prompt, and database persistence helpers. Only the response style
differs (one return vs many yields).

Multi-server design:
  - exam_prep_server   : RAG, quizzes, confidence tracking, revision plans
  - advisor_server     : profile, course recommendations, prerequisites
  - campus_server      : deadlines, timetable, daily-life tasks

Adding a new MCP server is still a 3-line change: import its TOOLS and
execute function, then register both.

Owner: Abrar (AI/MCP Lead)
"""

import json
import os
from typing import Any, AsyncGenerator

from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import Message
from backend.schemas.chat import (
    DoneEvent,
    ErrorEvent,
    TokenEvent,
    ToolEndEvent,
    ToolStartEvent,
)

# Each MCP server exports a TOOLS list and an execute function.
from backend.mcp_servers.exam_prep_server import (
    EXAM_PREP_TOOLS,
    execute_tool as execute_exam_prep_tool,
)
from backend.mcp_servers.advisor_server import (
    ADVISOR_TOOLS,
    execute_advisor_tool,
)
from backend.mcp_servers.campus_server import (
    CAMPUS_TOOLS,
    execute_campus_tool,
)

load_dotenv()


# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------

_client = Anthropic()
_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")
_MAX_TOOL_ITERATIONS = 10  # full-stack chains use many tools


# ----------------------------------------------------------------------
# TOOL REGISTRY (built once at import time)
# ----------------------------------------------------------------------

ALL_TOOLS = EXAM_PREP_TOOLS + ADVISOR_TOOLS + CAMPUS_TOOLS

_TOOL_DISPATCH = {}
for tool in EXAM_PREP_TOOLS:
    _TOOL_DISPATCH[tool["name"]] = execute_exam_prep_tool
for tool in ADVISOR_TOOLS:
    _TOOL_DISPATCH[tool["name"]] = execute_advisor_tool
for tool in CAMPUS_TOOLS:
    _TOOL_DISPATCH[tool["name"]] = execute_campus_tool


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
    "You help university students across three areas:\n"
    "  1. Studying: RAG over their uploaded materials, quizzes, summaries.\n"
    "  2. Adaptive learning: tracking confidence, identifying weak topics, "
    "building revision plans.\n"
    "  3. Academic advising: reading their profile, recommending courses, "
    "checking prerequisites.\n"
    "  4. Campus life: managing deadlines, viewing their timetable, "
    "organising their week.\n\n"
    "IMPORTANT IDENTIFIERS:\n"
    "- The student's user_id is: '{user_id}'\n"
    "- ALWAYS use this exact user_id for tools that need it.\n\n"
    "{collection_hint}"
    "Tool behavior guidelines:\n"
    "- For 'what does my document say...' → search_materials first.\n"
    "- For 'quiz me on my materials' → search_materials then generate_quiz.\n"
    "- For 'summarize what I uploaded' → summarize_document.\n"
    "- For 'mock exam', 'practice exam', 'simulate exam', 'full exam' → "
    "create_mock_exam. If the student has uploaded materials, call "
    "search_materials FIRST, then pass the context to create_mock_exam.\n"
    "- For 'how did I do?', 'grade my answer', 'was my answer correct?' → "
    "evaluate_answer. Call this after the student submits any answer.\n"
    "- For self-ratings ('I'm confident on X', 'I'm weak on Y') → "
    "log_confidence (once per topic).\n"
    "- For 'what should I focus on?' or 'my weak areas?' → "
    "identify_weak_topics.\n"
    "- For 'upcoming exam, plan it' → identify_weak_topics first (if no topics "
    "given), then generate_revision_plan.\n"
    "- For 'what's my profile?' or 'what do you know about me?' → "
    "get_student_profile.\n"
    "- For 'what should I take next semester?' or 'recommend courses' → "
    "get_student_profile first, then recommend_courses.\n"
    "- For 'can I take CS401?' or 'am I ready for X?' → check_prerequisites.\n"
    "- For 'I have an assignment/exam/project due...' → add_deadline.\n"
    "- For 'what's due?', 'what's coming up?', 'what's this week?' → "
    "list_upcoming_deadlines.\n"
    "- For 'what's my schedule', 'what's my Monday', 'my timetable' → "
    "get_timetable_summary.\n"
    "- For BIG questions that span domains (e.g. 'given my schedule, my "
    "deadlines, and my weak topics, plan my next two weeks'): chain tools "
    "across servers. This cross-server orchestration is encouraged and is "
    "where SAGE shines.\n\n"
    "Be warm, encouraging, and pedagogically minded - you're a tutor, "
    "advisor, AND life-organiser."
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
# BLOCKING CHAT (unchanged from previous version)
# ----------------------------------------------------------------------

async def chat(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    user_message: str,
    collection_name: str | None = None,
) -> dict[str, Any]:
    """
    Handle one full chat turn (blocking): load history, run agentic loop,
    save messages, return the final result as a dict.

    Used by POST /api/v1/chat.
    """
    history = await _load_history(db, session_id)
    await _save_message(db, session_id, role="user", content=user_message)

    messages: list[dict] = history + [{"role": "user", "content": user_message}]

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
            continue

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            break

        final_text = "[The assistant stopped unexpectedly.]"
        break
    else:
        final_text += "\n\n[Stopped after reaching tool-call limit.]"

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


# ----------------------------------------------------------------------
# STREAMING CHAT (new — for SSE endpoint)
# ----------------------------------------------------------------------

async def chat_stream(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    user_message: str,
    collection_name: str | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Streaming version of chat(). Yields SSE event dicts as Claude produces
    them. Persists the user message before streaming and the assistant
    message after streaming completes.

    Used by POST /api/v1/chat/stream.

    Yields one of:
        TokenEvent       — partial text from Claude
        ToolStartEvent   — Claude is about to call an MCP tool
        ToolEndEvent     — Tool returned; Claude can resume
        DoneEvent        — Final, exactly one per successful turn
        ErrorEvent       — Final, exactly one per failed turn

    All events are emitted as dicts (via .model_dump()). The endpoint
    layer is responsible for SSE wire formatting ("data: ...\\n\\n").
    """
    try:
        # Load history + save user message before streaming starts.
        history = await _load_history(db, session_id)
        await _save_message(db, session_id, role="user", content=user_message)

        messages: list[dict] = history + [{"role": "user", "content": user_message}]
        tools_used: list[str] = []
        final_text = ""
        iteration = 0

        for iteration in range(1, _MAX_TOOL_ITERATIONS + 1):
            # Accumulators reset each iteration.
            iteration_text = ""        # text accumulated this iteration
            assistant_blocks = []      # full content blocks for history append
            pending_tool_blocks = []   # tool_use blocks to execute after stream

            with _client.messages.stream(
                model=_MODEL,
                max_tokens=2048,
                system=_build_system_prompt(user_id, collection_name),
                tools=ALL_TOOLS,
                messages=messages,
            ) as stream:
                for event in stream:
                    # Yield text deltas as token events.
                    if event.type == "text":
                        yield TokenEvent(text=event.text).model_dump()
                        iteration_text += event.text

                # After the stream completes, inspect the final message for tool_use blocks.
                final_message = stream.get_final_message()
                stop_reason = final_message.stop_reason

                for block in final_message.content:
                    assistant_blocks.append(block)
                    if block.type == "tool_use":
                        pending_tool_blocks.append(block)

            # Append the assistant turn (text + any tool_use blocks) to history.
            messages.append({"role": "assistant", "content": assistant_blocks})

            # Case A: Claude wants to use tools — execute them and continue the loop.
            if stop_reason == "tool_use" and pending_tool_blocks:
                tool_results = []
                for block in pending_tool_blocks:
                    # Tell the frontend a tool is starting.
                    yield ToolStartEvent(
                        id=block.id,
                        name=block.name,
                        input=block.input or {},
                    ).model_dump()

                    tools_used.append(block.name)
                    result = _execute_any_tool(block.name, block.input)
                    status = result.get("status", "ok") if isinstance(result, dict) else "ok"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

                    # Tell the frontend the tool finished.
                    yield ToolEndEvent(id=block.id, status=status).model_dump()

                messages.append({"role": "user", "content": tool_results})
                continue

            # Case B: Claude produced a final text answer — done.
            if stop_reason == "end_turn":
                final_text += iteration_text
                break

            # Case C: Some other stop reason — bail out.
            final_text += iteration_text or "[The assistant stopped unexpectedly.]"
            break
        else:
            # Loop hit max iterations without break.
            final_text += "\n\n[Stopped after reaching tool-call limit.]"

        # Persist assistant message after streaming is fully done.
        await _save_message(
            db,
            session_id,
            role="assistant",
            content=final_text,
            tools_used={"tools": tools_used},
        )

        # Final event: signals stream end.
        yield DoneEvent(iterations=iteration, tools_used=tools_used).model_dump()

    except Exception as exc:  # noqa: BLE001 — endpoint layer doesn't see this otherwise
        yield ErrorEvent(
            message=f"{type(exc).__name__}: {exc}",
        ).model_dump()
