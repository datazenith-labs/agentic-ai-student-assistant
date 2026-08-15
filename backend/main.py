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
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1 import auth as auth_routes
from backend.database.connection import init_db

load_dotenv()


# ----------------------------------------------------------------------
# APP CREATION
# ----------------------------------------------------------------------

@asynccontextmanager
async def lifespan(_: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="SAGE - Agentic AI Student Assistant",
    description=(
        "Backend API for SAGE, a Student Academic Guidance Engine. "
        "Powered by Claude, MCP (Model Context Protocol), and RAG."
    ),
    version="0.1.0",
    lifespan=lifespan,
)


# ----------------------------------------------------------------------
# CORS - allows the Streamlit frontend (on a different port) to call us
# ----------------------------------------------------------------------

# Default to allowing both Streamlit (8501) and Next.js (3000) in development.
# Production should set the CORS_ORIGINS env var explicitly.
_DEFAULT_DEV_ORIGINS = "http://localhost:3000,http://localhost:8501"
cors_origins = os.getenv("CORS_ORIGINS", _DEFAULT_DEV_ORIGINS).split(",")

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

app.include_router(auth_routes.router, prefix="/api/v1")

# Auth-only mode lets contributors test accounts without API keys or the
# heavyweight RAG model dependencies. Chat and uploads are intentionally absent.
AUTH_ONLY_MODE = os.getenv("AUTH_ONLY_MODE", "false").lower() == "true"
if not AUTH_ONLY_MODE:
    from backend.api.v1 import chat as chat_routes
    from backend.api.v1 import documents as documents_routes

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
