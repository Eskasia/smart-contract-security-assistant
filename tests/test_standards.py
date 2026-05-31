from smart_contract_audit.standards import standard_refs_for


def test_standard_refs_for_reentrancy_include_owasp_and_swc() -> None:
    refs = standard_refs_for("reentrancy")

    ids = {ref["id"] for ref in refs}
    assert "SC08:2026" in ids
    assert "SWC-107" in ids


def test_unknown_standard_mapping_returns_empty_list() -> None:
    assert standard_refs_for("unknown_type") == []
