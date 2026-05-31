import importlib.util
import sys
from pathlib import Path


def _load_build_graph():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_knowledge_graph.py"
    spec = importlib.util.spec_from_file_location("build_knowledge_graph", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.build_graph


def test_knowledge_graph_contains_required_artifacts_and_validation_edges() -> None:
    build_graph = _load_build_graph()
    graph = build_graph()
    node_ids = {node["id"] for node in graph["nodes"]}
    edges = {(edge["source"], edge["target"], edge["type"]) for edge in graph["edges"]}

    assert "artifact.graph_json" in node_ids
    assert "artifact.graph_report" in node_ids
    assert "artifact.graph_html" in node_ids
    assert ("evidence.pytest", "capability.ci", "VALIDATES") in edges
    assert ("evidence.rag_eval", "capability.rag", "VALIDATES") in edges
    assert graph["schema_version"] == "scsa-knowledge-graph.v1"
    assert graph["summary"]["remaining_gaps"] == []
