from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from smart_contract_audit.analyzer import analyze_contract

LABEL_BY_VULN = {
    "reentrancy": "reentrancy",
    "unchecked_external_call": "unchecked-calls",
    "oracle": "bad-randomness",
    "access_control": "access-control",
    "privilege_escalation": "access-control",
}


class PublicBenchmarkFailure(RuntimeError):
    pass


def run_benchmark(
    manifest_path: Path,
    reports_dir: Path,
    rag_mode: str = "fallback",
    min_supported_hit_rate: float = 0.0,
    min_score_gap: float | None = None,
) -> dict[str, Any]:
    cases = json.loads(manifest_path.read_text(encoding="utf-8"))
    reports_dir.mkdir(parents=True, exist_ok=True)
    results = [
        _run_case(case, reports_dir / str(case["case_id"]), rag_mode) for case in cases
    ]
    summary = _summarize_results(results)
    (reports_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if summary["supported_hit_rate"] < min_supported_hit_rate:
        raise PublicBenchmarkFailure(
            "supported_hit_rate "
            f"{summary['supported_hit_rate']:.4f} is below {min_supported_hit_rate:.4f}"
        )
    score_gap = summary.get("average_score_gap_safe_minus_vulnerable")
    if min_score_gap is not None and score_gap is not None and score_gap < min_score_gap:
        raise PublicBenchmarkFailure(
            f"average_score_gap_safe_minus_vulnerable {score_gap:.2f} "
            f"is below {min_score_gap:.2f}"
        )
    return summary


def _run_case(case: dict[str, Any], output_dir: Path, rag_mode: str) -> dict[str, Any]:
    report = _load_or_analyze_report(case, output_dir, rag_mode)
    expected = sorted(str(label) for label in case.get("supported_labels", []))
    detected = sorted(
        {
            LABEL_BY_VULN[finding.get("vulnerability_type")]
            for finding in report.get("findings", [])
            if finding.get("vulnerability_type") in LABEL_BY_VULN
        }
    )
    expected_set = set(expected)
    detected_set = set(detected)
    return {
        "case_id": str(case["case_id"]),
        "source": case.get("source", ""),
        "source_url": case.get("source_url", ""),
        "external_class": case.get("external_class", ""),
        "file": str(case.get("file", "")),
        "overall_status": report.get("overall_status", "error"),
        "expected_supported_labels": expected,
        "detected_supported_labels": detected,
        "matched_labels": sorted(expected_set & detected_set),
        "missed_labels": sorted(expected_set - detected_set),
        "extra_labels": sorted(detected_set - expected_set),
        "finding_count": len(report.get("findings", [])),
        "security_score": report.get("security_score"),
        "errors": report.get("analysis_metadata", {}).get("errors", []),
    }


def _load_or_analyze_report(
    case: dict[str, Any],
    output_dir: Path,
    rag_mode: str,
) -> dict[str, Any]:
    report_json = case.get("report_json")
    if report_json:
        return json.loads(Path(report_json).read_text(encoding="utf-8"))

    existing = sorted(output_dir.glob("*.json"))
    if existing:
        return json.loads(existing[0].read_text(encoding="utf-8"))

    report = analyze_contract(Path(str(case["file"])), output_dir=output_dir, rag_mode=rag_mode)
    return report.to_dict()


def _summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    label_totals: dict[str, dict[str, int]] = {}
    expected_occurrences = 0
    matched_occurrences = 0
    for result in results:
        matched = set(result["matched_labels"])
        for label in result["expected_supported_labels"]:
            expected_occurrences += 1
            if label in matched:
                matched_occurrences += 1
            label_totals.setdefault(label, {"expected_cases": 0, "matched_cases": 0})
            label_totals[label]["expected_cases"] += 1
            if label in matched:
                label_totals[label]["matched_cases"] += 1

    supported_hit_rate = (
        matched_occurrences / expected_occurrences if expected_occurrences else 0.0
    )
    score_groups = _score_groups(results)
    score_gap = _score_gap(score_groups)
    return {
        "cases": len(results),
        "successful_analyzer_runs": sum(
            1 for result in results if result["overall_status"] in {"finding", "no_finding"}
        ),
        "cases_with_all_expected_supported_labels": sum(
            1 for result in results if not result["missed_labels"]
        ),
        "cases_with_any_expected_supported_label": sum(
            1 for result in results if result["matched_labels"]
        ),
        "supported_label_occurrences": expected_occurrences,
        "matched_label_occurrences": matched_occurrences,
        "supported_hit_rate": supported_hit_rate,
        "score_groups": score_groups,
        "average_score_gap_safe_minus_vulnerable": score_gap,
        "label_totals": label_totals,
        "results": results,
    }


def _score_groups(results: list[dict[str, Any]]) -> dict[str, dict[str, float | int]]:
    group_names = sorted(
        {
            str(result.get("external_class"))
            for result in results
            if result.get("external_class")
        }
    )
    groups: dict[str, dict[str, float | int]] = {}
    for group_name in group_names:
        group_results = [
            result for result in results if result.get("external_class") == group_name
        ]
        scores = [
            float(result["security_score"])
            for result in group_results
            if isinstance(result.get("security_score"), int | float)
        ]
        if not scores:
            continue
        groups[group_name] = {
            "count": len(group_results),
            "successful_runs": sum(
                1
                for result in group_results
                if result["overall_status"] in {"finding", "no_finding"}
            ),
            "average_security_score": round(sum(scores) / len(scores), 2),
            "median_security_score": round(statistics.median(scores), 2),
            "min_security_score": round(min(scores), 2),
            "max_security_score": round(max(scores), 2),
            "score_lt_50": sum(1 for score in scores if score < 50),
            "score_50_to_89": sum(1 for score in scores if 50 <= score < 90),
            "score_gte_90": sum(1 for score in scores if score >= 90),
            "finding_cases": sum(1 for result in group_results if result["finding_count"] > 0),
            "no_finding_cases": sum(
                1 for result in group_results if result["finding_count"] == 0
            ),
        }
    return groups


def _score_gap(score_groups: dict[str, dict[str, float | int]]) -> float | None:
    safe = score_groups.get("safe")
    vulnerable = score_groups.get("vulnerable")
    if not safe or not vulnerable:
        return None
    return round(
        float(safe["average_security_score"])
        - float(vulnerable["average_security_score"]),
        2,
    )
