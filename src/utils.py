from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PDFS_DIR = PROJECT_ROOT / "pdfs"
DATA_DIR = PROJECT_ROOT / "data"
INDEX_PATH = DATA_DIR / "vector.index"
METADATA_PATH = DATA_DIR / "chunks.json"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split()).strip()
