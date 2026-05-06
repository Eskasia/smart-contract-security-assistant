from pathlib import Path

import pytest

from smart_contract_audit.analyzer import analyze_contract
from smart_contract_audit.slither_runner import SlitherRunError, SlitherRunResult


def test_e2e_slither_to_trace_report(tmp_path: Path) -> None:
    try:
        report = analyze_contract(
            Path("tests/contracts/VulnerableVault.sol"),
            output_dir=tmp_path / "reports",
            dataset_chunks=Path("data/dataset_v1.0/chunks/chunks.jsonl"),
            rag_mode="fallback",
        )
    except SlitherRunError as exc:
        pytest.fail(f"E2E Slither run failed: {exc}")

    assert report.overall_status == "finding"
    assert report.analysis_metadata.total_duration_ms < 120_000
    assert report.findings[0].vulnerability_type == "reentrancy"
    assert report.findings[0].explanation_confidence >= 0.5
    assert "msg.sender.call" in report.findings[0].vulnerable_code
    assert "nonReentrant" in report.findings[0].remediation_code
    assert report.analysis_metadata.total_tokens > 0
    assert report.analysis_metadata.external_average_judge_score == 5.0
    assert (tmp_path / "reports" / f"{report.contract_id}.json").exists()
    assert (tmp_path / "reports" / "analysis_trace.sqlite").exists()
    markdown = (tmp_path / "reports" / f"{report.contract_id}.md").read_text(encoding="utf-8")
    assert "Vulnerable code:" in markdown
    assert "AI remediation code:" in markdown


def test_e2e_timeout_marks_partial(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    ticks = iter([0.0, 116.0, 116.1, 116.2])
    monkeypatch.setattr("smart_contract_audit.analyzer.time.perf_counter", lambda: next(ticks))

    def fake_slither(_: Path, native_build_policy: str = "trusted") -> SlitherRunResult:
        return SlitherRunResult(
            raw_json={
                "results": {
                    "detectors": [
                        {
                            "check": "reentrancy-eth",
                            "description": "External call before state update",
                            "elements": [
                                {
                                    "type": "function",
                                    "name": "withdraw",
                                    "source_mapping": {
                                        "lines": [11, 12, 13],
                                        "filename_relative": "Vault.sol",
                                    },
                                }
                            ],
                        }
                    ]
                }
            },
            solc_version="0.8.34",
            slither_version="0.11.5",
            warnings=[],
        )

    report = analyze_contract(
        Path("tests/contracts/VulnerableVault.sol"),
        output_dir=tmp_path / "timeout-reports",
        dataset_chunks=Path("data/dataset_v1.0/chunks/chunks.jsonl"),
        slither_runner=fake_slither,
    )

    assert report.overall_status == "partial_analysis"
    assert report.findings[0].partial is True
