"""
SAGE — FastAPI application entry point.

This is the main backend server. It wires together all API routes,
configures CORS, and starts the application.

Status: PLACEHOLDER — to be implemented in Step 3.
"""

from fastapi import FastAPI

app = FastAPI(title="SAGE — Agentic AI Student Assistant")


@app.get("/")
async def root():
    """Health check endpoint. Confirms the server is running."""
    return {"status": "ok", "message": "SAGE backend is running"}
