from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .analyzer import analyze_contract


def launch(host: str = "127.0.0.1", port: int = 7860) -> None:
    try:
        import gradio as gr
    except ImportError as exc:
        raise RuntimeError("Gradio UI requires `uv sync --extra web`.") from exc

    def analyze_file(file_obj, rag_mode: str) -> tuple[str, str]:
        if file_obj is None:
            return "No file uploaded.", ""
        source_path = Path(file_obj.name)
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp) / "reports"
            report = analyze_contract(source_path, output_dir=output_dir, rag_mode=rag_mode)
            markdown = (output_dir / f"{report.contract_id}.md").read_text(encoding="utf-8")
            return markdown, json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

    with gr.Blocks(title="Smart Contract Security Assistant") as demo:
        gr.Markdown("# Smart Contract Security Assistant")
        with gr.Row():
            contract = gr.File(label="Solidity file", file_types=[".sol"])
            rag_mode = gr.Dropdown(["quality", "balanced", "fast", "fallback"], value="balanced")
        run = gr.Button("Analyze")
        markdown = gr.Markdown()
        raw_json = gr.Code(language="json")
        run.click(analyze_file, inputs=[contract, rag_mode], outputs=[markdown, raw_json])

    demo.launch(server_name=host, server_port=port)
