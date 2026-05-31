from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def evaluate_paired_variants(root: Path) -> dict[str, Any]:
    cases = _load_cases(root)
    results = []
    tp = tn = fp = fn = paired_passes = 0
    for case in cases:
        vuln_type = case["vulnerability_type"]
        positive_detected = _detect(vuln_type, (root / case["positive"]["path"]).read_text())
        negative_detected = _detect(vuln_type, (root / case["negative"]["path"]).read_text())
        if positive_detected:
            tp += 1
        else:
            fn += 1
        if negative_detected:
            fp += 1
        else:
            tn += 1
        pair_pass = positive_detected and not negative_detected
        paired_passes += int(pair_pass)
        results.append(
            {
                "case_id": case["case_id"],
                "vulnerability_type": vuln_type,
                "positive_detected": positive_detected,
                "negative_detected": negative_detected,
                "pair_pass": pair_pass,
            }
        )

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    paired_pass_rate = paired_passes / len(cases) if cases else 0.0
    return {
        "cases": results,
        "pairs": len(cases),
        "vulnerability_types": len({case["vulnerability_type"] for case in cases}),
        "true_positive": tp,
        "true_negative": tn,
        "false_positive": fp,
        "false_negative": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "paired_pass_rate": round(paired_pass_rate, 4),
    }


def write_paired_variant_reports(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "paired_variant_results.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    summary = [
        "# Paired Variant Benchmark Summary",
        "",
        f"- Pairs: `{result['pairs']}`",
        f"- Vulnerability types: `{result['vulnerability_types']}`",
        f"- Precision: `{result['precision']}`",
        f"- Recall: `{result['recall']}`",
        f"- F1: `{result['f1']}`",
        f"- Paired pass rate: `{result['paired_pass_rate']}`",
    ]
    (output_dir / "benchmark_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")


def _load_cases(root: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for metadata_path in sorted(root.glob("*/metadata.yml")):
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        for case in payload["cases"]:
            case = dict(case)
            base = metadata_path.parent.relative_to(root)
            case["positive"] = dict(case["positive"])
            case["negative"] = dict(case["negative"])
            case["positive"]["path"] = str(base / case["positive"]["path"])
            case["negative"]["path"] = str(base / case["negative"]["path"])
            cases.append(case)
    return cases


def _detect(vulnerability_type: str, source: str) -> bool:
    text = _strip_comments(source).lower().replace(" ", "")
    if vulnerability_type == "reentrancy":
        call = text.find(".call")
        reset = text.find("balances[msg.sender]=0")
        return call >= 0 and reset >= 0 and call < reset and "nonreentrant" not in text
    if vulnerability_type == "unchecked_external_call":
        has_call = any(marker in text for marker in (".call(", ".delegatecall(", ".staticcall("))
        checked = any(
            marker in text
            for marker in ("require(success", "if(!success", "assert(success")
        )
        return has_call and not checked
    if vulnerability_type == "access_control":
        sensitive_write = any(
            marker in text
            for marker in ("owner=", "admin=", "treasury=", "fee=")
        )
        public_entry = "external" in text or "public" in text
        guarded = "onlyowner" in text or "require(msg.sender==owner" in text
        return sensitive_write and public_entry and not guarded
    if vulnerability_type == "upgrade_risk":
        upgrade_write = "implementation=" in text or "_implementationslot" in text
        initializer = "initialize(" in text
        guarded = (
            "onlyowner" in text
            or "require(msg.sender==owner" in text
            or "initializer" in text.replace("functioninitialize", "")
        )
        return (upgrade_write or initializer) and not guarded
    if vulnerability_type == "dangerous_delegatecall":
        has_delegatecall = ".delegatecall" in text
        guarded = "onlyowner" in text or "allowlisted" in text or "trustedtarget" in text
        return has_delegatecall and not guarded
    return False


def _strip_comments(source: str) -> str:
    lines = []
    for line in source.splitlines():
        lines.append(line.split("//", 1)[0])
    return "\n".join(lines)
