from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def lookup_trace(
    db_path: Path, trace_id: str, finding_id: str | None = None
) -> list[dict[str, Any]]:
    query = "SELECT * FROM trace_findings WHERE trace_id = ?"
    params: list[str] = [trace_id]
    if finding_id:
        query += " AND finding_id = ?"
        params.append(finding_id)

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]
