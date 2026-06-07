"""
Test: prove Claude can use our MCP tools agentically.

We send Claude a natural-language request and provide our tools.
Claude decides on its own which tool to call (if any), with what arguments.
We execute the tool and feed the result back, and Claude composes a final reply.

Run with:  python test_mcp.py
"""

import json
import os

from dotenv import load_dotenv
from anthropic import Anthropic

from backend.mcp_servers.exam_prep_server import EXAM_PREP_TOOLS, execute_tool

load_dotenv()

client = Anthropic()
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

# The student's natural-language request.
# Notice: we do NOT mention "generate_quiz" - Claude figures it out.
USER_MESSAGE = "Hey, can you quiz me on the basics of photosynthesis? Just 2 questions please."


def run_agentic_loop():
    print("=" * 60)
    print(f"Student says: {USER_MESSAGE}")
    print("=" * 60)
    print()

    # Conversation starts with the student's message
    messages = [{"role": "user", "content": USER_MESSAGE}]

    # We loop because Claude might use a tool, get a result,
    # then decide to use another tool, etc. (here: only one round needed).
    while True:
        print("--> Calling Claude with tools available...")
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            tools=EXAM_PREP_TOOLS,
            messages=messages,
        )

        print(f"<-- Claude's stop reason: {response.stop_reason}")
        print()

        # Case 1: Claude wants to call a tool
        if response.stop_reason == "tool_use":
            # Save Claude's full response (including its decision to use the tool) to history
            messages.append({"role": "assistant", "content": response.content})

            # There might be multiple tool calls; handle each
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  Claude decided to call: {block.name}")
                    print(f"  With input: {json.dumps(block.input, indent=2)}")
                    print()

                    # Run the tool
                    result = execute_tool(block.name, block.input)

                    print(f"  Tool returned (preview):")
                    print(f"  {json.dumps(result, indent=2)[:400]}...")
                    print()

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })

            # Send tool results back to Claude so it can form a final answer
            messages.append({"role": "user", "content": tool_results})
            continue  # loop again to get Claude's next response

        # Case 2: Claude is done - it has a final text answer for the student
        if response.stop_reason == "end_turn":
            print("=" * 60)
            print("Claude's final answer to the student:")
            print("=" * 60)
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            break

        # Anything else - shouldn't happen in this simple test
        print(f"Unexpected stop reason: {response.stop_reason}")
        break


if __name__ == "__main__":
    run_agentic_loop()