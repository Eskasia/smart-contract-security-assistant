from pathlib import Path

from smart_contract_audit.finding_adapter import normalize_slither_json
from smart_contract_audit.models import AnalysisMetadata, AnalysisReport
from smart_contract_audit.validation.validator import validate_report

DETECTOR_CASES = {
    "oracle": [
        ("weak-prng", "tests/contracts/detectors/OracleWeakRandom.sol"),
        ("pyth-unchecked-confidence", "tests/contracts/detectors/OracleStalePrice.sol"),
    ],
    "price_manipulation": [
        ("divide-before-multiply", "tests/contracts/detectors/PriceSlippage.sol"),
        ("timestamp", "tests/contracts/detectors/PriceTimestamp.sol"),
    ],
    "privilege_escalation": [
        ("arbitrary-send-erc20", "tests/contracts/detectors/PrivilegeOwnerDrain.sol"),
        ("tx-origin", "tests/contracts/detectors/PrivilegeTxOrigin.sol"),
    ],
    "upgrade_risk": [
        ("unprotected-upgrade", "tests/contracts/detectors/UpgradeInitializer.sol"),
        ("uninitialized-state", "tests/contracts/detectors/UpgradeStorage.sol"),
    ],
}


def test_expanded_detector_mapping_has_two_contracts_per_class() -> None:
    for vulnerability_type, cases in DETECTOR_CASES.items():
        assert len(cases) == 2
        for detector_name, contract_path in cases:
            path = Path(contract_path)
            assert path.exists()
            raw = _raw_detector(detector_name, path)

            result = normalize_slither_json(raw, path)

            assert not result.unmapped
            assert result.findings[0].vulnerability_type == vulnerability_type


def test_expanded_detector_report_passes_schema_validation() -> None:
    findings = []
    for vulnerability_type, cases in DETECTOR_CASES.items():
        detector_name, contract_path = cases[0]
        result = normalize_slither_json(
            _raw_detector(detector_name, Path(contract_path)),
            Path(contract_path),
        )
        finding = result.findings[0]
        finding.finding_id = f"f_{len(findings) + 1:03d}"
        assert finding.vulnerability_type == vulnerability_type
        findings.append(finding)

    report = AnalysisReport(
        report_version="report_v1.1",
        overall_status="finding",
        contract_id="detector_expansion",
        review_status="pending_human_review",
        requires_human_review=True,
        business_logic_review_required=True,
        review_reason="Expanded detector mapping validation.",
        findings=findings,
        analysis_metadata=AnalysisMetadata(
            dataset_version="dataset_v1.0",
            model_version="mlx-8b-4bit",
            solc_version="0.8.34",
            slither_version="0.11.5",
            partial_analysis=False,
            analysis_trace_id="trace_detector_expansion",
            context_tokens_used=0,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            local_average_judge_score=0.0,
            external_average_judge_score=0.0,
            rag_mode="fallback",
            total_duration_ms=1,
            input_kind="single_file",
            project_type="single_file",
            entry_path="tests/contracts/detectors/OracleWeakRandom.sol",
            project_root="tests/contracts/detectors",
            source_files_count=1,
        ),
    )

    validation = validate_report(report.to_dict())
    assert validation.valid, validation.errors


def _raw_detector(detector_name: str, path: Path) -> dict:
    return {
        "results": {
            "detectors": [
                {
                    "check": detector_name,
                    "description": f"{detector_name} evidence in {path.name}",
                    "elements": [
                        {
                            "type": "function",
                            "name": "fixture",
                            "source_mapping": {
                                "lines": [3, 4],
                                "filename_relative": str(path),
                            },
                        }
                    ],
                }
            ]
        }
    }
