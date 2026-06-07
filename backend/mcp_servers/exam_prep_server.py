"""
SAGE - Exam Prep MCP Server (Phase 2 - the technical centerpiece).

This module defines the tools Claude can call to help students prepare for exams.
Each tool follows the MCP (Model Context Protocol) format so they can later be
exposed as a standalone MCP server. For now we attach them directly to the
Claude API via the `tools` parameter.

Available tools:
  - search_materials      : RAG search over the student's uploaded documents.
  - summarize_document    : Returns a summary of an entire uploaded document.
  - generate_quiz         : Generates a multiple-choice quiz. Can be grounded
                            in the student's documents if a collection is given.

Owner: Abrar (AI/MCP Lead)
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

# Pull in our RAG retriever - this is the bridge between MCP and RAG
from backend.rag.retriever import search_documents

load_dotenv()

_client = Anthropic()
_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


# ====================================================================
# TOOL DEFINITIONS (the "menu" Claude reads to decide what to call)
# ====================================================================

EXAM_PREP_TOOLS = [
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
                    "description": "The student's document collection name. For now, always use 'test_collection_5'.",
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
                    "description": "The student's document collection name. For now, always use 'test_collection_5'.",
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
]


# ====================================================================
# TOOL IMPLEMENTATIONS
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
    # Pull a wide sample of chunks across the document (using a generic query gets a spread)
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

    # Combine the chunks into a single text block
    combined = "\n\n".join([f"[Page {c['page']}]\n{c['text']}" for c in chunks])

    # Ask Claude to summarize
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
    """Generate a multiple-choice quiz. `topic` can be a plain topic OR retrieved doc excerpts."""
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

    # Strip markdown code fences if Claude added them
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    quiz_data = json.loads(raw_text)
    return quiz_data


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
    raise ValueError(f"Unknown tool: {tool_name}")