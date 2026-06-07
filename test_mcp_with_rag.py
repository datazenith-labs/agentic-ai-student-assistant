"""
Test: Claude orchestrating MCP tools that use RAG.

We send three different student messages and watch Claude decide which
tools to call (and in what order) for each one. The student's "uploaded
document" is the Transformer paper we ingested in Step 5
(collection: test_collection_5).

Run with:  python test_mcp_with_rag.py
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from backend.mcp_servers.exam_prep_server import EXAM_PREP_TOOLS, execute_tool

load_dotenv()

client = Anthropic()
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

# A small system prompt tells Claude the student has uploaded materials
SYSTEM_PROMPT = (
    "You are SAGE, an AI study assistant. "
    "The student has uploaded a document; their collection name is 'test_collection_5'. "
    "Use the available tools when relevant to the student's question. "
    "When the student references their own materials, ALWAYS call search_materials first."
)

# Three test scenarios, each requiring different tool orchestration
TEST_MESSAGES = [
    {
        "label": "TEST 1: A document-grounded question (should call search_materials)",
        "message": "What does my uploaded document say about positional encoding?",
    },
    {
        "label": "TEST 2: A summary request (should call summarize_document)",
        "message": "Can you summarize the document I uploaded?",
    },
    {
        "label": "TEST 3: A document-grounded quiz (should call search_materials THEN generate_quiz)",
        "message": "Quiz me with 2 questions on multi-head attention based on my notes.",
    },
]


def run_agentic_loop(user_message: str):
    """Run the full Claude+MCP loop for a single user message."""
    messages = [{"role": "user", "content": user_message}]
    tools_called = []  # for reporting at the end

    iteration = 0
    while True:
        iteration += 1
        print(f"\n  [iteration {iteration}] Calling Claude...")
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=EXAM_PREP_TOOLS,
            messages=messages,
        )
        print(f"  [iteration {iteration}] stop_reason: {response.stop_reason}")

        # Case 1: Claude wants to use a tool
        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"\n  --> Claude called: {block.name}")
                    print(f"      With input: {json.dumps(block.input, indent=6)[:300]}")
                    tools_called.append(block.name)

                    # Execute the tool
                    result = execute_tool(block.name, block.input)
                    result_str = json.dumps(result)

                    # Show a preview of what the tool returned
                    preview = result_str[:250].replace("\n", " ")
                    print(f"      Result preview: {preview}...")

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_str,
                    })

            messages.append({"role": "user", "content": tool_results})
            continue  # loop back for Claude's next decision

        # Case 2: Claude is done
        if response.stop_reason == "end_turn":
            final_text = ""
            for block in response.content:
                if block.type == "text":
                    final_text += block.text
            return final_text, tools_called

        print(f"  Unexpected stop reason: {response.stop_reason}")
        return "", tools_called


def main():
    for test in TEST_MESSAGES:
        print("\n" + "=" * 75)
        print(test["label"])
        print("=" * 75)
        print(f"Student says: {test['message']}")

        final_answer, tools_called = run_agentic_loop(test["message"])

        print("\n  Tools Claude chose to call:", tools_called or "(none)")
        print("\n  Claude's final answer to the student:")
        print("  " + "-" * 60)
        # Indent each line of the answer for readability
        for line in final_answer.split("\n"):
            print(f"  {line}")
        print("  " + "-" * 60)

    print("\n" + "=" * 75)
    print("All three tests complete.")
    print("Notice how Claude chose DIFFERENT tools for each question,")
    print("based only on the tool descriptions - no manual routing.")
    print("That's agentic AI + MCP + RAG working together.")
    print("=" * 75)


if __name__ == "__main__":
    main()