from __future__ import annotations

import os

from dotenv import load_dotenv
from fastmcp import FastMCP

from .embeddings import EmbeddingModel
from .qa import create_answer_generator
from .retriever import LocalVectorStore
from .utils import METADATA_PATH, load_json

load_dotenv()

mcp = FastMCP("local-pdf-qa")

_embedding_model = EmbeddingModel(
    os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
)
_store = LocalVectorStore(_embedding_model)
_answer_generator = create_answer_generator()
_top_k = int(os.getenv("TOP_K", "5"))
_min_score = float(os.getenv("MIN_SCORE", "0.35"))


def _ensure_store_loaded() -> None:
    if _store.index is None:
        _store.load()


@mcp.tool()
def query_documents(question: str) -> dict[str, object]:
    """Answer a question using only the indexed PDFs and include citations."""
    _ensure_store_loaded()
    retrieved_chunks = [
        item for item in _store.search(question=question, top_k=_top_k) if item.score >= _min_score
    ]
    response = _answer_generator.answer(question=question, retrieved_chunks=retrieved_chunks)
    return response.to_dict()


@mcp.tool()
def list_documents() -> dict[str, list[str]]:
    """List the PDF files currently represented in the local index."""
    if not METADATA_PATH.exists():
        return {"documents": []}

    metadata = load_json(METADATA_PATH)
    documents = sorted({item["document_name"] for item in metadata})
    return {"documents": documents}


if __name__ == "__main__":
    mcp.run()
