from pathlib import Path

from smart_contract_audit.evaluation.paired_variants import evaluate_paired_variants


def test_paired_variants_meet_phase_two_gate() -> None:
    result = evaluate_paired_variants(Path("eval/paired_variants"))

    assert result["vulnerability_types"] >= 5
    assert result["pairs"] >= 15
    assert result["paired_pass_rate"] >= 0.70
    assert result["precision"] >= 0.70
    assert result["recall"] >= 0.70
