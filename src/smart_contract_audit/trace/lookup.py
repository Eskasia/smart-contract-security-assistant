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


def trace_dashboard(db_path: Path) -> list[dict[str, Any]]:
    query = """
        SELECT
            analysis_trace.trace_id,
            analysis_trace.contract_id,
            analysis_trace.created_at,
            analysis_trace.dataset_version,
            analysis_trace.model_version,
            analysis_trace.solc_version,
            analysis_trace.slither_version,
            analysis_trace.review_status,
            analysis_trace.final_status,
            analysis_trace.total_duration_ms,
            COUNT(trace_findings.finding_id) AS finding_rows
        FROM analysis_trace
        LEFT JOIN trace_findings
            ON analysis_trace.trace_id = trace_findings.trace_id
        GROUP BY analysis_trace.trace_id
        ORDER BY analysis_trace.created_at DESC
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query).fetchall()
        return [dict(row) for row in rows]
