"""
SAGE - Exam Prep MCP Server (Phase 2 - the technical centerpiece).

This module defines the tools Claude can call to help students prepare for exams.
Each tool follows the MCP (Model Context Protocol) format so they can later be
exposed as a standalone MCP server. For now we attach them directly to the
Claude API via the `tools` parameter.

Available tools:
  RAG / Content tools:
    - search_materials      : RAG search over the student's uploaded documents.
    - summarize_document    : Returns a summary of an entire uploaded document.
    - generate_quiz         : Generates a multiple-choice quiz.
    - create_mock_exam      : Generates a full timed practice exam.
    - evaluate_answer       : Grades a student's answer with detailed feedback.

  Adaptive engine tools (Step 9):
    - log_confidence        : Record how confident a student feels on a topic.
    - identify_weak_topics  : Return topics where the student is struggling.
    - generate_revision_plan: Build a buffer-aware study schedule.

Owner: Abrar (AI/MCP Lead)
"""

import json
import os
from datetime import datetime, timedelta, timezone

from anthropic import Anthropic
from dotenv import load_dotenv
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Pull in our RAG retriever — bridge between MCP and RAG
from backend.rag.retriever import search_documents

# Database access for adaptive engine tools
from backend.database.models import ConfidenceLog, MockExam

load_dotenv()

# Allow nested asyncio loops (the adaptive tools wrap async DB calls in
# asyncio.run, which would normally fail when called from inside an already-
# running loop like FastAPI's). nest_asyncio patches Python's asyncio to
# allow this.
import nest_asyncio
nest_asyncio.apply()

_client = Anthropic()
_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


# ----------------------------------------------------------------------
# Internal: a sync engine for tool use
# Tools are called synchronously from the agentic loop, so we use a
# separate sync session here rather than threading async through.
# ----------------------------------------------------------------------

_DB_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/sage.db")
_tool_engine = create_async_engine(_DB_URL)
_ToolSession = async_sessionmaker(_tool_engine, expire_on_commit=False)


# ====================================================================
# TOOL DEFINITIONS (the "menu" Claude reads to decide what to call)
# ====================================================================

EXAM_PREP_TOOLS = [
    # ─── RAG / Content tools ──────────────────────────────────────────
    {
        "name": "search_materials",
        "description": (
            "Search the student's uploaded study materials (lectures, notes, "
            "textbooks) for content relevant to a query. ALWAYS call this tool "
            "FIRST when the student asks about something in their own materials "
            "(phrases like 'what does my lecture say...', 'in my notes...', "
            "'from the document I uploaded...'). Returns the most relevant excerpts."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "A natural-language search query, e.g. 'positional encoding' or 'role of NADPH'.",
                },
                "collection_name": {
                    "type": "string",
                    "description": "The student's document collection name. Use the active collection provided in the system prompt.",
                },
                "top_k": {
                    "type": "integer",
                    "description": "How many excerpts to retrieve. Default is 3.",
                    "default": 3,
                },
            },
            "required": ["query", "collection_name"],
        },
    },
    {
        "name": "summarize_document",
        "description": (
            "Generate a high-level summary of a student's entire uploaded document. "
            "Use this when the student asks 'what is this document about', "
            "'summarize what I uploaded', or wants the big picture of their materials."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "collection_name": {
                    "type": "string",
                    "description": "The student's document collection name.",
                },
            },
            "required": ["collection_name"],
        },
    },
    {
        "name": "generate_quiz",
        "description": (
            "Generate a multiple-choice quiz on a topic. If the student has "
            "uploaded materials and references them (e.g. 'quiz me on my notes'), "
            "you should call search_materials FIRST to get context, then call this "
            "tool with that context in the topic field. For general topics, just "
            "pass the topic name."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic or context to quiz on. Can be a plain topic (e.g. 'photosynthesis') OR retrieved excerpts from the student's documents.",
                },
                "num_questions": {
                    "type": "integer",
                    "description": "How many questions to generate. Default is 3.",
                    "default": 3,
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                    "description": "Difficulty level. Default is 'medium'.",
                    "default": "medium",
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "create_mock_exam",
        "description": (
            "Generate a full timed practice exam simulating real exam conditions. "
            "Use this when the student says things like 'give me a mock exam', "
            "'simulate an exam', 'I want to practice under exam conditions', "
            "'create a practice test', or 'give me a full exam'. Produces a "
            "structured exam with multiple questions, time limits, and instructions. "
            "If the student has uploaded materials, call search_materials FIRST "
            "to get context, then pass that as the topic."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic or context for the exam. Can be a plain topic or retrieved excerpts from documents.",
                },
                "collection_name": {
                    "type": "string",
                    "description": "Optional. The student's document collection for RAG-grounded exams.",
                },
                "num_questions": {
                    "type": "integer",
                    "description": "Number of questions. Default is 20.",
                    "default": 20,
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard"],
                    "description": "Difficulty level. Default is 'medium'.",
                    "default": "medium",
                },
                "duration_minutes": {
                    "type": "integer",
                    "description": "Time limit in minutes. Default is 60.",
                    "default": 60,
                },
            },
            "required": ["topic"],
        },
    },
    {
        "name": "evaluate_answer",
        "description": (
            "Grade a student's answer to a question and provide detailed feedback. "
            "Use this after the student answers a quiz question or mock exam "
            "question. Also use when the student asks 'how did I do?', "
            "'grade my answer', or 'was my answer correct?'. Returns a score, "
            "correctness flag, and specific improvements."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "The original question text.",
                },
                "student_answer": {
                    "type": "string",
                    "description": "The answer the student provided.",
                },
                "correct_answer": {
                    "type": "string",
                    "description": "The correct answer to compare against.",
                },
                "explanation": {
                    "type": "string",
                    "description": "Optional explanation of why the correct answer is right.",
                    "default": "",
                },
            },
            "required": ["question", "student_answer", "correct_answer"],
        },
    },

    # ─── Adaptive engine tools (Step 9) ───────────────────────────────
    {
        "name": "log_confidence",
        "description": (
            "Record how confident a student feels about a topic after studying or "
            "taking a quiz. Use this when the student says things like 'I feel "
            "confident about X', 'I'm still confused about Y', or after they "
            "complete a quiz and rate their understanding. Confidence is on a "
            "0.0-1.0 scale (0=very weak, 1=very strong)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The student's user ID. Use the user_id provided in the system prompt.",
                },
                "topic": {
                    "type": "string",
                    "description": "The topic the student is rating, e.g. 'positional encoding' or 'multi-head attention'.",
                },
                "score": {
                    "type": "number",
                    "description": "Confidence score 0.0-1.0. Map descriptions: very low=0.1, low=0.3, medium=0.5, high=0.75, very high=0.95.",
                },
            },
            "required": ["user_id", "topic", "score"],
        },
    },
    {
        "name": "identify_weak_topics",
        "description": (
            "Look at the student's confidence history and return the topics where "
            "they need the most work. Use this when planning revision, suggesting "
            "what to study, or when the student asks 'what should I focus on?' or "
            "'what are my weak areas?'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The student's user ID. Use the user_id provided in the system prompt.",
                },
                "limit": {
                    "type": "integer",
                    "description": "How many weak topics to return. Default is 5.",
                    "default": 5,
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "generate_revision_plan",
        "description": (
            "Build a day-by-day revision schedule for an upcoming exam. "
            "Distributes weak topics first, leaves buffer days near the exam for "
            "review. Use this when the student says things like 'I have an exam "
            "in N days, help me plan' or 'make me a study schedule'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "exam_date_iso": {
                    "type": "string",
                    "description": "Exam date in ISO format YYYY-MM-DD. If the student says 'in 10 days', calculate the date yourself.",
                },
                "topics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of topics to cover. If empty, call identify_weak_topics first to get the student's weak topics.",
                },
                "hours_per_day": {
                    "type": "number",
                    "description": "Suggested study hours per day. Default 2.",
                    "default": 2,
                },
            },
            "required": ["exam_date_iso", "topics"],
        },
    },
]


# ====================================================================
# TOOL IMPLEMENTATIONS — Content tools
# ====================================================================

def search_materials(query: str, collection_name: str, top_k: int = 3) -> dict:
    """RAG search over the student's documents."""
    chunks = search_documents(query, collection_name, top_k=top_k)
    if not chunks:
        return {
            "status": "no_results",
            "message": f"No content found in collection '{collection_name}'. The student may not have uploaded any documents yet.",
            "excerpts": [],
        }
    return {
        "status": "ok",
        "query": query,
        "excerpts": [
            {
                "page": c["page"],
                "source": c["source"],
                "relevance_score": round(c["score"], 3) if c["score"] else None,
                "text": c["text"],
            }
            for c in chunks
        ],
    }


def summarize_document(collection_name: str) -> dict:
    """Summarize an entire document by retrieving broad chunks and asking Claude to summarize."""
    chunks = search_documents(
        "overview main topics introduction conclusion",
        collection_name,
        top_k=8,
    )
    if not chunks:
        return {
            "status": "no_results",
            "message": f"No content found in collection '{collection_name}'.",
        }

    combined = "\n\n".join([f"[Page {c['page']}]\n{c['text']}" for c in chunks])
    prompt = (
        "Below are excerpts from a student's uploaded document. "
        "Write a clear 3-5 sentence summary of what this document is about, "
        "based ONLY on these excerpts.\n\n"
        f"EXCERPTS:\n{combined}"
    )

    response = _client.messages.create(
        model=_MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "status": "ok",
        "summary": response.content[0].text,
        "based_on_chunks": len(chunks),
    }


def generate_quiz(topic: str, num_questions: int = 3, difficulty: str = "medium") -> dict:
    """Generate a multiple-choice quiz."""
    prompt = f"""Generate a {difficulty}-difficulty multiple-choice quiz based on the following topic/context.

If the context below is a plain topic name, use your general knowledge.
If it contains specific excerpts from a document, base the questions ONLY on what's in those excerpts.

CONTEXT:
{topic}

Create exactly {num_questions} questions. Return ONLY valid JSON in this exact format,
with no other text before or after:

{{
  "topic": "brief topic summary",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "question": "the question text",
      "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
      "correct_answer": "A",
      "explanation": "brief explanation"
    }}
  ]
}}
"""

    response = _client.messages.create(
        model=_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    return json.loads(raw_text)


# ====================================================================
# TOOL IMPLEMENTATIONS — Mock Exam & Answer Evaluation
# ====================================================================

def create_mock_exam(
    topic: str,
    collection_name: str = "",
    num_questions: int = 20,
    difficulty: str = "medium",
    duration_minutes: int = 60,
) -> dict:
    """Generate a full timed practice exam with structured sections."""
    # If a collection is specified, enrich the topic with RAG context
    rag_context = ""
    if collection_name:
        chunks = search_documents(
            f"comprehensive overview of {topic}",
            collection_name,
            top_k=10,
        )
        if chunks:
            rag_context = "\n\n".join(
                [f"[Page {c['page']}]\n{c['text']}" for c in chunks]
            )

    context_block = rag_context if rag_context else topic
    time_per_question = max(1, round(duration_minutes / num_questions))

    prompt = f"""Generate a {difficulty}-difficulty timed practice exam based on the following context.

If the context contains specific document excerpts, base ALL questions ONLY on what's in those excerpts.
If the context is a general topic, use your general knowledge.

CONTEXT:
{context_block}

Create a realistic exam with exactly {num_questions} multiple-choice questions.
The exam should feel like a real university exam — varied question types (conceptual, analytical, application).

Duration: {duration_minutes} minutes (~{time_per_question} min per question).

Return ONLY valid JSON in this exact format, with no other text before or after:

{{
  "title": "descriptive exam title",
  "topic": "brief topic summary",
  "difficulty": "{difficulty}",
  "duration_minutes": {duration_minutes},
  "time_per_question_minutes": {time_per_question},
  "instructions": "exam instructions for the student",
  "total_questions": {num_questions},
  "questions": [
    {{
      "number": 1,
      "question": "the question text",
      "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
      "correct_answer": "A",
      "explanation": "brief explanation of why this is correct",
      "topic_tag": "specific sub-topic this question covers"
    }}
  ]
}}
"""

    response = _client.messages.create(
        model=_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    exam_data = json.loads(raw_text)
    exam_data["status"] = "ok"
    exam_data["rag_enriched"] = bool(rag_context)
    return exam_data


def evaluate_answer(
    question: str,
    student_answer: str,
    correct_answer: str,
    explanation: str = "",
) -> dict:
    """Grade a student's answer and provide detailed feedback."""
    explanation_block = f"\nEXPLANATION: {explanation}" if explanation else ""

    prompt = f"""You are an expert tutor grading a student's answer. Evaluate the answer strictly but fairly.

QUESTION:
{question}

CORRECT ANSWER:
{correct_answer}
{explanation_block}

STUDENT'S ANSWER:
{student_answer}

Evaluate the student's answer and return ONLY valid JSON in this exact format:

{{
  "is_correct": true or false,
  "score": 0 to 100,
  "correctness_label": "exactly_correct" OR "mostly_correct" OR "partially_correct" OR "incorrect",
  "feedback": "2-3 sentences of encouraging feedback",
  "what_the_student_got_right": "specific points the student understood correctly",
  "what_to_improve": "specific actionable advice for improvement",
  "key_concept": "the core concept this question tests"
}}

Scoring rubric:
- 90-100: Exactly correct or extremely close
- 70-89: Mostly correct, minor gaps
- 40-69: Partially correct, significant gaps but understood some concepts
- 0-39: Incorrect or fundamentally misunderstood

Be encouraging in feedback but honest about correctness."""

    response = _client.messages.create(
        model=_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    result = json.loads(raw_text)
    result["status"] = "ok"
    result["question_preview"] = question[:100] + "..." if len(question) > 100 else question
    return result


# ====================================================================
# TOOL IMPLEMENTATIONS — Adaptive engine (Step 9)
# ====================================================================

async def _log_confidence_async(user_id: str, topic: str, score: float) -> dict:
    """Persist a confidence rating to the database."""
    async with _ToolSession() as session:
        entry = ConfidenceLog(
            user_id=user_id,
            topic=topic.lower().strip(),  # normalize for grouping
            score=float(score),
        )
        session.add(entry)
        await session.commit()
        await session.refresh(entry)
        return {
            "status": "ok",
            "logged_id": entry.id,
            "topic": entry.topic,
            "score": entry.score,
        }


def log_confidence(user_id: str, topic: str, score: float) -> dict:
    """Sync wrapper around the async DB call."""
    import asyncio
    return asyncio.run(_log_confidence_async(user_id, topic, score))


async def _identify_weak_topics_async(user_id: str, limit: int = 5) -> dict:
    """Query the confidence_logs table for this user's weakest topics
    (by average score, lowest first)."""
    async with _ToolSession() as session:
        stmt = (
            select(ConfidenceLog)
            .where(ConfidenceLog.user_id == user_id)
            .order_by(desc(ConfidenceLog.created_at))
        )
        result = await session.execute(stmt)
        all_logs = result.scalars().all()

    if not all_logs:
        return {
            "status": "no_data",
            "message": "No confidence logs yet for this student. Suggest taking a quiz or rating some topics to build a learning profile.",
            "weak_topics": [],
        }

    # Compute average score per topic (using the most recent entries)
    by_topic: dict[str, list[float]] = {}
    for log in all_logs:
        by_topic.setdefault(log.topic, []).append(log.score)

    avg_per_topic = [
        {
            "topic": topic,
            "average_score": round(sum(scores) / len(scores), 2),
            "attempts": len(scores),
        }
        for topic, scores in by_topic.items()
    ]
    # Sort: lowest average first (weakest)
    avg_per_topic.sort(key=lambda x: x["average_score"])

    return {
        "status": "ok",
        "weak_topics": avg_per_topic[:limit],
        "total_topics_tracked": len(by_topic),
    }


def identify_weak_topics(user_id: str, limit: int = 5) -> dict:
    """Sync wrapper around the async DB call."""
    import asyncio
    return asyncio.run(_identify_weak_topics_async(user_id, limit))


def generate_revision_plan(
    exam_date_iso: str,
    topics: list[str],
    hours_per_day: float = 2.0,
) -> dict:
    """
    Build a day-by-day revision schedule.
    Strategy: assign topics round-robin across days, leaving the last 2 days
    as 'buffer' (mixed review + practice exam).
    """
    try:
        exam_date = datetime.fromisoformat(exam_date_iso).date()
    except ValueError:
        return {
            "status": "error",
            "message": f"Could not parse exam_date_iso '{exam_date_iso}'. Use YYYY-MM-DD.",
        }

    today = datetime.now(timezone.utc).date()
    days_until_exam = (exam_date - today).days

    if days_until_exam <= 0:
        return {
            "status": "error",
            "message": f"Exam date {exam_date_iso} is today or in the past. Cannot plan.",
        }

    if not topics:
        return {
            "status": "error",
            "message": "No topics provided. Call identify_weak_topics first, or ask the student for topics.",
        }

    # Reserve the last ≤2 days for buffer
    buffer_days = min(2, max(1, days_until_exam // 5))
    study_days = days_until_exam - buffer_days

    if study_days <= 0:
        # Very short window — just split everything across whatever days we have
        study_days = days_until_exam
        buffer_days = 0

    # Distribute topics across study days (round-robin)
    schedule = []
    for offset in range(study_days):
        day_date = today + timedelta(days=offset)
        # Each day gets ~ ceil(len(topics) / study_days) topics
        day_topics = topics[offset::study_days]
        if day_topics:
            schedule.append({
                "date": day_date.isoformat(),
                "day_label": f"Day {offset + 1}",
                "hours": hours_per_day,
                "focus_topics": day_topics,
                "activity": "Focused study + practice questions",
            })

    # Buffer days
    for offset in range(study_days, days_until_exam):
        day_date = today + timedelta(days=offset)
        schedule.append({
            "date": day_date.isoformat(),
            "day_label": f"Day {offset + 1} (Buffer)",
            "hours": hours_per_day,
            "focus_topics": topics,  # all topics, light review
            "activity": "Mixed review + mock exam",
        })

    return {
        "status": "ok",
        "exam_date": exam_date_iso,
        "days_until_exam": days_until_exam,
        "study_days": study_days,
        "buffer_days": buffer_days,
        "total_topics": len(topics),
        "schedule": schedule,
    }


# ====================================================================
# TOOL DISPATCHER
# ====================================================================

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Route a tool call from Claude to the right Python function."""
    if tool_name == "search_materials":
        return search_materials(**tool_input)
    if tool_name == "summarize_document":
        return summarize_document(**tool_input)
    if tool_name == "generate_quiz":
        return generate_quiz(**tool_input)
    if tool_name == "create_mock_exam":
        return create_mock_exam(**tool_input)
    if tool_name == "evaluate_answer":
        return evaluate_answer(**tool_input)
    if tool_name == "log_confidence":
        return log_confidence(**tool_input)
    if tool_name == "identify_weak_topics":
        return identify_weak_topics(**tool_input)
    if tool_name == "generate_revision_plan":
        return generate_revision_plan(**tool_input)
    raise ValueError(f"Unknown tool: {tool_name}")
