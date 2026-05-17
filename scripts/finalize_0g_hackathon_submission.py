#!/usr/bin/env python3
"""Finalize 0G APAC Hackathon proof fields after a live 0G mainnet run."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO_URL = "https://eskasia.github.io/smart-contract-security-assistant/"
DEMO_VIDEO_URL = (
    "https://eskasia.github.io/smart-contract-security-assistant/scsa-usage-tutorial.mp4?v=7aa1ab4"
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run(args: list[str], cwd: Path = ROOT, env: dict[str, str] | None = None) -> str:
    process = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        print(process.stdout, file=sys.stderr)
        print(process.stderr, file=sys.stderr)
        fail(f"command failed: {' '.join(args)}")
    return process.stdout.strip()


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        fail(
            f"{name} is required. Use a funded 0G Mainnet wallet; dry-run proof is not valid."
        )
    return value


def json_from_stdout(stdout: str, command_name: str) -> dict:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError as exc:
        fail(f"{command_name} did not return JSON: {exc}")


def replace_line_after_label(text: str, label: str, value: str) -> str:
    prefix = f"{label}:"
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = f"{prefix} {value}"
            return "\n".join(lines) + "\n"
    fail(f"label not found: {label}")


def update_markdown_table(path: Path, values: dict[str, str]) -> None:
    text = path.read_text()
    for field, value in values.items():
        text = text.replace(f"| {field} |  |", f"| {field} | {value} |")
    path.write_text(text)


def update_submission_markdown(path: Path, values: dict[str, str]) -> None:
    text = path.read_text()
    labels = {
        "Registry contract address": values["Registry contract address"],
        "Registry explorer link": values["Registry explorer link"],
        "Storage root hash": values["Storage root hash"],
        "Storage upload transaction": values["Storage upload transaction"],
        "Storage explorer link": values["Storage explorer link"],
        "Proof registration transaction": values["Proof registration transaction"],
        "Proof registration explorer link": values["Proof registration explorer link"],
    }
    for label, value in labels.items():
        text = replace_line_after_label(text, label, value)
    path.write_text(text)


def update_hackquest_json(path: Path, proof: dict, public_x_post_url: str) -> None:
    data = json.loads(path.read_text())
    data["repository_visibility"] = "public"
    data["frontend_demo_url"] = DEMO_URL
    data["demo_video_url"] = DEMO_VIDEO_URL
    data["public_x_post_url"] = public_x_post_url
    zero_g = data["zero_g_integration_proof"]
    zero_g["proof_mode"] = "live_registered"
    zero_g["registry_contract_address"] = proof["registry_address"]
    zero_g["registry_explorer_link"] = proof["explorer_links"]["registry"]
    zero_g["storage_root_hash"] = proof["storage_root_hash"]
    zero_g["storage_upload_transaction"] = proof["storage_tx_hash"]
    zero_g["storage_explorer_link"] = proof["explorer_links"]["storage_tx"]
    zero_g["proof_registration_transaction"] = proof["registry_tx_hash"]
    zero_g["proof_registration_explorer_link"] = proof["explorer_links"]["registration_tx"]
    data["reviewer_notes"]["live_proof_record"] = (
        "Live 0G proof was generated and verified by scripts/finalize_0g_hackathon_submission.py."
    )
    path.write_text(json.dumps(data, indent=2) + "\n")


def sync_submission_folder() -> None:
    copies = {
        ROOT / "README.hackathon.md": ROOT
        / "submission/0g-apac-hackathon/README.hackathon.md",
        ROOT / "docs/hackathon/0g-apac-submission.md": ROOT
        / "submission/0g-apac-hackathon/hackquest-submission.md",
        ROOT / "docs/hackathon/hackquest-submission.form.json": ROOT
        / "submission/0g-apac-hackathon/hackquest-submission.form.json",
        ROOT / "docs/hackathon/004-live-0g-proof-record.md": ROOT
        / "submission/0g-apac-hackathon/live-0g-proof-record.md",
        ROOT / "docs/hackathon/003-submission-package-index.md": ROOT
        / "submission/0g-apac-hackathon/submission-package-index.md",
    }
    for source, target in copies.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def main() -> None:
    private_key = require_env("ZERO_G_PRIVATE_KEY")
    public_x_post_url = os.environ.get("PUBLIC_X_POST_URL", "").strip()
    if not public_x_post_url:
        fail("PUBLIC_X_POST_URL is required after publishing the mandatory X post.")

    env = os.environ.copy()
    env.update(
        {
            "ZERO_G_RPC_URL": env.get("ZERO_G_RPC_URL", "https://evmrpc.0g.ai"),
            "ZERO_G_PRIVATE_KEY": private_key,
            "ZERO_G_STORAGE_INDEXER_RPC": env.get(
                "ZERO_G_STORAGE_INDEXER_RPC", "https://indexer-storage-turbo.0g.ai"
            ),
            "ZERO_G_CHAIN_EXPLORER_TX_BASE": env.get(
                "ZERO_G_CHAIN_EXPLORER_TX_BASE", "https://chainscan.0g.ai/tx/"
            ),
            "ZERO_G_CHAIN_EXPLORER_ADDRESS_BASE": env.get(
                "ZERO_G_CHAIN_EXPLORER_ADDRESS_BASE", "https://chainscan.0g.ai/address/"
            ),
            "ZERO_G_STORAGE_EXPLORER_BASE": env.get(
                "ZERO_G_STORAGE_EXPLORER_BASE", "https://storagescan.0g.ai/"
            ),
        }
    )

    reports = ROOT / "reports"
    proof_root = ROOT / "reports-0g"
    reports.mkdir(exist_ok=True)

    analysis_json = reports / "latest-analysis.json"
    analysis_output = run(
        [
            "uv",
            "run",
            "scsa",
            "analyze",
            "tests/contracts/VulnerableVault.sol",
            "--out-dir",
            str(reports),
            "--native-build-policy",
            "disabled",
        ],
        env=env,
    )
    analysis_json.write_text(analysis_output + "\n")
    analysis = json.loads(analysis_output)
    report_id = analysis["contract_id"]

    run(
        [
            "uv",
            "run",
            "scsa",
            "0g-package",
            str(analysis_json),
            "--out-dir",
            str(proof_root),
            "--project-name",
            "SCSA 0G Audit Proof",
            "--track",
            "Track 1: Agentic Infrastructure & OpenClaw Lab",
        ],
        env=env,
    )

    zero_g = ROOT / "integrations/0g"
    run(["npm", "install"], cwd=zero_g, env=env)
    deploy = json_from_stdout(
        run(["npm", "run", "deploy", "--silent"], cwd=zero_g, env=env),
        "deploy",
    )
    env["ZERO_G_REGISTRY_ADDRESS"] = deploy["registry_address"]

    audit_proof = proof_root / report_id / "audit-proof.json"
    submission_proof = proof_root / report_id / "submission-proof.json"
    run(["npm", "run", "upload", "--silent", "--", str(audit_proof)], cwd=zero_g, env=env)
    run(["npm", "run", "register", "--silent", "--", str(submission_proof)], cwd=zero_g, env=env)
    run(
        ["npm", "run", "verify-proof", "--silent", "--", str(submission_proof)],
        cwd=zero_g,
        env=env,
    )
    run(
        [
            "uv",
            "run",
            "scsa",
            "0g-attach-proof",
            str(analysis_json),
            str(submission_proof),
        ],
        env=env,
    )

    proof = json.loads(submission_proof.read_text())
    values = {
        "Registry contract address": proof["registry_address"],
        "Registry explorer link": proof["explorer_links"]["registry"],
        "Storage root hash": proof["storage_root_hash"],
        "Storage upload transaction": proof["storage_tx_hash"],
        "Storage explorer link": proof["explorer_links"]["storage_tx"],
        "Proof registration transaction": proof["registry_tx_hash"],
        "Proof registration explorer link": proof["explorer_links"]["registration_tx"],
        "`submission-proof.json` path": str(submission_proof.relative_to(ROOT)),
        "Demo report path": str(analysis_json.relative_to(ROOT)),
    }

    update_markdown_table(ROOT / "docs/hackathon/004-live-0g-proof-record.md", values)
    update_submission_markdown(ROOT / "docs/hackathon/0g-apac-submission.md", values)
    update_hackquest_json(
        ROOT / "docs/hackathon/hackquest-submission.form.json", proof, public_x_post_url
    )
    sync_submission_folder()
    print(json.dumps({"ok": True, "report_id": report_id, "proof": values}, indent=2))


if __name__ == "__main__":
    main()
