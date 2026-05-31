"""
SAGE — Assistant Client (the brain).

This is the core orchestration loop:
  1. Load conversation history
  2. Call Claude with the available MCP tools attached
  3. If Claude wants to use a tool, execute it and return the result
  4. Repeat until Claude produces a final answer
  5. Return the response

This ~60-line loop replaces what would otherwise require a heavy
orchestration framework (LangGraph / CrewAI). Claude itself decides
which tools to call.

Owner: Abrar (AI/MCP Lead)
Status: PLACEHOLDER — to be implemented in Step 7.
"""
