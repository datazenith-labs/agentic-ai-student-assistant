"""
SAGE - FastAPI application entry point.

This is the main backend server. It:
  - Creates the FastAPI app
  - Configures CORS so the Streamlit frontend can call it
  - Registers all API routes (/chat and /documents)
  - Exposes a root health-check endpoint

Run with:
    uvicorn backend.main:app --reload --port 8000

Then open http://localhost:8000/docs for interactive API docs.

Owner: Tanjid (Backend) - scaffolded by Abrar
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1 import chat as chat_routes
from backend.api.v1 import documents as documents_routes

load_dotenv()


# ----------------------------------------------------------------------
# APP CREATION
# ----------------------------------------------------------------------

app = FastAPI(
    title="SAGE - Agentic AI Student Assistant",
    description=(
        "Backend API for SAGE, a Student Academic Guidance Engine. "
        "Powered by Claude, MCP (Model Context Protocol), and RAG."
    ),
    version="0.1.0",
)


# ----------------------------------------------------------------------
# CORS - allows the Streamlit frontend (on a different port) to call us
# ----------------------------------------------------------------------

cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8501").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------------------------------------------------
# ROUTES
# ----------------------------------------------------------------------

# Register routers under /api/v1
# Full paths become:
#   POST /api/v1/chat
#   POST /api/v1/documents/upload
app.include_router(chat_routes.router, prefix="/api/v1")
app.include_router(documents_routes.router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def root():
    """Health check. Confirms the server is running."""
    return {
        "status": "ok",
        "service": "SAGE",
        "version": "0.1.0",
        "docs": "/docs",
    }