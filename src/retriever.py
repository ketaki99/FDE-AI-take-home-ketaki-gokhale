from __future__ import annotations

from pathlib import Path

import faiss
import numpy as np

from .embeddings import EmbeddingModel
from .models import DocumentChunk, RetrievedChunk
from .utils import INDEX_PATH, METADATA_PATH, ensure_data_dir, load_json, save_json


class LocalVectorStore:
    def __init__(self, embedding_model: EmbeddingModel) -> None:
        self.embedding_model = embedding_model
        self.index: faiss.IndexFlatIP | None = None
        self.chunks: list[DocumentChunk] = []

    def build(self, chunks: list[DocumentChunk]) -> None:
        if not chunks:
            raise ValueError("No chunks were produced from the PDF folder.")

        vectors = self.embedding_model.embed_chunks(chunks)
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)

        self.index = index
        self.chunks = chunks

    def save(self, index_path: Path = INDEX_PATH, metadata_path: Path = METADATA_PATH) -> None:
        if self.index is None:
            raise ValueError("Cannot save an empty vector index.")

        ensure_data_dir()
        faiss.write_index(self.index, str(index_path))
        save_json(metadata_path, [chunk.to_dict() for chunk in self.chunks])

    def load(self, index_path: Path = INDEX_PATH, metadata_path: Path = METADATA_PATH) -> None:
        if not index_path.exists() or not metadata_path.exists():
            raise FileNotFoundError("Vector index not found. Run ingestion first.")

        self.index = faiss.read_index(str(index_path))
        self.chunks = [DocumentChunk(**item) for item in load_json(metadata_path)]

    def search(self, question: str, top_k: int) -> list[RetrievedChunk]:
        if self.index is None:
            raise ValueError("Vector store is not loaded.")

        query_vector = self.embedding_model.embed_texts([question])
        scores, indices = self.index.search(query_vector, top_k)

        results: list[RetrievedChunk] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append(RetrievedChunk(chunk=self.chunks[idx], score=float(score)))

        return results
