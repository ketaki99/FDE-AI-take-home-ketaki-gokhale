from __future__ import annotations

from pathlib import Path

import fitz

from .models import DocumentPage
from .utils import normalize_whitespace


def extract_pages_from_pdf(pdf_path: Path) -> list[DocumentPage]:
    pages: list[DocumentPage] = []

    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            text = normalize_whitespace(page.get_text("text"))
            if not text:
                continue
            pages.append(
                DocumentPage(
                    document_name=pdf_path.name,
                    page_number=page_index,
                    text=text,
                )
            )

    return pages


def extract_pages_from_folder(folder_path: Path) -> list[DocumentPage]:
    pages: list[DocumentPage] = []

    for pdf_path in sorted(folder_path.glob("*.pdf")):
        pages.extend(extract_pages_from_pdf(pdf_path))

    return pages
