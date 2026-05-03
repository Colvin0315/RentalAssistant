from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from .config import INDEX_DIR, PARSED_DIR, UPLOAD_DIR, ensure_directories


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def save_upload(document_id: str, upload: UploadFile) -> Path:
    ensure_directories()
    suffix = Path(upload.filename or "upload.bin").suffix
    target = UPLOAD_DIR / f"{document_id}{suffix}"
    with target.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    return target


def parsed_path(document_id: str) -> Path:
    return PARSED_DIR / f"{document_id}.json"


def index_path(document_id: str) -> Path:
    return INDEX_DIR / f"{document_id}.json"


def faiss_index_path(document_id: str) -> Path:
    return INDEX_DIR / f"{document_id}.faiss"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
