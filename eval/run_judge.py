from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "judge_eval_set",
        type=Path,
        nargs="?",
        default=Path("eval/judge_eval_set.json"),
    )
    args = parser.parse_args()

    cases = json.loads(args.judge_eval_set.read_text(encoding="utf-8"))
    scores = [_score_case(case) for case in cases]
    average = sum(scores) / len(scores) if scores else 0
    judge_model = os.getenv("JUDGE_MODEL", "local-rule-judge")
    print(
        json.dumps(
            {
                "cases": len(cases),
                "average_judge_score": average,
                "judge_model": judge_model,
            },
            indent=2,
        )
    )
    if scores and average < 4.0:
        raise SystemExit(1)


def _score_case(case: dict) -> float:
    output = case.get("local_model_output", {})
    score = 0.0
    if case.get("static_finding", {}).get("vulnerability_type", "") in output.get(
        "explanation", ""
    ):
        score += 1.0
    if output.get("fix_suggestion"):
        score += 1.0
    if output.get("attack_path"):
        score += 1.0
    if re.search(r"line\s+\d+|L\d+", output.get("explanation", ""), re.IGNORECASE):
        score += 1.0
    if any(
        str(chunk_id) in output.get("explanation", "") for chunk_id in case.get("rag_chunks", [])
    ):
        score += 1.0
    return score


if __name__ == "__main__":
    main()
