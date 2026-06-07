"""
SAGE - Chat Pydantic schemas.

These models define the JSON shapes for the /chat API. FastAPI uses
them to (1) validate incoming requests, (2) generate the OpenAPI docs,
and (3) serialize responses.

Owner: Tanjid (Backend) - scaffolded by Abrar
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """The JSON body for POST /api/v1/chat."""

    user_id: str = Field(
        ...,
        description="The student's UUID. For now, passed directly; later replaced by JWT auth.",
        examples=["1670551a-ecef-449c-a63c-cce402570981"],
    )
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


class ChatResponse(BaseModel):
    """The JSON returned by POST /api/v1/chat."""

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