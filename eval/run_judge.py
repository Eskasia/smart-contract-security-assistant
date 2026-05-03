from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
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
    local_scores = [_score_case(case) for case in cases]
    external_scores = [_external_score_case(case) for case in cases]
    local_average = sum(local_scores) / len(local_scores) if local_scores else 0
    external_average = sum(external_scores) / len(external_scores) if external_scores else 0
    local_judge_model = os.getenv("JUDGE_MODEL", "local-rule-judge")
    external_judge_model = os.getenv("EXTERNAL_JUDGE_MODEL", "external-rule-judge-adapter")
    print(
        json.dumps(
            {
                "cases": len(cases),
                "local_average_judge_score": local_average,
                "external_average_judge_score": external_average,
                "local_judge_model": local_judge_model,
                "external_judge_model": external_judge_model,
            },
            indent=2,
        )
    )
    if local_scores and (local_average < 4.0 or external_average < 4.0):
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


def _external_score_case(case: dict) -> float:
    command = os.getenv("EXTERNAL_JUDGE_COMMAND")
    if command:
        return _score_with_command(command, case)
    return _score_case(case)


def _score_with_command(command: str, case: dict) -> float:
    result = subprocess.run(
        command.split(),
        input=json.dumps(case, ensure_ascii=False),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        return 0.0
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return 0.0
    score = payload.get("score", 0)
    return float(score) if isinstance(score, int | float) else 0.0


if __name__ == "__main__":
    main()
