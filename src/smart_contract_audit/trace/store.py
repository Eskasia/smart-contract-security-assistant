from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any


class TraceStore:
    def __init__(self, path: Path):
        self.path = path
        self.conn: sqlite3.Connection | None = None

    def __enter__(self) -> TraceStore:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.init_schema()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn is not None:
            self.conn.close()

    def init_schema(self) -> None:
        assert self.conn is not None
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS analysis_trace (
                trace_id TEXT PRIMARY KEY,
                contract_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                solc_version TEXT,
                slither_version TEXT,
                model_version TEXT,
                dataset_version TEXT,
                initial_rag_mode TEXT,
                final_status TEXT,
                total_duration_ms INTEGER
            );

            CREATE TABLE IF NOT EXISTS trace_findings (
                trace_id TEXT REFERENCES analysis_trace(trace_id),
                finding_id TEXT NOT NULL,
                detector_name TEXT,
                rag_mode TEXT,
                retrieval_duration_ms INTEGER,
                llm_duration_ms INTEGER,
                chunks_used INTEGER,
                slither_raw TEXT,
                normalized_finding TEXT,
                rag_chunk_ids TEXT,
                packed_prompt TEXT,
                llm_raw_output TEXT,
                schema_valid BOOLEAN,
                retry_count INTEGER DEFAULT 0,
                partial BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (trace_id, finding_id)
            );
            """
        )
        self.conn.commit()

    def create_trace(
        self,
        contract_id: str,
        solc_version: str | None,
        slither_version: str | None,
        model_version: str,
        dataset_version: str,
        initial_rag_mode: str,
    ) -> str:
        assert self.conn is not None
        trace_id = f"trace_{uuid.uuid4().hex[:12]}"
        self.conn.execute(
            """
            INSERT INTO analysis_trace (
                trace_id, contract_id, solc_version, slither_version, model_version,
                dataset_version, initial_rag_mode, final_status, total_duration_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                contract_id,
                solc_version,
                slither_version,
                model_version,
                dataset_version,
                initial_rag_mode,
                "running",
                0,
            ),
        )
        self.conn.commit()
        return trace_id

    def finish_trace(self, trace_id: str, final_status: str, total_duration_ms: int) -> None:
        assert self.conn is not None
        self.conn.execute(
            "UPDATE analysis_trace SET final_status = ?, total_duration_ms = ? WHERE trace_id = ?",
            (final_status, total_duration_ms, trace_id),
        )
        self.conn.commit()

    def update_versions(
        self,
        trace_id: str,
        solc_version: str | None,
        slither_version: str | None,
    ) -> None:
        assert self.conn is not None
        self.conn.execute(
            "UPDATE analysis_trace SET solc_version = ?, slither_version = ? WHERE trace_id = ?",
            (solc_version, slither_version, trace_id),
        )
        self.conn.commit()

    def record_finding(
        self,
        trace_id: str,
        finding_id: str,
        detector_name: str | None,
        rag_mode: str,
        retrieval_duration_ms: int,
        llm_duration_ms: int,
        chunks_used: int,
        slither_raw: dict[str, Any] | None,
        normalized_finding: dict[str, Any] | None,
        rag_chunk_ids: list[str],
        packed_prompt: str,
        llm_raw_output: dict[str, Any] | str | None,
        schema_valid: bool,
        retry_count: int = 0,
        partial: bool = False,
    ) -> None:
        assert self.conn is not None
        self.conn.execute(
            """
            INSERT OR REPLACE INTO trace_findings (
                trace_id, finding_id, detector_name, rag_mode, retrieval_duration_ms,
                llm_duration_ms, chunks_used, slither_raw, normalized_finding,
                rag_chunk_ids, packed_prompt, llm_raw_output, schema_valid,
                retry_count, partial
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trace_id,
                finding_id,
                detector_name,
                rag_mode,
                retrieval_duration_ms,
                llm_duration_ms,
                chunks_used,
                json.dumps(slither_raw, ensure_ascii=False) if slither_raw is not None else None,
                json.dumps(normalized_finding, ensure_ascii=False)
                if normalized_finding is not None
                else None,
                json.dumps(rag_chunk_ids, ensure_ascii=False),
                packed_prompt,
                json.dumps(llm_raw_output, ensure_ascii=False)
                if not isinstance(llm_raw_output, str)
                else llm_raw_output,
                schema_valid,
                retry_count,
                partial,
            ),
        )
        self.conn.commit()
