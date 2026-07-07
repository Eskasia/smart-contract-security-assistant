from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import Finding


def build_falsification_pack(finding: Finding) -> dict[str, Any]:
    """Build reviewer checks that can confirm or refute a finding."""
    normalized_type = finding.vulnerability_type.lower()
    checks = _checks_for_type(normalized_type)
    requirements = _requirements_for_type(normalized_type)
    missing_evidence = _missing_evidence(finding, normalized_type)
    return {
        "status": "needs_human_review",
        "reviewer_goal": (
            "Confirm the detector evidence or document the counterevidence before "
            "marking this finding true_positive, false_positive, accepted_risk, or fixed."
        ),
        "counterevidence_checks": checks,
        "confirmation_requirements": requirements,
        "missing_evidence": missing_evidence,
        "human_review_required": True,
        "supported_by": _supported_by(finding),
        "limitations": [
            "Generated from detector evidence and local report context.",
            "This pack is not proof that the finding is exploitable or impossible.",
        ],
    }


def _checks_for_type(vulnerability_type: str) -> list[dict[str, str]]:
    checks_by_type = {
        "reentrancy": [
            _check(
                "reentrancy_state_update_before_call",
                "Is every affected balance or accounting state updated before the external call?",
                "All affected state is updated before the external call on every reachable path.",
                "Trace the function order around the external call and state writes.",
            ),
            _check(
                "reentrancy_guard_effective",
                "Is an effective nonReentrant guard or equivalent mutex active on the call path?",
                "A reachable guard prevents nested entry into the affected function.",
                "Inspect modifiers, inherited guards, and internal function call paths.",
            ),
            _check(
                "reentrancy_untrusted_receiver",
                "Can the receiver execute attacker-controlled fallback or callback logic?",
                "The receiver is fixed, trusted, and cannot re-enter the affected path.",
                "Identify the receiver source and whether user-controlled code can run.",
            ),
        ],
        "access_control": [
            _check(
                "access_control_authorization_boundary",
                "Is the affected operation protected by owner, role, or capability checks?",
                "All reachable callers must pass an intended authorization boundary.",
                "Review modifiers, internal guards, and inherited access-control logic.",
            ),
            _check(
                "access_control_public_intent",
                "Is the operation intentionally public and safe for any caller?",
                "The operation is designed to be permissionless and cannot move privileged state.",
                "Compare code behavior with the protocol's documented permission model.",
            ),
        ],
        "unchecked_external_call": [
            _check(
                "unchecked_call_success_handling",
                "Is the external call success value checked before state continues?",
                "The return value is checked or failure is safely handled before "
                "accounting continues.",
                "Inspect the call result variables, require statements, and error branches.",
            ),
            _check(
                "unchecked_call_failure_impact",
                "Can a failed call leave user-visible state, accounting, or assets inconsistent?",
                "Failure has no security impact or all state changes are reverted.",
                "Trace state writes before and after the external call.",
            ),
        ],
        "dangerous_delegatecall": [
            _check(
                "delegatecall_target_control",
                "Can an untrusted caller influence the delegatecall target or calldata?",
                "The target and calldata are fixed or constrained to audited code paths.",
                "Trace target derivation and caller-controlled parameters.",
            ),
            _check(
                "delegatecall_storage_impact",
                "Can delegated code modify privileged storage in the caller contract?",
                "Delegated code cannot reach sensitive storage or authority-changing state.",
                "Map storage layout and writes reachable through delegatecall.",
            ),
        ],
    }
    return checks_by_type.get(
        vulnerability_type,
        [
            _check(
                "detector_evidence_matches_code",
                "Does the detector evidence still match the current source code?",
                "The referenced code path is absent, unreachable, or materially different.",
                "Open the referenced location and compare it with the normalized finding evidence.",
            ),
            _check(
                "security_impact_reachable",
                "Can an attacker reach the affected path and cause security impact?",
                "The path is unreachable by an attacker or impact is blocked by "
                "surrounding checks.",
                "Trace caller permissions, state preconditions, and asset or authority effects.",
            ),
        ],
    )


def _requirements_for_type(vulnerability_type: str) -> list[str]:
    requirements_by_type = {
        "reentrancy": [
            "Show a reachable external call before the relevant state update.",
            "Show that attacker-controlled code can re-enter the affected path.",
            "Show the guard or ordering is absent or ineffective.",
        ],
        "access_control": [
            "Show the intended authorization boundary for the affected operation.",
            "Show an unauthorized caller can reach the operation.",
            "Show the operation changes privileged state, assets, or authority.",
        ],
        "unchecked_external_call": [
            "Show the external call can fail without reverting.",
            "Show execution continues after the failure.",
            "Show continued execution can create inconsistent state or asset flow.",
        ],
        "dangerous_delegatecall": [
            "Show caller influence over delegatecall target or payload.",
            "Show delegated code executes in the caller storage context.",
            "Show a sensitive storage or authority impact is reachable.",
        ],
    }
    return requirements_by_type.get(
        vulnerability_type,
        [
            "Confirm the referenced source location still exists.",
            "Confirm the vulnerable path is reachable by the attacker model.",
            "Confirm the impact is security-relevant and not only informational.",
        ],
    )


def _missing_evidence(finding: Finding, vulnerability_type: str) -> list[str]:
    context = " ".join(
        [
            finding.evidence,
            finding.vulnerable_code,
            finding.explanation,
            finding.attack_path,
        ]
    ).lower()
    missing: list[str] = []
    if vulnerability_type == "reentrancy":
        if "nonreentrant" not in context and "mutex" not in context:
            missing.append("No positive or negative reentrancy guard evidence is recorded.")
        if "balance" not in context and "state" not in context:
            missing.append("No concrete affected accounting state is named.")
        if "fallback" not in context and "callback" not in context and "re-enter" not in context:
            missing.append("No callback or fallback route is confirmed.")
    elif vulnerability_type == "access_control":
        if "owner" not in context and "role" not in context and "auth" not in context:
            missing.append("No intended authorization boundary is named.")
        if "asset" not in context and "admin" not in context and "privileged" not in context:
            missing.append("No privileged state or asset impact is named.")
    elif vulnerability_type == "unchecked_external_call":
        if "success" not in context and "return" not in context:
            missing.append("No unchecked return value variable is named.")
        if "state" not in context and "accounting" not in context and "asset" not in context:
            missing.append("No failure impact on state or assets is named.")
    elif vulnerability_type == "dangerous_delegatecall":
        if "target" not in context and "calldata" not in context:
            missing.append("No delegatecall target or payload control evidence is named.")
        if "storage" not in context and "owner" not in context and "admin" not in context:
            missing.append("No caller-storage impact is named.")
    if not missing:
        missing.append("No obvious missing evidence was detected by deterministic checks.")
    return missing


def _supported_by(finding: Finding) -> list[str]:
    return [
        f"detector:{finding.detector_name}",
        f"static_tool:{finding.static_tool_source}",
        f"location:{finding.location.file}:{finding.location.line_start}",
    ]


def _check(
    check_id: str,
    question: str,
    would_refute_if: str,
    evidence_to_collect: str,
) -> dict[str, str]:
    return {
        "check_id": check_id,
        "question": question,
        "would_refute_if": would_refute_if,
        "evidence_to_collect": evidence_to_collect,
        "status": "not_checked",
    }
