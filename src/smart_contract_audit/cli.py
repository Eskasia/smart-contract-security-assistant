from __future__ import annotations

import argparse
import json
from pathlib import Path

from .analyzer import analyze_contract
from .llm.mlx_runtime import MLXRuntimeConfig, discover_mlx_model_paths, probe_mlx_runtime
from .rag.chunker import chunk_document
from .rag.indexer import write_chunks
from .trace.lookup import lookup_trace


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

    clean = subparsers.add_parser("clean-reports", help="Extract and chunk raw reports into JSONL.")
    clean.add_argument("raw_reports_dir", type=Path)
    clean.add_argument("output_jsonl", type=Path)

    lookup = subparsers.add_parser("trace-lookup", help="Lookup trace rows.")
    lookup.add_argument("trace_db", type=Path)
    lookup.add_argument("trace_id")
    lookup.add_argument("--finding-id")

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

    args = parser.parse_args(argv)
    if args.command == "analyze":
        report = analyze_contract(
            contract_path=args.contract,
            output_dir=args.out_dir,
            trace_db=args.trace_db,
            dataset_chunks=args.dataset_chunks,
            rag_mode=args.rag_mode,
            model_path=args.model_path,
        )
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    elif args.command == "clean-reports":
        chunks = []
        for path in sorted(args.raw_reports_dir.iterdir()):
            if path.is_file():
                chunks.extend(chunk_document(path))
        write_chunks(chunks, args.output_jsonl)
        print(json.dumps({"chunks": len(chunks), "output": str(args.output_jsonl)}, indent=2))
    elif args.command == "trace-lookup":
        rows = lookup_trace(args.trace_db, args.trace_id, args.finding_id)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
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
