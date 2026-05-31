from __future__ import annotations

from .auth_sensitive_write import evaluate_auth_sensitive_write
from .consensus import evaluate_consensus
from .proxy_risk import evaluate_proxy_risk
from .reentrancy_confirmer import evaluate_reentrancy
from .unchecked_call import evaluate_unchecked_call

__all__ = ["apply_native_rules"]


def apply_native_rules(finding, sibling_findings=()):
    siblings = list(sibling_findings)
    return [
        evaluate_reentrancy(finding),
        evaluate_auth_sensitive_write(finding),
        evaluate_unchecked_call(finding),
        evaluate_proxy_risk(finding),
        evaluate_consensus(finding, siblings),
    ]
