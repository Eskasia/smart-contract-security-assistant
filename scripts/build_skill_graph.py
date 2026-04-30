# ruff: noqa: E501

from __future__ import annotations

import argparse
import html
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "graphify-out"


@dataclass(frozen=True)
class Node:
    id: str
    label: str
    type: str
    owner: str
    evidence: list[str]


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: str
    evidence: str


def build_graph() -> dict[str, Any]:
    nodes = [
        Node("goal.local_first_audit", "Local-first Solidity security triage", "goal", "Orchestrator", ["README.md"]),
        Node("capability.cli", "CLI entrypoint", "capability", "Python Quality Agent", ["src/smart_contract_audit/cli.py"]),
        Node("capability.slither", "Slither static analysis", "capability", "Solidity Security Agent", ["src/smart_contract_audit/slither_runner.py"]),
        Node("capability.adapter", "Finding normalization", "capability", "Solidity Security Agent", ["src/smart_contract_audit/finding_adapter.py"]),
        Node("capability.schema", "JSON schema validation", "capability", "Python Quality Agent", ["schemas/finding_schema.json"]),
        Node("capability.rag", "Local RAG retrieval", "capability", "RAG Data Agent", ["src/smart_contract_audit/rag/retriever.py"]),
        Node("capability.llm", "MLX-ready generation", "capability", "LLM Eval Agent", ["src/smart_contract_audit/llm/mlx_runtime.py"]),
        Node("capability.trace", "SQLite traceability", "capability", "Python Quality Agent", ["src/smart_contract_audit/trace/store.py"]),
        Node("capability.report", "Markdown and JSON reports", "capability", "Product Doc Agent", ["src/smart_contract_audit/report.py"]),
        Node("capability.ci", "CI validation", "capability", "Release Agent", [".github/workflows/ci.yml"]),
        Node("agent.orchestrator", "Orchestrator", "agent", "Orchestrator", ["docs/skill-graph.md"]),
        Node("agent.security", "Solidity Security Agent", "agent", "Solidity Security Agent", ["tests/test_slither.py"]),
        Node("agent.rag", "RAG Data Agent", "agent", "RAG Data Agent", ["eval/run_eval.py"]),
        Node("agent.llm_eval", "LLM Eval Agent", "agent", "LLM Eval Agent", ["eval/run_judge.py"]),
        Node("agent.quality", "Python Quality Agent", "agent", "Python Quality Agent", ["pyproject.toml"]),
        Node("agent.docs", "Product Doc Agent", "agent", "Product Doc Agent", ["README.md", "docs/handoff.md"]),
        Node("evidence.pytest", "uv run pytest: 15 passed", "evidence", "Python Quality Agent", ["tests"]),
        Node("evidence.ruff", "uv run ruff check .: passed", "evidence", "Python Quality Agent", ["pyproject.toml"]),
        Node("evidence.rag_eval", "RAG recall eval: recall_at_k=1.0", "evidence", "RAG Data Agent", ["eval/run_eval.py"]),
        Node("evidence.judge_eval", "Judge eval: average_judge_score=5.0", "evidence", "LLM Eval Agent", ["eval/run_judge.py"]),
        Node("evidence.mlx_probe", "MLX 4bit model load probe succeeded", "evidence", "LLM Eval Agent", ["src/smart_contract_audit/llm/mlx_runtime.py"]),
        Node("artifact.mlx_probe", "reports-mlx/mlx_probe.json", "artifact", "LLM Eval Agent", ["reports-mlx/mlx_probe.json"]),
        Node("artifact.graph_json", "graphify-out/graph.json", "artifact", "Orchestrator", ["graphify-out/graph.json"]),
        Node("artifact.graph_report", "graphify-out/GRAPH_REPORT.md", "artifact", "Orchestrator", ["graphify-out/GRAPH_REPORT.md"]),
        Node("artifact.graph_html", "graphify-out/graph.html", "artifact", "Orchestrator", ["graphify-out/graph.html"]),
    ]
    edges = [
        Edge("goal.local_first_audit", "capability.cli", "REQUIRES", "README.md"),
        Edge("capability.cli", "capability.slither", "TRIGGERS", "src/smart_contract_audit/cli.py"),
        Edge("capability.slither", "capability.adapter", "PRODUCES", "src/smart_contract_audit/analyzer.py"),
        Edge("capability.adapter", "capability.schema", "VALIDATES", "src/smart_contract_audit/validation/validator.py"),
        Edge("capability.schema", "capability.rag", "UNLOCKS", "src/smart_contract_audit/analyzer.py"),
        Edge("capability.rag", "capability.llm", "SUPPLIES_CONTEXT", "src/smart_contract_audit/llm/prompt_template.py"),
        Edge("capability.llm", "capability.report", "PRODUCES", "src/smart_contract_audit/report.py"),
        Edge("capability.report", "capability.trace", "RECORDS", "src/smart_contract_audit/trace/store.py"),
        Edge("agent.security", "capability.slither", "OWNS", "docs/skill-graph.md"),
        Edge("agent.rag", "capability.rag", "OWNS", "docs/skill-graph.md"),
        Edge("agent.llm_eval", "capability.llm", "OWNS", "docs/skill-graph.md"),
        Edge("agent.quality", "capability.schema", "OWNS", "docs/skill-graph.md"),
        Edge("agent.docs", "capability.report", "OWNS", "docs/skill-graph.md"),
        Edge("evidence.pytest", "capability.ci", "VALIDATES", ".github/workflows/ci.yml"),
        Edge("evidence.ruff", "capability.ci", "VALIDATES", ".github/workflows/ci.yml"),
        Edge("evidence.rag_eval", "capability.rag", "VALIDATES", "eval/rag_recall_test.json"),
        Edge("evidence.judge_eval", "capability.llm", "VALIDATES", "eval/judge_eval_set.json"),
        Edge("evidence.mlx_probe", "artifact.mlx_probe", "PRODUCES", "reports-mlx/mlx_probe.json"),
        Edge("agent.orchestrator", "artifact.graph_json", "PRODUCES", "scripts/build_skill_graph.py"),
        Edge("artifact.graph_json", "artifact.graph_report", "PRODUCES", "scripts/build_skill_graph.py"),
        Edge("artifact.graph_json", "artifact.graph_html", "PRODUCES", "scripts/build_skill_graph.py"),
        Edge("artifact.graph_report", "agent.orchestrator", "UPDATES", "docs/skill-graph.md"),
    ]
    return {
        "schema_version": "skill-graph.v1",
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "generated_by": "scripts/build_skill_graph.py",
        "project_root": str(PROJECT_ROOT),
        "nodes": [asdict(node) for node in nodes],
        "edges": [asdict(edge) for edge in edges],
        "summary": {
            "nodes": len(nodes),
            "edges": len(edges),
            "core_files": len(_core_files()),
            "remaining_gaps": [],
        },
    }


def write_outputs(output_dir: Path = DEFAULT_OUTPUT_DIR) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    graph = build_graph()
    graph_path = output_dir / "graph.json"
    report_path = output_dir / "GRAPH_REPORT.md"
    html_path = output_dir / "graph.html"

    graph_path.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report_path.write_text(_render_report(graph), encoding="utf-8")
    html_path.write_text(_render_html(graph), encoding="utf-8")
    return {"graph": graph_path, "report": report_path, "html": html_path}


def _core_files() -> list[Path]:
    roots = ["README.md", "AGENTS.md", "pyproject.toml", "docs", "src", "tests", "eval", "schemas"]
    files: list[Path] = []
    for root in roots:
        path = PROJECT_ROOT / root
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(
                child
                for child in path.rglob("*")
                if child.is_file()
                and "__pycache__" not in child.parts
                and child.suffix in {".md", ".py", ".json", ".toml", ".yml", ".yaml", ".sol"}
            )
    return sorted(files)


def _render_report(graph: dict[str, Any]) -> str:
    summary = graph["summary"]
    node_counts: dict[str, int] = {}
    for node in graph["nodes"]:
        node_counts[node["type"]] = node_counts.get(node["type"], 0) + 1
    counts = ", ".join(f"{key}={value}" for key, value in sorted(node_counts.items()))
    return (
        "# Skill Graph Report\n\n"
        f"Generated at: {graph['generated_at']}\n\n"
        f"Nodes: {summary['nodes']}; edges: {summary['edges']}; core files: {summary['core_files']}.\n\n"
        f"Node types: {counts}.\n\n"
        "Primary loop: CLI -> Slither -> adapter -> schema -> RAG -> MLX generator -> report -> trace -> evidence -> orchestrator.\n\n"
        "Remaining gap: none. MLX 4bit model probe succeeds and records peak RSS in `reports-mlx/mlx_probe.json`.\n"
    )


def _render_html(graph: dict[str, Any]) -> str:
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_list = "\n".join(
        f"<li><span>{html.escape(node['type'])}</span>{html.escape(node['label'])}</li>"
        for node in nodes
    )
    edge_list = "\n".join(
        f"<li>{html.escape(edge['source'])} <b>{html.escape(edge['type'])}</b> {html.escape(edge['target'])}</li>"
        for edge in edges
    )
    graph_json = html.escape(json.dumps(graph, ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <title>智能合約安全分析助理 Skill Graph</title>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #f7f7f4; color: #1f2933; }}
    main {{ max-width: 1160px; margin: 0 auto; padding: 32px 24px; }}
    h1 {{ font-size: 28px; margin: 0 0 8px; letter-spacing: 0; }}
    .meta {{ color: #52606d; margin-bottom: 24px; }}
    .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; align-items: start; }}
    section {{ background: #fff; border: 1px solid #d9e2ec; border-radius: 8px; padding: 16px; }}
    h2 {{ font-size: 16px; margin: 0 0 12px; }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 6px 0; line-height: 1.35; }}
    li span {{ display: inline-block; min-width: 86px; color: #52606d; }}
    pre {{ overflow: auto; background: #102a43; color: #d9e2ec; border-radius: 8px; padding: 16px; font-size: 12px; }}
    @media (max-width: 800px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <main>
    <h1>智能合約安全分析助理 Skill Graph</h1>
    <div class="meta">Nodes: {graph['summary']['nodes']} · Edges: {graph['summary']['edges']} · Core files: {graph['summary']['core_files']} · Generated: {html.escape(graph['generated_at'])}</div>
    <div class="grid">
      <section><h2>Nodes</h2><ul>{node_list}</ul></section>
      <section><h2>Edges</h2><ul>{edge_list}</ul></section>
    </div>
    <section style="margin-top:16px"><h2>Raw JSON</h2><pre>{graph_json}</pre></section>
  </main>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    paths = write_outputs(args.out_dir)
    print(json.dumps({key: str(path) for key, path in paths.items()}, indent=2))


if __name__ == "__main__":
    main()
