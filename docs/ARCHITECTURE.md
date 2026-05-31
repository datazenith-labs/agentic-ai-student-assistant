# SAGE — Architecture Notes

This document explains the system design for the team and for the
project defense. (Detailed content lives in the main project spec.)

## The Core Idea
Claude is the orchestrator. We expose tools via MCP; Claude decides
what to call. No custom routing framework needed.

## Layers
1. Streamlit frontend (Minhazul)
2. FastAPI backend (Tanjid)
3. Assistant client — Claude + MCP loop (Abrar)
4. MCP tool servers — exam_prep / advisor / campus (Abrar)
5. Shared foundation — RAG, database, Claude wrapper

(To be expanded as we build.)
