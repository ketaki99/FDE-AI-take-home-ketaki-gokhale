from __future__ import annotations

import hashlib

from .models import DocumentChunk, DocumentPage


def chunk_pages(
    pages: list[DocumentPage],
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    chunks: list[DocumentChunk] = []

    for page in pages:
        text = page.text
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunk_id = build_chunk_id(page.document_name, page.page_number, start, chunk_text)
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_name=page.document_name,
                        page_number=page.page_number,
                        chunk_text=chunk_text,
                    )
                )

            if end >= len(text):
                break
            start = max(end - chunk_overlap, start + 1)

    return chunks


def build_chunk_id(document_name: str, page_number: int, offset: int, text: str) -> str:
    fingerprint = hashlib.md5(text.encode("utf-8")).hexdigest()[:8]
    return f"{document_name}-p{page_number}-o{offset}-{fingerprint}"
