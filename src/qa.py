from __future__ import annotations

import os
from collections import OrderedDict

from openai import OpenAI

from .models import QueryResponse, RetrievedChunk


class AnswerGenerator:
    def answer(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> QueryResponse:
        raise NotImplementedError


class ExtractiveAnswerGenerator(AnswerGenerator):
    def answer(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> QueryResponse:
        if not retrieved_chunks:
            return QueryResponse(
                answer="I could not find support for that question in the indexed documents.",
                sources=[],
            )

        sources = build_sources(retrieved_chunks)
        top_snippets = [item.chunk.chunk_text.strip() for item in retrieved_chunks[:3]]
        answer = "\n\n".join(top_snippets)
        return QueryResponse(answer=answer, sources=sources)


class OpenAIAnswerGenerator(AnswerGenerator):
    def __init__(self, model: str, base_url: str | None = None) -> None:
        self.client = OpenAI(base_url=base_url) if base_url else OpenAI()
        self.model = model

    def answer(self, question: str, retrieved_chunks: list[RetrievedChunk]) -> QueryResponse:
        if not retrieved_chunks:
            return QueryResponse(
                answer="I could not find support for that question in the indexed documents.",
                sources=[],
            )

        sources = build_sources(retrieved_chunks)
        context = "\n\n".join(
            f"[{idx}] {item.chunk.document_name} page {item.chunk.page_number}: {item.chunk.chunk_text.strip()}"
            for idx, item in enumerate(retrieved_chunks, start=1)
        )
        prompt = (
            "Answer the question using only the context below. "
            "If the context does not support the answer, say so clearly. "
            "Respond with a direct answer only. "
            "Do not ask follow-up questions. "
            "Do not add closing remarks.\n\n"
            f"Question: {question}\n\n"
            f"Context:\n{context}"
        )
        response = self.client.responses.create(
            model=self.model,
            input=prompt,
            temperature=0,
        )
        return QueryResponse(answer=response.output_text, sources=sources)


def create_answer_generator() -> AnswerGenerator:
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return OpenAIAnswerGenerator(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            base_url=os.getenv("OPENAI_BASE_URL"),
        )
    return ExtractiveAnswerGenerator()


def build_sources(retrieved_chunks: list[RetrievedChunk]) -> list[dict[str, object]]:
    deduped: OrderedDict[tuple[str, int], dict[str, object]] = OrderedDict()

    for item in retrieved_chunks:
        key = (item.chunk.document_name, item.chunk.page_number)
        deduped[key] = {
            "document": item.chunk.document_name,
            "page": item.chunk.page_number,
        }

    return list(deduped.values())
