from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class DocumentPage:
    document_name: str
    page_number: int
    text: str


@dataclass(slots=True)
class DocumentChunk:
    chunk_id: str
    document_name: str
    page_number: int
    chunk_text: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RetrievedChunk:
    chunk: DocumentChunk
    score: float


@dataclass(slots=True)
class QueryResponse:
    answer: str
    sources: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {"answer": self.answer, "sources": self.sources}
