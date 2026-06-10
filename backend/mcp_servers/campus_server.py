"""
SAGE - Campus MCP Server (Phase 1 - day-to-day automation).

This is the THIRD MCP server in SAGE. It handles practical campus tasks:
  - Recording upcoming deadlines (assignments, exams, projects).
  - Listing what's due soon.
  - Returning the student's weekly class timetable.

With this server registered, Claude can coordinate across all three
phases of SAGE: exam_prep (study), advisor (planning), and campus
(daily life). A single question like 'plan my next two weeks given my
schedule and weak topics' will trigger tools from all three.

Owner: Abrar (AI/MCP Lead)
"""

import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Allow nested asyncio loops (matches the pattern in our other MCP servers)
import nest_asyncio
nest_asyncio.apply()

from backend.database.models import Task

load_dotenv()

# ----------------------------------------------------------------------
# Internal database session (separate from FastAPI's request-scoped one)
# ----------------------------------------------------------------------

_DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/sage.db")
_tool_engine = create_async_engine(_DB_URL)
_ToolSession = async_sessionmaker(_tool_engine, expire_on_commit=False)


# ====================================================================
# DEMO TIMETABLE
# In production this would come from a university timetable API or a
# Classes table populated from CSV imports. For the demo, we hardcode
# a realistic week with the same courses referenced by the advisor.
# ====================================================================

_DEMO_TIMETABLE = {
    "Monday":    [{"time": "09:00-10:30", "course": "CS301", "title": "Algorithms",       "location": "Room A-204"},
                  {"time": "13:00-14:30", "course": "CS310", "title": "Databases",        "location": "Lab B-105"}],
    "Tuesday":   [{"time": "10:00-11:30", "course": "CS401", "title": "Machine Learning", "location": "Room C-301"},
                  {"time": "14:00-15:30", "course": "MATH301","title": "Linear Algebra II","location": "Room A-110"}],
    "Wednesday": [{"time": "09:00-10:30", "course": "CS301", "title": "Algorithms",       "location": "Room A-204"},
                  {"time": "13:00-14:30", "course": "CS302", "title": "Operating Systems","location": "Lab B-202"}],
    "Thursday":  [{"time": "10:00-11:30", "course": "CS401", "title": "Machine Learning", "location": "Room C-301"},
                  {"time": "15:00-16:30", "course": "CS320", "title": "Computer Networks","location": "Room D-401"}],
    "Friday":    [{"time": "09:00-10:30", "course": "CS302", "title": "Operating Systems","location": "Lab B-202"},
                  {"time": "13:00-14:30", "course": "CS310", "title": "Databases",        "location": "Lab B-105"}],
}


# ====================================================================
# TOOL DEFINITIONS
# ====================================================================

CAMPUS_TOOLS = [
    {
        "name": "add_deadline",
        "description": (
            "Record an upcoming deadline (assignment, exam, project, "
            "report, etc.) in the student's task list. Use this when the "
            "student says things like 'add a deadline', 'I have an "
            "assignment due...', 'remind me about my exam on...', or "
            "'add this to my to-do list'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The student's user ID from the system prompt.",
                },
                "title": {
                    "type": "string",
                    "description": "Short description of the task, e.g. 'ML Assignment 3' or 'CS302 Midterm'.",
                },
                "due_date_iso": {
                    "type": "string",
                    "description": "Due date in ISO format YYYY-MM-DD. If the student says 'next Friday', calculate the date yourself.",
                },
                "course": {
                    "type": "string",
                    "description": "The course code or name this task belongs to, e.g. 'CS401'. Empty string if not specified.",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Priority level. Default 'medium'.",
                    "default": "medium",
                },
            },
            "required": ["user_id", "title", "due_date_iso"],
        },
    },
    {
        "name": "list_upcoming_deadlines",
        "description": (
            "List the student's upcoming deadlines, sorted by due date "
            "(nearest first). Use this when the student asks 'what's due "
            "this week?', 'what's coming up?', 'what do I have to do?', "
            "or wants an overview of their workload."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The student's user ID.",
                },
                "days_ahead": {
                    "type": "integer",
                    "description": "Only return deadlines within the next N days. Default 14.",
                    "default": 14,
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_timetable_summary",
        "description": (
            "Return the student's weekly class timetable, organised by "
            "day. Use this when the student asks 'what's my Monday?', "
            "'show me my schedule', or when planning study time around "
            "known classes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The student's user ID. (Currently the demo timetable is the same for all users.)",
                },
                "day": {
                    "type": "string",
                    "description": "Optional. One of 'Monday', 'Tuesday', ..., 'Friday'. If omitted, return the whole week.",
                },
            },
            "required": ["user_id"],
        },
    },
]


# ====================================================================
# TOOL IMPLEMENTATIONS
# ====================================================================

async def _add_deadline_async(
    user_id: str,
    title: str,
    due_date_iso: str,
    course: str = "",
    priority: str = "medium",
) -> dict:
    """Insert a new Task row representing an upcoming deadline."""
    try:
        # Parse the date and treat it as end-of-day UTC for safety
        due_date = datetime.fromisoformat(due_date_iso).replace(
            hour=23, minute=59, second=0, tzinfo=timezone.utc
        )
    except ValueError:
        return {
            "status": "error",
            "message": f"Could not parse due_date_iso '{due_date_iso}'. Use YYYY-MM-DD.",
        }

    async with _ToolSession() as session:
        task = Task(
            user_id=user_id,
            title=title.strip(),
            subject=course.strip(),
            priority=priority,
            status="pending",
            due_date=due_date,
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return {
            "status": "ok",
            "task_id": task.id,
            "title": task.title,
            "course": task.subject,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "priority": task.priority,
        }


def add_deadline(
    user_id: str,
    title: str,
    due_date_iso: str,
    course: str = "",
    priority: str = "medium",
) -> dict:
    """Sync wrapper around the async DB call."""
    import asyncio
    return asyncio.run(_add_deadline_async(user_id, title, due_date_iso, course, priority))


async def _list_upcoming_deadlines_async(user_id: str, days_ahead: int = 14) -> dict:
    """Return pending tasks due within the next `days_ahead` days, sorted ascending."""
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_ahead)

    async with _ToolSession() as session:
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .where(Task.status != "done")
            .order_by(Task.due_date.asc())
        )
        result = await session.execute(stmt)
        all_pending = result.scalars().all()

    upcoming = []
    for task in all_pending:
        if task.due_date is None:
            continue
        # The due_date may have been stored as naive (no tzinfo) in SQLite
        due = task.due_date
        if due.tzinfo is None:
            due = due.replace(tzinfo=timezone.utc)
        if now <= due <= cutoff:
            upcoming.append({
                "task_id": task.id,
                "title": task.title,
                "course": task.subject,
                "due_date": due.isoformat(),
                "days_until_due": (due.date() - now.date()).days,
                "priority": task.priority,
            })

    return {
        "status": "ok",
        "total_upcoming": len(upcoming),
        "deadlines": upcoming,
        "window_days": days_ahead,
    }


def list_upcoming_deadlines(user_id: str, days_ahead: int = 14) -> dict:
    """Sync wrapper around the async DB call."""
    import asyncio
    return asyncio.run(_list_upcoming_deadlines_async(user_id, days_ahead))


def get_timetable_summary(user_id: str, day: str | None = None) -> dict:
    """Return the student's weekly (or single-day) class timetable."""
    if day:
        day_clean = day.strip().capitalize()
        if day_clean not in _DEMO_TIMETABLE:
            return {
                "status": "error",
                "message": f"Unknown day '{day}'. Valid: {list(_DEMO_TIMETABLE.keys())}",
            }
        return {
            "status": "ok",
            "day": day_clean,
            "classes": _DEMO_TIMETABLE[day_clean],
        }

    return {
        "status": "ok",
        "week": _DEMO_TIMETABLE,
        "note": "Demo timetable. In production this would come from the university's API.",
    }


# ====================================================================
# TOOL DISPATCHER
# ====================================================================

def execute_campus_tool(tool_name: str, tool_input: dict) -> dict:
    """Route a campus tool call to the right Python function."""
    if tool_name == "add_deadline":
        return add_deadline(**tool_input)
    if tool_name == "list_upcoming_deadlines":
        return list_upcoming_deadlines(**tool_input)
    if tool_name == "get_timetable_summary":
        return get_timetable_summary(**tool_input)
    raise ValueError(f"Unknown campus tool: {tool_name}")