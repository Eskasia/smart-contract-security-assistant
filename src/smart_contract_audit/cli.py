from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzer import analyze_contract
from .external_tools import SUPPORTED_EXTERNAL_TOOLS
from .llm.mlx_runtime import MLXRuntimeConfig, discover_mlx_model_paths, probe_mlx_runtime
from .rag.chunker import chunk_document
from .rag.indexer import deduplicate_chunks, write_chunks
from .report_compare import (
    compare_report_files,
    comparison_should_fail,
    render_comparison_markdown,
)
from .source_import import (
    ImportLimits,
    cleanup_import_staging,
    import_explorer_source,
    import_github_source,
    import_local_archive,
)
from .trace.lookup import lookup_trace, trace_dashboard
from .zero_g.proof_package import attach_zero_g_proof, build_proof_package


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="scsa")
    subparsers = parser.add_subparsers(dest="command", required=True)

    analyze = subparsers.add_parser("analyze", help="Analyze a single Solidity file.")
    analyze.add_argument("contract", type=Path)
    analyze.add_argument("--out-dir", type=Path, default=Path("reports"))
    analyze.add_argument("--trace-db", type=Path)
    analyze.add_argument(
        "--dataset-chunks", type=Path, default=Path("data/dataset_v1.0/chunks/chunks.jsonl")
    )
    analyze.add_argument(
        "--rag-mode", choices=["quality", "balanced", "fast", "fallback"], default="balanced"
    )
    analyze.add_argument("--model-path")
    analyze.add_argument(
        "--native-build-policy",
        choices=["trusted", "disabled"],
        default="disabled",
    )
    analyze.add_argument(
        "--external-tool",
        action="append",
        choices=sorted(SUPPORTED_EXTERNAL_TOOLS),
        default=[],
        help="Run optional external tools and attach their summaries to the report.",
    )
    analyze.add_argument("--external-timeout-seconds", type=int, default=60)

    import_source = subparsers.add_parser(
        "import-source",
        help="Stage remote or local Solidity sources into a safe local directory.",
    )
    import_source_group = import_source.add_mutually_exclusive_group(required=True)
    import_source_group.add_argument("--zip-file", type=Path)
    import_source_group.add_argument("--github-url")
    import_source_group.add_argument("--etherscan-api-host")
    import_source.add_argument("--address")
    import_source.add_argument("--api-key")
    import_source.add_argument("--out-dir", type=Path, default=Path("reports-api/imports"))
    import_source.add_argument("--max-files", type=int, default=128)
    import_source.add_argument("--max-total-bytes", type=int, default=5_000_000)
    import_source.add_argument("--max-single-file-bytes", type=int, default=1_000_000)

    clean_imports = subparsers.add_parser(
        "clean-imports",
        help="Remove expired source import staging directories.",
    )
    clean_imports.add_argument("--imports-dir", type=Path, default=Path("reports-api/imports"))
    clean_imports.add_argument("--ttl-seconds", type=int, default=86_400)

    clean = subparsers.add_parser("clean-reports", help="Extract and chunk raw reports into JSONL.")
    clean.add_argument("raw_reports_dir", type=Path)
    clean.add_argument("output_jsonl", type=Path)
    clean.add_argument("--filter-unknown", action="store_true")

    lookup = subparsers.add_parser("trace-lookup", help="Lookup trace rows.")
    lookup.add_argument("trace_db", type=Path)
    lookup.add_argument("trace_id")
    lookup.add_argument("--finding-id")

    dashboard = subparsers.add_parser("trace-dashboard", help="Summarize analysis traces.")
    dashboard.add_argument("trace_db", type=Path)

    compare = subparsers.add_parser(
        "compare-reports",
        help="Compare two JSON reports and optionally fail on security regression.",
    )
    compare.add_argument("base_report", type=Path)
    compare.add_argument("head_report", type=Path)
    compare.add_argument("--output", type=Path)
    compare.add_argument("--fail-on-high-added", action="store_true")
    compare.add_argument("--fail-on-score-drop", type=float)

    zero_g_package = subparsers.add_parser(
        "0g-package",
        help="Create a 0G audit proof package for a JSON report.",
    )
    zero_g_package.add_argument("report", type=Path)
    zero_g_package.add_argument("--out-dir", type=Path, default=Path("reports-0g"))
    zero_g_package.add_argument("--project-name", default="SCSA 0G Audit Proof")
    zero_g_package.add_argument(
        "--track",
        default="Track 1: Agentic Infrastructure & OpenClaw Lab",
    )

    zero_g_attach_proof = subparsers.add_parser(
        "0g-attach-proof",
        help="Attach 0G proof metadata to an audit JSON report.",
    )
    zero_g_attach_proof.add_argument("report", type=Path)
    zero_g_attach_proof.add_argument("proof", type=Path)

    properties = subparsers.add_parser(
        "properties",
        help="Generate reviewer-only formal property suggestions.",
    )
    properties_subparsers = properties.add_subparsers(
        dest="properties_command",
        required=True,
    )
    properties_suggest = properties_subparsers.add_parser(
        "suggest",
        help="Suggest draft formal properties for an existing JSON report.",
    )
    properties_suggest.add_argument("report", type=Path)
    properties_suggest.add_argument(
        "--format",
        default="foundry_invariant",
        choices=[
            "foundry-invariant",
            "foundry_invariant",
            "scribble",
            "certora_cvl",
            "solidity_assert",
        ],
    )
    properties_suggest.add_argument("--out", type=Path, default=Path("reports/properties"))

    mlx_probe = subparsers.add_parser("mlx-probe", help="Record MLX load/fallback status.")
    mlx_probe.add_argument("--model-path")
    mlx_probe.add_argument("--parameter-count-billion", type=float, default=8.0)
    mlx_probe.add_argument("--quantization-bits", type=int, default=4)
    mlx_probe.add_argument("--max-tokens", type=int, default=16)
    mlx_probe.add_argument("--prompt", default='Return JSON: {"ok": true}')
    mlx_probe.add_argument("--auto-discover-model", action="store_true")
    mlx_probe.add_argument("--model-search-root", type=Path, action="append")
    mlx_probe.add_argument("--output", type=Path)

    web = subparsers.add_parser("web", help="Run the optional Gradio UI.")
    web.add_argument("--host", default="127.0.0.1")
    web.add_argument("--port", type=int, default=7860)

    api = subparsers.add_parser("api", help="Run the local HTTP API for the React frontend.")
    api.add_argument("--host", default="127.0.0.1")
    api.add_argument("--port", type=int, default=8787)
    api.add_argument("--out-dir", type=Path, default=Path("reports-api"))
    api.add_argument("--trace-db", type=Path)
    api.add_argument("--input-root", type=Path)
    api.add_argument("--api-token")
    api.add_argument("--allow-tokenless-local-demo", action="store_true")
    api.add_argument("--allow-any-input-root", action="store_true")
    api.add_argument("--cors-origin", default="http://127.0.0.1:5173")
    api.add_argument("--max-request-bytes", type=int, default=1_048_576)
    api.add_argument("--max-concurrent-jobs", type=int, default=4)
    api.add_argument("--max-events-per-job", type=int, default=256)
    api.add_argument("--max-report-bytes", type=int, default=5_000_000)
    api.add_argument("--imports-dir", type=Path)
    api.add_argument("--max-import-files", type=int, default=128)
    api.add_argument("--max-import-bytes", type=int, default=5_000_000)
    api.add_argument("--max-import-single-file-bytes", type=int, default=1_000_000)
    api.add_argument(
        "--native-build-policy",
        choices=["trusted", "disabled"],
        default="disabled",
    )

    args = parser.parse_args(argv)
    if args.command == "analyze":
        report = analyze_contract(
            contract_path=args.contract,
            output_dir=args.out_dir,
            trace_db=args.trace_db,
            dataset_chunks=args.dataset_chunks,
            rag_mode=args.rag_mode,
            model_path=args.model_path,
            external_tools=tuple(args.external_tool),
            external_timeout_seconds=args.external_timeout_seconds,
            native_build_policy=args.native_build_policy,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "import-source":
        limits = ImportLimits(
            max_files=args.max_files,
            max_total_bytes=args.max_total_bytes,
            max_single_file_bytes=args.max_single_file_bytes,
        )
        if args.zip_file is not None:
            imported = import_local_archive(
                archive_path=args.zip_file,
                destination_root=args.out_dir,
                limits=limits,
            )
        elif args.github_url is not None:
            imported = import_github_source(
                args.github_url,
                args.out_dir,
                limits=limits,
            )
        else:
            if not args.address:
                raise SystemExit("--address is required with --etherscan-api-host")
            imported = import_explorer_source(
                api_host=args.etherscan_api_host,
                address=args.address,
                destination_root=args.out_dir,
                api_key=args.api_key,
                limits=limits,
            )
        print(json.dumps(imported.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "clean-imports":
        removed = cleanup_import_staging(
            args.imports_dir,
            ttl_seconds=args.ttl_seconds,
        )
        print(
            json.dumps(
                {
                    "imports_dir": str(args.imports_dir),
                    "ttl_seconds": args.ttl_seconds,
                    "removed_count": len(removed),
                    "removed_paths": [str(path) for path in removed],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "clean-reports":
        chunks = []
        for path in sorted(args.raw_reports_dir.iterdir()):
            if path.is_file():
                chunks.extend(chunk_document(path, include_unknown=not args.filter_unknown))
        chunks = deduplicate_chunks(chunks)
        write_chunks(chunks, args.output_jsonl)
        print(json.dumps({"chunks": len(chunks), "output": str(args.output_jsonl)}, indent=2))
    elif args.command == "trace-lookup":
        rows = lookup_trace(args.trace_db, args.trace_id, args.finding_id)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif args.command == "trace-dashboard":
        rows = trace_dashboard(args.trace_db)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif args.command == "compare-reports":
        comparison = compare_report_files(args.base_report, args.head_report)
        markdown = render_comparison_markdown(comparison)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(markdown, encoding="utf-8")
        print(json.dumps(comparison, ensure_ascii=False, indent=2))
        if comparison_should_fail(
            comparison,
            fail_on_high_added=args.fail_on_high_added,
            fail_on_score_drop=args.fail_on_score_drop,
        ):
            raise SystemExit(2)
    elif args.command == "0g-package":
        result = build_proof_package(
            report_path=args.report,
            output_dir=args.out_dir,
            project_name=args.project_name,
            track=args.track,
        )
        print(
            json.dumps(
                {
                    "contract_id": result.contract_id,
                    "output_dir": str(result.output_dir),
                    "proof_json": str(result.proof_json),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "0g-attach-proof":
        proof = json.loads(args.proof.read_text(encoding="utf-8"))
        report = attach_zero_g_proof(args.report, proof)
        print(
            json.dumps(
                {"proof": str(args.proof.resolve()), "report": str(report.resolve())},
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "properties":
        from .properties import suggest_properties_for_report

        payload = suggest_properties_for_report(
            report_path=args.report,
            output_dir=args.out,
            output_format=args.format,
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.command == "mlx-probe":
        discovered_paths = []
        model_path = args.model_path
        if args.auto_discover_model and not model_path:
            discovered_paths = discover_mlx_model_paths(args.model_search_root)
            if discovered_paths:
                model_path = str(discovered_paths[0])
        probe = probe_mlx_runtime(
            MLXRuntimeConfig(
                model_path=model_path,
                quantization_bits=args.quantization_bits,
                max_tokens=args.max_tokens,
            ),
            parameter_count_billion=args.parameter_count_billion,
            prompt=args.prompt,
        )
        payload = probe.to_dict()
        payload["auto_discovered_model_path"] = (
            str(discovered_paths[0]) if discovered_paths else None
        )
        payload["discovered_model_paths"] = [str(path) for path in discovered_paths]
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif args.command == "web":
        from .web import launch

        launch(host=args.host, port=args.port)
    elif args.command == "api":
        from .http_api import run_api_server

        try:
            run_api_server(
                host=args.host,
                port=args.port,
                output_dir=args.out_dir,
                trace_db=args.trace_db,
                input_root=args.input_root,
                api_token=args.api_token,
                allow_tokenless_local_demo=args.allow_tokenless_local_demo,
                allow_any_input_root=args.allow_any_input_root,
                cors_origin=args.cors_origin,
                max_request_bytes=args.max_request_bytes,
                max_concurrent_jobs=args.max_concurrent_jobs,
                max_events_per_job=args.max_events_per_job,
                max_report_bytes=args.max_report_bytes,
                imports_dir=args.imports_dir,
                max_import_files=args.max_import_files,
                max_import_bytes=args.max_import_bytes,
                max_import_single_file_bytes=args.max_import_single_file_bytes,
                native_build_policy=args.native_build_policy,
            )
        except ValueError as exc:
            raise SystemExit(str(exc)) from exc
