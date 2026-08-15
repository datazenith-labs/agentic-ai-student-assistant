"""
SAGE - Chat Pydantic schemas.
These models define the JSON shapes for the /chat API. FastAPI uses
them to (1) validate incoming requests, (2) generate the OpenAPI docs,
and (3) serialize responses.

Owner: Tanjid (Backend) - scaffolded by Abrar
"""

from pydantic import BaseModel, Field


# ----------------------------------------------------------------------
# REQUEST + BLOCKING RESPONSE — for POST /api/v1/chat
# ----------------------------------------------------------------------


class ChatRequest(BaseModel):
    """The JSON body for POST /api/v1/chat (and /api/v1/chat/stream)."""

    session_id: str = Field(
        ...,
        description="The chat session (conversation thread) UUID.",
        examples=["5285610b-69a5-4efa-9e57-fb2678ce4808"],
    )
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The student's message.",
        examples=["What does my document say about positional encoding?"],
    )
    collection_name: str | None = Field(
        default=None,
        description=(
            "The ChromaDB collection name for the student's active uploaded document. "
            "Optional - if omitted, Claude will note that no documents are loaded."
        ),
        examples=["user_1670551a_doc_abc123"],
    )


class ChatResponse(BaseModel):
    """The JSON returned by POST /api/v1/chat (blocking endpoint only)."""

    reply: str = Field(
        ...,
        description="Claude's final text response to the student.",
    )
    tools_used: list[str] = Field(
        default_factory=list,
        description="Names of MCP tools Claude called during this turn.",
    )
    iterations: int = Field(
        ...,
        description="How many round-trips with Claude this turn took.",
    )


# ----------------------------------------------------------------------
# SSE EVENTS — for POST /api/v1/chat/stream
# ----------------------------------------------------------------------
#
# Each event the streaming endpoint emits is one of these types,
# serialized to JSON and prefixed with `data: ` per the SSE spec.
# Event order during a typical turn:
#
#   1. `token` events (many) — incremental text from Claude
#   2. `tool_start` event — if Claude calls an MCP tool mid-stream
#   3. `tool_end` event — when the tool result is back
#   4. (back to `token` events for the post-tool response)
#   5. `done` event — final, signals stream end
#
# Or, if anything goes wrong:
#   * `error` event — single event, stream then closes
#
# The `type` discriminator lets the frontend dispatch on event type
# in a switch / if-else, similar to Redux actions.


class TokenEvent(BaseModel):
    """A chunk of streamed text from Claude. Many of these per turn."""

    type: str = Field(default="token", description="Event discriminator.")
    text: str = Field(..., description="Text chunk to append to assistant message.")


class ToolStartEvent(BaseModel):
    """Emitted when Claude begins calling an MCP tool."""

    type: str = Field(default="tool_start", description="Event discriminator.")
    id: str = Field(..., description="Anthropic tool_use_id; links start to end.")
    name: str = Field(..., description="Tool name, e.g. 'list_upcoming_deadlines'.")
    input: dict = Field(default_factory=dict, description="Tool arguments Claude chose.")


class ToolEndEvent(BaseModel):
    """Emitted when the MCP tool result is back and Claude can resume."""

    type: str = Field(default="tool_end", description="Event discriminator.")
    id: str = Field(..., description="Matches the corresponding tool_start id.")
    status: str = Field(
        ...,
        description="'ok' on success, 'error' on tool failure.",
        examples=["ok", "error"],
    )


class DoneEvent(BaseModel):
    """Final event of a successful stream. Signals the frontend to stop reading."""

    type: str = Field(default="done", description="Event discriminator.")
    iterations: int = Field(..., description="How many Claude calls this turn took.")
    tools_used: list[str] = Field(
        default_factory=list,
        description="Names of all MCP tools Claude invoked during this turn.",
    )


class ErrorEvent(BaseModel):
    """Emitted on any backend or Claude API error. Stream closes after this."""

    type: str = Field(default="error", description="Event discriminator.")
    message: str = Field(..., description="Human-readable error description.")
