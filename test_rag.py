"""
Test the full RAG pipeline end-to-end.

Steps:
  1. Ingest a PDF (one-time per document).
  2. Ask a question.
  3. Retrieve relevant chunks.
  4. Feed question + chunks to Claude as context.
  5. Print the grounded answer + citations.

Usage:
    1. Put a PDF in the ./uploads folder.
    2. Edit PDF_PATH and QUESTION below.
    3. Run: python test_rag.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from anthropic import Anthropic

from backend.rag.ingest import ingest_document
from backend.rag.retriever import search_documents

load_dotenv()

# ----------------------------------------------------------------------
# EDIT THESE LINES TO MATCH YOUR PDF AND YOUR QUESTION
# ----------------------------------------------------------------------
PDF_PATH = "uploads/lecture1.pdf"
QUESTION = "What is the Transformer architecture and why did the authors propose it?"
COLLECTION_NAME = "test_collection_5"

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
client = Anthropic()
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")


def main():
    # ── PHASE 1: INGEST (once per document) ─────────────────────────
    if not Path(PDF_PATH).exists():
        print(f"ERROR: PDF not found at '{PDF_PATH}'.")
        print(f"       Put a PDF in the uploads/ folder and edit PDF_PATH in this script.")
        return

    print("=" * 70)
    print("PHASE 1: INGESTION")
    print("=" * 70)
    result = ingest_document(PDF_PATH, COLLECTION_NAME)
    print(f"\nIngestion result: {result}\n")

    # ── PHASE 2: RETRIEVE ───────────────────────────────────────────
    print("=" * 70)
    print("PHASE 2: RETRIEVAL")
    print("=" * 70)
    print(f"Question: {QUESTION}\n")
    print("Searching for relevant chunks...")
    chunks = search_documents(QUESTION, COLLECTION_NAME, top_k=3)

    if not chunks:
        print("No chunks found. Ingestion may have failed.")
        return

    print(f"\nRetrieved {len(chunks)} chunks:\n")
    for i, chunk in enumerate(chunks, start=1):
        print(f"  [Chunk {i}] score={chunk['score']:.3f} | page={chunk['page']}")
        preview = chunk["text"][:150].replace("\n", " ")
        print(f"           preview: {preview}...")
        print()

    # ── PHASE 3: GENERATE GROUNDED ANSWER ──────────────────────────
    print("=" * 70)
    print("PHASE 3: GROUNDED GENERATION (Claude answers using retrieved context)")
    print("=" * 70)

    # Build a context block from the retrieved chunks
    context_block = "\n\n".join([
        f"[Excerpt {i+1}, page {c['page']}]\n{c['text']}"
        for i, c in enumerate(chunks)
    ])

    # Build the prompt: question + context, with explicit grounding instructions
    prompt = f"""Answer the student's question using ONLY the excerpts below.
If the answer isn't in the excerpts, say so clearly — do not invent information.
Cite which excerpt(s) support your answer (e.g. "According to Excerpt 2...").

QUESTION:
{QUESTION}

EXCERPTS:
{context_block}
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    print("\nClaude's grounded answer:\n")
    print(response.content[0].text)
    print()
    print("=" * 70)
    print("RAG pipeline complete. Notice how the answer is grounded in YOUR document,")
    print("not in Claude's training data. That's RAG.")
    print("=" * 70)


if __name__ == "__main__":
    main()