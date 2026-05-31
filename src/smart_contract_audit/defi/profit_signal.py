from __future__ import annotations

from typing import Any


def derive_defi_profit_signal(finding: Any) -> dict[str, Any]:
    validation = finding.exploit_validation or {}
    asset_delta = validation.get("asset_delta") or []
    if (
        validation.get("status") == "executed_triggered"
        and validation.get("mode") in {"local_foundry_test", "sandbox_only"}
        and asset_delta
    ):
        return {
            "status": "observed",
            "asset_flow": asset_delta,
            "oracle_dependency": None,
            "flash_loan_dependency": False,
            "profitability_status": "profitable_in_sandbox",
            "supported_by": [
                validation.get(
                    "validation_id",
                    f"exploit_validation:{finding.finding_id}:001",
                )
            ],
        }
    return {
        "status": "not_observed",
        "asset_flow": [],
        "oracle_dependency": None,
        "flash_loan_dependency": False,
        "profitability_status": "not_assessed",
        "supported_by": [],
    }
