from __future__ import annotations

import os
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BACKEND_ROOT.parents[0]
STORAGE_ROOT = PROJECT_ROOT / "storage"
UPLOAD_DIR = STORAGE_ROOT / "uploads"
PARSED_DIR = STORAGE_ROOT / "parsed"
INDEX_DIR = STORAGE_ROOT / "indexes"
LOG_DIR = STORAGE_ROOT / "logs"
DB_PATH = STORAGE_ROOT / "rentguard.db"

API_PREFIX = "/api/v1"

VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "384"))
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_TIMEOUT = float(os.getenv("DEEPSEEK_TIMEOUT", "30"))
TESSERACT_CMD = os.getenv("TESSERACT_CMD", "")


def ensure_directories() -> None:
    for path in (STORAGE_ROOT, UPLOAD_DIR, PARSED_DIR, INDEX_DIR, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
