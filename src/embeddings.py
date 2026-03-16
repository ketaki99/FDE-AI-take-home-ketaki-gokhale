from __future__ import annotations

import numpy as np
from sentence_transformers import SentenceTransformer

from .models import DocumentChunk


class EmbeddingModel:
    def __init__(self, model_name: str) -> None:
        self._model = SentenceTransformer(model_name)

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        embeddings = self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.astype("float32")

    def embed_chunks(self, chunks: list[DocumentChunk]) -> np.ndarray:
        return self.embed_texts([chunk.chunk_text for chunk in chunks])
