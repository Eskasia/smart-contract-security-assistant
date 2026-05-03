from __future__ import annotations

import argparse
from pathlib import Path

from smart_contract_audit.rag.indexer import load_chunks, write_chunks

KEYWORDS = {
    "reentrancy": "reentrancy",
    "onlyowner": "privilege_escalation",
    "access control": "privilege_escalation",
    "owner can": "privilege_escalation",
    "low-level call": "unchecked_external_call",
    "delegatecall": "dangerous_delegatecall",
    "array length": "array_length_manipulation",
    "oracle": "oracle",
    "price feed": "oracle",
    "slippage": "price_manipulation",
    "swap": "price_manipulation",
    "upgrade": "upgrade_risk",
    "proxy": "upgrade_risk",
    "zero address": "input_validation",
    "zero amount": "input_validation",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_jsonl", type=Path)
    parser.add_argument("output_jsonl", type=Path)
    args = parser.parse_args()

    chunks = load_chunks(args.input_jsonl)
    for chunk in chunks:
        if chunk.vuln_type != "unknown":
            continue
        lowered = chunk.content.lower()
        for keyword, vuln_type in KEYWORDS.items():
            if keyword in lowered:
                chunk.vuln_type = vuln_type
                chunk.label_source = "rule_based_backfill"
                chunk.label_confidence = 0.75
                chunk.eligible_for_eval = True
                break
    write_chunks(chunks, args.output_jsonl)


if __name__ == "__main__":
    main()
