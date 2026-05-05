from __future__ import annotations

import argparse
import json
from pathlib import Path

from smart_contract_audit.evaluation.public_project_builds import (
    preflight_public_project_builds,
    run_public_project_builds,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "manifest",
        type=Path,
        nargs="?",
        default=Path("eval/public_benchmark/public-project-builds-10-manifest.json"),
    )
    parser.add_argument("--workspace-dir", type=Path, default=Path("public-projects"))
    parser.add_argument("--reports-dir", type=Path, default=Path("reports-public/projects"))
    parser.add_argument(
        "--rag-mode",
        choices=["quality", "balanced", "fast", "fallback"],
        default="fallback",
    )
    parser.add_argument("--min-analyzer-success-rate", type=float, default=0.0)
    parser.add_argument("--min-native-build-success-rate", type=float, default=0.0)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()

    if args.preflight_only:
        summary = preflight_public_project_builds(args.manifest)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return

    summary = run_public_project_builds(
        args.manifest,
        workspace_dir=args.workspace_dir,
        reports_dir=args.reports_dir,
        rag_mode=args.rag_mode,
        min_analyzer_success_rate=args.min_analyzer_success_rate,
        min_native_build_success_rate=args.min_native_build_success_rate,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
