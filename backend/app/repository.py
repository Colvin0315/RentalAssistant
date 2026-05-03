from __future__ import annotations

import json
from typing import Any

from .db import get_conn, utc_now


def insert_document(
    document_id: str,
    filename: str,
    document_type: str,
    stored_path: str,
    status: str,
) -> None:
    now = utc_now()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO documents(document_id, filename, document_type, stored_path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (document_id, filename, document_type, stored_path, status, now, now),
        )


def update_document_status(document_id: str, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE documents SET status = ?, updated_at = ? WHERE document_id = ?",
            (status, utc_now(), document_id),
        )


def get_document(document_id: str) -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM documents WHERE document_id = ?",
            (document_id,),
        ).fetchone()
    return dict(row) if row else None


def insert_session(session_id: str, document_id: str, question: str, answer: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO sessions(session_id, document_id, question, answer, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, document_id, question, answer, utc_now()),
        )


def insert_session_event(session_id: str, event_type: str, payload: dict[str, Any]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO session_events(session_id, type, payload, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, event_type, json.dumps(payload, ensure_ascii=False), utc_now()),
        )


def get_session_events(session_id: str) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT type, payload
            FROM session_events
            WHERE session_id = ?
            ORDER BY id ASC
            """,
            (session_id,),
        ).fetchall()
    return [{"type": row["type"], "data": json.loads(row["payload"])} for row in rows]
