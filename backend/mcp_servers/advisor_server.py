"""
SAGE - Advisor MCP Server (Phase 3 - course recommendations & profile).

This is the SECOND MCP server in SAGE. It handles academic guidance:
  - Reading the student's profile (major, year, strengths, weaknesses, goals).
  - Recommending courses for an upcoming semester.
  - Checking course prerequisites.

Architecturally, this proves the multi-server MCP design works:
Claude orchestrates tools from both exam_prep_server AND advisor_server
without either knowing the other exists.

Owner: Abrar (AI/MCP Lead)
"""

import os

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Allow nested asyncio loops (tool calls are sync, DB calls are async)
import nest_asyncio
nest_asyncio.apply()

from backend.database.models import StudentProfile

load_dotenv()

# ----------------------------------------------------------------------
# Internal database session (separate from FastAPI's request-scoped one,
# so tools can run from any context — test scripts, CLI, the API loop).
# ----------------------------------------------------------------------

_DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/sage.db")
_tool_engine = create_async_engine(_DB_URL)
_ToolSession = async_sessionmaker(_tool_engine, expire_on_commit=False)


# ====================================================================
# IN-MEMORY COURSE CATALOG
# Realistic enough for a demo. In production, this would come from a
# university API or a courses table populated from the registrar.
# ====================================================================

_COURSE_CATALOG = {
    "CS301": {
        "title": "Algorithms",
        "credits": 4,
        "prerequisites": ["CS201"],
        "tags": ["theory", "core"],
        "description": "Algorithm design, complexity analysis, dynamic programming, greedy methods.",
    },
    "CS302": {
        "title": "Operating Systems",
        "credits": 4,
        "prerequisites": ["CS202"],
        "tags": ["systems", "core"],
        "description": "Processes, threads, scheduling, memory, file systems, concurrency.",
    },
    "CS310": {
        "title": "Databases",
        "credits": 3,
        "prerequisites": ["CS202"],
        "tags": ["systems", "core"],
        "description": "Relational model, SQL, indexing, transactions, NoSQL overview.",
    },
    "CS320": {
        "title": "Computer Networks",
        "credits": 3,
        "prerequisites": ["CS202"],
        "tags": ["systems", "elective"],
        "description": "Layered protocols, TCP/IP, routing, HTTP, security basics.",
    },
    "CS401": {
        "title": "Machine Learning",
        "credits": 4,
        "prerequisites": ["CS301", "MATH202"],
        "tags": ["ml", "elective"],
        "description": "Supervised/unsupervised learning, linear models, neural nets, evaluation.",
    },
    "CS402": {
        "title": "Deep Learning",
        "credits": 4,
        "prerequisites": ["CS401"],
        "tags": ["ml", "elective"],
        "description": "Backprop, CNNs, RNNs, Transformers, modern architectures.",
    },
    "CS410": {
        "title": "Distributed Systems",
        "credits": 3,
        "prerequisites": ["CS302", "CS320"],
        "tags": ["systems", "elective"],
        "description": "Consensus, replication, fault tolerance, real distributed databases.",
    },
    "CS420": {
        "title": "AI Safety & Alignment",
        "credits": 3,
        "prerequisites": ["CS401"],
        "tags": ["ml", "elective"],
        "description": "Alignment problem, RLHF, interpretability, model evaluation, safety case studies.",
    },
    "CS499": {
        "title": "Bachelor's Thesis",
        "credits": 6,
        "prerequisites": ["CS301", "CS302"],
        "tags": ["capstone"],
        "description": "Independent research project supervised by a faculty member.",
    },
}


# ====================================================================
# TOOL DEFINITIONS (the "menu" Claude reads to decide what to call)
# ====================================================================

ADVISOR_TOOLS = [
    {
        "name": "get_student_profile",
        "description": (
            "Read the student's stored academic profile: major, year of study, "
            "weak topics, strong topics, and stated goals. Use this when the "
            "student asks 'what do you know about me?', 'what's my profile?', "
            "or when you need their background to give personalized advice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The student's user ID from the system prompt.",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "recommend_courses",
        "description": (
            "Recommend courses for the student to consider next semester, based "
            "on their profile (major, year, completed prerequisites, strengths, "
            "weaknesses, and goals). Use this when the student asks 'what should "
            "I take next semester?', 'recommend me courses', or 'what would help "
            "me reach my goals?'. Returns a ranked list with reasoning."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The student's user ID.",
                },
                "completed_courses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of course codes the student has already passed (e.g. ['CS101','CS201']). If unknown, pass an empty list.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "How many recommendations to return. Default 5.",
                    "default": 5,
                },
            },
            "required": ["user_id", "completed_courses"],
        },
    },
    {
        "name": "check_prerequisites",
        "description": (
            "Check whether a student has met the prerequisites for a course. "
            "Use this when the student asks 'can I take CS401?' or 'am I ready "
            "for X?'. Returns the prerequisites and which ones are still missing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "course_code": {
                    "type": "string",
                    "description": "Course code to check, e.g. 'CS401'.",
                },
                "completed_courses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of course codes the student has already passed.",
                },
            },
            "required": ["course_code", "completed_courses"],
        },
    },
]


# ====================================================================
# TOOL IMPLEMENTATIONS
# ====================================================================

async def _get_student_profile_async(user_id: str) -> dict:
    """Read the StudentProfile row for this user."""
    async with _ToolSession() as session:
        stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()

    if profile is None:
        return {
            "status": "not_found",
            "message": (
                "No profile exists for this user yet. Suggest the student fill "
                "out their major, year, and academic goals so SAGE can give "
                "personalized advice."
            ),
        }

    return {
        "status": "ok",
        "user_id": user_id,
        "major": profile.major,
        "year_of_study": profile.year_of_study,
        "weak_topics": profile.weak_topics or [],
        "strong_topics": profile.strong_topics or [],
        "goals": profile.goals or "",
    }


def get_student_profile(user_id: str) -> dict:
    """Sync wrapper around the async DB call."""
    import asyncio
    return asyncio.run(_get_student_profile_async(user_id))


def recommend_courses(
    user_id: str,
    completed_courses: list[str],
    max_results: int = 5,
) -> dict:
    """
    Recommend courses by:
      1. Filter to courses whose prerequisites are met.
      2. Exclude courses the student already completed.
      3. Boost courses tagged 'ml' if the profile mentions ML/AI in goals
         (we don't read the profile here — Claude will pass that context in
         the conversation, OR call get_student_profile first).
      4. Return up to max_results with prerequisite info.
    """
    completed_set = set(completed_courses)
    candidates = []

    for code, info in _COURSE_CATALOG.items():
        if code in completed_set:
            continue

        prereqs = info.get("prerequisites", [])
        missing = [p for p in prereqs if p not in completed_set]
        if missing:
            continue  # not eligible

        candidates.append({
            "course_code": code,
            "title": info["title"],
            "credits": info["credits"],
            "tags": info["tags"],
            "description": info["description"],
            "prerequisites_met": prereqs,
        })

    # Ranking: 'ml' tagged first (a reasonable default for SAGE's audience),
    # then 'core' courses, then everything else.
    def _rank(c):
        if "ml" in c["tags"]:
            return 0
        if "core" in c["tags"]:
            return 1
        if "capstone" in c["tags"]:
            return 2
        return 3

    candidates.sort(key=_rank)

    return {
        "status": "ok",
        "total_eligible": len(candidates),
        "recommendations": candidates[:max_results],
        "note": (
            "Recommendations are ranked by relevance to ML/AI focus, then core, "
            "then electives. Use the student's profile and goals to explain why "
            "specific recommendations make sense for them."
        ),
    }


def check_prerequisites(course_code: str, completed_courses: list[str]) -> dict:
    """Check whether the student has met the prerequisites for a given course."""
    code = course_code.upper().strip()
    if code not in _COURSE_CATALOG:
        return {
            "status": "unknown_course",
            "message": f"Course '{code}' is not in the catalog. Known courses: {list(_COURSE_CATALOG.keys())}",
        }

    info = _COURSE_CATALOG[code]
    prereqs = info.get("prerequisites", [])
    completed_set = set(completed_courses)
    missing = [p for p in prereqs if p not in completed_set]

    return {
        "status": "ok",
        "course_code": code,
        "title": info["title"],
        "prerequisites": prereqs,
        "missing_prerequisites": missing,
        "ready_to_take": len(missing) == 0,
    }


# ====================================================================
# TOOL DISPATCHER
# ====================================================================

def execute_advisor_tool(tool_name: str, tool_input: dict) -> dict:
    """Route an advisor tool call to the right Python function."""
    if tool_name == "get_student_profile":
        return get_student_profile(**tool_input)
    if tool_name == "recommend_courses":
        return recommend_courses(**tool_input)
    if tool_name == "check_prerequisites":
        return check_prerequisites(**tool_input)
    raise ValueError(f"Unknown advisor tool: {tool_name}")