"""
SAGE - RAG document ingestion pipeline.

Pipeline: PDF -> extract text -> chunk -> embed -> store in ChromaDB.

We use:
  - pypdf for PDF text extraction (proven to work on this system).
  - HuggingFace's all-MiniLM-L6-v2 for local, free embeddings.
  - ChromaDB as the persistent vector store (a local folder, no server).

Owner: Abrar (RAG)
"""

import os
from pathlib import Path

import chromadb
import pypdf
from dotenv import load_dotenv
from llama_index.core import (
    Document,
    Settings,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()

# ----------------------------------------------------------------------
# CONFIGURATION
# ----------------------------------------------------------------------

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")

Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
Settings.llm = None


# ----------------------------------------------------------------------
# HELPER: Extract text from PDF with pypdf
# ----------------------------------------------------------------------

def _read_pdf_with_pypdf(file_path: Path) -> list[Document]:
    """Use pypdf directly — this is what proved to work in our diagnostic test."""
    reader = pypdf.PdfReader(str(file_path))
    documents = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            documents.append(Document(
                text=text,
                metadata={"page_label": str(i + 1), "file_name": file_path.name},
            ))
    return documents


# ----------------------------------------------------------------------
# INGESTION FUNCTION
# ----------------------------------------------------------------------

def ingest_document(file_path: str, collection_name: str) -> dict:
    """
    Ingest a single document into ChromaDB.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    print(f"Ingesting: {file_path.name}")
    print(f"  Collection: {collection_name}")

    # Step 1: Read the document with pypdf (proven to work on this system)
    print("  [1/4] Reading and extracting text with pypdf...")
    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Only PDF files supported for now. Got: {file_path.suffix}")

    documents = _read_pdf_with_pypdf(file_path)
    print(f"        Extracted {len(documents)} pages of readable text")

    if not documents:
        raise RuntimeError("No readable text extracted from PDF. File may be image-only or encrypted.")

    # Show a preview to confirm we got real text
    preview = documents[0].text[:200].replace("\n", " ")
    print(f"        Preview: {preview}...")

    # Step 2: Connect to ChromaDB
    print("  [2/4] Connecting to ChromaDB...")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    chroma_collection = chroma_client.get_or_create_collection(collection_name)

    # Step 3: Build the vector store
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Step 4: Chunk, embed, store
    print("  [3/4] Chunking and embedding...")
    VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        show_progress=True,
    )

    chunk_count = chroma_collection.count()
    print(f"  [4/4] Done. Collection now has {chunk_count} chunks total.")

    return {
        "filename": file_path.name,
        "collection_name": collection_name,
        "chunk_count": chunk_count,
        "status": "ready",
    }