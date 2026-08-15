"""
SAGE - Document upload endpoint.

POST /api/v1/documents/upload
    Accepts a PDF file, saves it, runs RAG ingestion, registers it
    in the database, and returns the collection name so the frontend
    can route subsequent chat queries to it.

Owner: Tanjid (Backend) + Abrar (RAG glue)
"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.connection import get_session
from backend.database.models import Document, User
from backend.dependencies import get_current_user
from backend.rag.ingest import ingest_document

router = APIRouter(prefix="/documents", tags=["documents"])

# Where uploaded files land on disk
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post(
    "/upload",
    summary="Upload a PDF and ingest it for RAG",
    description=(
        "Accepts a PDF file, saves it to the uploads folder, chunks and embeds "
        "it into a ChromaDB collection unique to this user+document, registers "
        "it in the documents table, and returns the document_id and "
        "collection_name so the frontend can use them in subsequent chat queries."
    ),
)
async def upload_document(
    file: UploadFile = File(..., description="The PDF file to ingest"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Accept a PDF upload, ingest it, and return the resulting collection name.
    """
    # Basic validation
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided.",
        )

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only PDF files are supported. Got: {file.filename}",
        )

    # 1. Create a database row in 'processing' state up front
    document = Document(
        user_id=current_user.id,
        filename=file.filename,
        status="processing",
        collection_name="",  # filled in after ingestion
    )
    db.add(document)
    await db.commit()
    await db.refresh(document)

    # 2. Save the uploaded file to disk under a safe, unique filename
    safe_name = f"{document.id}_{file.filename}"
    file_path = UPLOAD_DIR / safe_name

    try:
        file_bytes = await file.read()
        file_path.write_bytes(file_bytes)
    except Exception as exc:
        document.status = "failed"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {exc}",
        )

    # 3. Ingest into ChromaDB. Each user+document gets its own collection.
    collection_name = f"user_{current_user.id.replace('-', '')}_doc_{document.id.replace('-', '')}"

    try:
        result = ingest_document(str(file_path), collection_name)
    except Exception as exc:
        document.status = "failed"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion failed: {type(exc).__name__}: {exc}",
        )

    # 4. Update the database row to 'ready'
    document.status = "ready"
    document.collection_name = collection_name
    await db.commit()

    return {
        "document_id": document.id,
        "filename": file.filename,
        "collection_name": collection_name,
        "chunk_count": result["chunk_count"],
        "status": "ready",
    }


@router.get("", summary="List the authenticated user's documents")
async def list_documents(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    result = await db.scalars(
        select(Document).where(Document.user_id == current_user.id).order_by(Document.uploaded_at.desc())
    )
    return [
        {
            "document_id": doc.id,
            "filename": doc.filename,
            "status": doc.status,
            "collection_name": doc.collection_name,
            "uploaded_at": doc.uploaded_at,
        }
        for doc in result.all()
    ]
