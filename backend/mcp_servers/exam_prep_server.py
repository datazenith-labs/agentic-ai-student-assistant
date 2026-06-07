"""
SAGE - Exam Prep MCP Server (Phase 2 - built FIRST).

This module defines tools that Claude can call to help students prepare for exams.
For now, only generate_quiz is implemented; more tools (search_materials,
generate_revision_plan, etc.) come in later steps.

These tools follow the MCP (Model Context Protocol) tool format so they can
later be served as a real MCP server. In this step we use them directly via
the Claude API.

Owner: Abrar (AI/MCP Lead)
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

# Claude client (used internally to generate quiz content)
_client = Anthropic()
_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


# ----------------------------------------------------------------------
# TOOL DEFINITIONS (MCP-style)
# Each tool has: a name, a description (Claude reads this to decide
# whether to call it), and an input_schema (what arguments it accepts).
# ----------------------------------------------------------------------

EXAM_PREP_TOOLS = [
    {
        "name": "generate_quiz",
        "description": (
            "Generate a multiple-choice quiz on a given academic topic. "
            "Use this whenever a student asks to be quizzed, tested, or wants "
            "practice questions on a subject."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The academic topic to quiz the student on, e.g. 'photosynthesis' or 'binary search trees'.",
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


# ----------------------------------------------------------------------
# TOOL IMPLEMENTATIONS
# These are the actual Python functions that run when Claude calls a tool.
# ----------------------------------------------------------------------

def generate_quiz(topic: str, num_questions: int = 3, difficulty: str = "medium") -> dict:
    """
    Generates a multiple-choice quiz on the given topic.
    Returns a structured dictionary with questions, options, and correct answers.
    """
    prompt = f"""Generate a {difficulty}-difficulty multiple-choice quiz on the topic: "{topic}".

Create exactly {num_questions} questions. Return ONLY valid JSON in this exact format,
with no other text before or after:

{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "question": "the question text",
      "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
      "correct_answer": "A",
      "explanation": "brief explanation of why this is correct"
    }}
  ]
}}
"""

    response = _client.messages.create(
        model=_MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )

    # Claude returns text; we parse it as JSON
    raw_text = response.content[0].text.strip()

    # Sometimes Claude wraps JSON in markdown code fences - strip them if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    quiz_data = json.loads(raw_text)
    return quiz_data


# ----------------------------------------------------------------------
# TOOL DISPATCHER
# Given a tool name and arguments, runs the matching function.
# This is what gets called when Claude says "I want to use this tool".
# ----------------------------------------------------------------------

def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Routes a tool call to the right implementation."""
    if tool_name == "generate_quiz":
        return generate_quiz(**tool_input)
    raise ValueError(f"Unknown tool: {tool_name}")