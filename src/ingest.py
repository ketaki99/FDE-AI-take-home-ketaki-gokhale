from __future__ import annotations

import os

from dotenv import load_dotenv

from .chunking import chunk_pages
from .embeddings import EmbeddingModel
from .parser import extract_pages_from_folder
from .retriever import LocalVectorStore
from .utils import PDFS_DIR


def build_index() -> dict[str, int]:
    load_dotenv()

    chunk_size = int(os.getenv("CHUNK_SIZE", "800"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "120"))
    embedding_model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

    pages = extract_pages_from_folder(PDFS_DIR)
    chunks = chunk_pages(pages, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    store = LocalVectorStore(EmbeddingModel(embedding_model_name))
    store.build(chunks)
    store.save()

    return {
        "documents_indexed": len({page.document_name for page in pages}),
        "pages_indexed": len(pages),
        "chunks_indexed": len(chunks),
    }


if __name__ == "__main__":
    stats = build_index()
    print("Index built successfully.")
    for key, value in stats.items():
        print(f"{key}: {value}")
