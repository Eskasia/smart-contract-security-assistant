from pathlib import Path

from smart_contract_audit.finding_adapter import normalize_slither_json


def test_normalize_mapped_detector() -> None:
    raw = {
        "results": {
            "detectors": [
                {
                    "check": "reentrancy-eth",
                    "description": "withdraw() sends ETH before updating state",
                    "elements": [
                        {
                            "type": "function",
                            "name": "withdraw",
                            "source_mapping": {
                                "lines": [10, 11, 12],
                                "filename_relative": "Vault.sol",
                            },
                        }
                    ],
                }
            ]
        }
    }

    result = normalize_slither_json(raw, Path("Vault.sol"))

    assert len(result.findings) == 1
    assert result.findings[0].vulnerability_type == "reentrancy"
    assert result.findings[0].severity == 3
    assert result.findings[0].location.line_start == 10
    assert not result.unmapped


def test_unmapped_detector_goes_to_trace_bucket() -> None:
    raw = {"results": {"detectors": [{"check": "unused-state", "description": "not in MVP"}]}}

    result = normalize_slither_json(raw, Path("Vault.sol"))

    assert not result.findings
    assert len(result.unmapped) == 1
