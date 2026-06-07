"""
SAGE - RAG retrieval.

Given a user's question, finds the most relevant chunks from a ChromaDB
collection so they can be injected into Claude's context.

Owner: Abrar (RAG)
"""

import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
Path(CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

# Same embedding model we used for ingestion. CRITICAL: this MUST match
# the model used during ingest, otherwise the vectors won't be comparable.
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")
Settings.llm = None


def search_documents(query: str, collection_name: str, top_k: int = 3) -> list[dict]:
    """
    Search a ChromaDB collection for the most relevant chunks to a query.

    Args:
        query: the student's question, e.g. "What is the role of NADPH?"
        collection_name: which collection to search (one per user/document set).
        top_k: how many chunks to return (default 3).

    Returns:
        A list of dicts, each with the chunk text and a similarity score.
        Most relevant first.
    """
    # Connect to ChromaDB
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Check the collection exists. If not, return empty (no documents ingested yet).
    try:
        chroma_collection = chroma_client.get_collection(collection_name)
    except Exception:
        print(f"  [retriever] No collection named '{collection_name}' yet.")
        return []

    # Rebuild the index object from the existing ChromaDB collection
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store=vector_store)

    # Run the semantic search.
    # The retriever embeds the query, computes similarity vs. all stored
    # chunks, and returns the top_k most similar ones.
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)

    # Package the results in a clean format
    results = []
    for node in nodes:
        results.append({
            "text": node.text,
            "score": float(node.score) if node.score is not None else None,
            "source": node.metadata.get("file_name", "unknown"),
            "page": node.metadata.get("page_label", "?"),
        })

    return results