import json
from pathlib import Path

import pytest

from smart_contract_audit.evaluation.public_benchmark import (
    PublicBenchmarkFailure,
    run_benchmark,
)


def test_public_benchmark_counts_supported_label_hits(tmp_path: Path) -> None:
    report_a = tmp_path / "a.json"
    report_b = tmp_path / "b.json"
    _write_report(report_a, ["reentrancy", "oracle"], security_score=40)
    _write_report(report_b, [], security_score=95)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "case_id": "case_a",
                    "file": "a.sol",
                    "report_json": str(report_a),
                    "external_class": "vulnerable",
                    "supported_labels": ["reentrancy", "bad-randomness"],
                },
                {
                    "case_id": "case_b",
                    "file": "b.sol",
                    "report_json": str(report_b),
                    "external_class": "safe",
                    "supported_labels": ["unchecked-calls"],
                },
            ]
        ),
        encoding="utf-8",
    )

    summary = run_benchmark(manifest, tmp_path / "reports", min_supported_hit_rate=0.0)

    assert summary["cases"] == 2
    assert summary["supported_label_occurrences"] == 3
    assert summary["matched_label_occurrences"] == 2
    assert summary["supported_hit_rate"] == pytest.approx(2 / 3)
    assert summary["label_totals"]["bad-randomness"] == {
        "expected_cases": 1,
        "matched_cases": 1,
    }
    assert summary["score_groups"]["safe"]["average_security_score"] == 95.0
    assert summary["score_groups"]["vulnerable"]["average_security_score"] == 40.0
    assert summary["average_score_gap_safe_minus_vulnerable"] == 55.0
    assert summary["results"][1]["missed_labels"] == ["unchecked-calls"]


def test_public_benchmark_fails_below_threshold(tmp_path: Path) -> None:
    report = tmp_path / "report.json"
    _write_report(report, [])
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "case_id": "case_a",
                    "file": "a.sol",
                    "report_json": str(report),
                    "supported_labels": ["reentrancy"],
                }
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(PublicBenchmarkFailure):
        run_benchmark(manifest, tmp_path / "reports", min_supported_hit_rate=0.95)


def test_public_benchmark_fails_when_score_gap_is_too_small(tmp_path: Path) -> None:
    safe_report = tmp_path / "safe.json"
    vulnerable_report = tmp_path / "vulnerable.json"
    _write_report(safe_report, [], security_score=80)
    _write_report(vulnerable_report, ["reentrancy"], security_score=70)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            [
                {
                    "case_id": "safe",
                    "file": "safe.sol",
                    "report_json": str(safe_report),
                    "external_class": "safe",
                    "supported_labels": [],
                },
                {
                    "case_id": "vulnerable",
                    "file": "vulnerable.sol",
                    "report_json": str(vulnerable_report),
                    "external_class": "vulnerable",
                    "supported_labels": ["reentrancy"],
                },
            ]
        ),
        encoding="utf-8",
    )

    with pytest.raises(PublicBenchmarkFailure):
        run_benchmark(
            manifest,
            tmp_path / "reports",
            min_supported_hit_rate=0.0,
            min_score_gap=30.0,
        )


def _write_report(
    path: Path,
    vulnerability_types: list[str],
    security_score: float = 100.0,
) -> None:
    path.write_text(
        json.dumps(
            {
                "overall_status": "finding" if vulnerability_types else "no_finding",
                "security_score": security_score,
                "findings": [
                    {
                        "vulnerability_type": vulnerability_type,
                        "detector_name": vulnerability_type,
                    }
                    for vulnerability_type in vulnerability_types
                ],
                "analysis_metadata": {"errors": []},
            }
        ),
        encoding="utf-8",
    )
