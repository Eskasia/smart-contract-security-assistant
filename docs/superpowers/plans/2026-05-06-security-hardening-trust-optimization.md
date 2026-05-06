# Security Hardening and Trust Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Raise professional trust by hardening the local API boundary, reducing untrusted native build risk, and expanding evaluation coverage.

**Architecture:** Keep the analyzer deterministic and local-first. Add explicit trust boundaries at the HTTP API and native build layers, then expand benchmark reporting so product claims are backed by reproducible metrics.

**Tech Stack:** Python stdlib HTTP server, pytest, Slither, Foundry, Hardhat, existing React/Vite frontend, existing eval harness.

---

## File Structure

- Modify: `src/smart_contract_audit/http_api.py` — API auth, CORS, request size, and allowed input path checks.
- Modify: `src/smart_contract_audit/cli.py` — expose API hardening flags and native build policy flags.
- Modify: `src/smart_contract_audit/analyzer.py` — pass native build policy into Slither runner.
- Modify: `src/smart_contract_audit/slither_runner.py` — gate native build execution with a policy.
- Modify: `src/smart_contract_audit/evaluation/public_benchmark.py` — add false positive, false negative, precision, recall, and F1 summary fields.
- Modify: `eval/run_public_benchmark.py` — expose output and threshold flags for the new metrics.
- Modify: `frontend/src` files that create analysis requests — send API token when configured and surface policy validation errors.
- Test: `tests/test_http_api.py` — API hardening regression tests.
- Test: `tests/test_slither.py` — native build policy regression tests.
- Test: `tests/test_public_benchmark.py` — benchmark metric regression tests.
- Docs: `README.md`, `README.en.md`, `docs/handoff.md`, `docs/guides/001-usage-manual.md`, `docs/review_checklist.md`.

---

### Task 1: API Request Boundary

**Files:**
- Modify: `src/smart_contract_audit/http_api.py`
- Modify: `src/smart_contract_audit/cli.py`
- Modify: `tests/test_http_api.py`

- [ ] **Step 1: Write failing tests for token auth, body limit, CORS origin, and input root**

Append these tests to `tests/test_http_api.py`:

```python
def test_http_api_requires_token_when_configured(tmp_path: Path) -> None:
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=tmp_path / "reports", api_token="dev-token"),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": "Vault.sol"},
            expect_error=401,
        )
        assert error["error"]["code"] == "UNAUTHORIZED"

        created = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": "Vault.sol"},
            headers={"Authorization": "Bearer dev-token"},
            expect_error=422,
        )
        assert created["error"]["code"] == "VALIDATION_ERROR"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_rejects_oversized_json_body(tmp_path: Path) -> None:
    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=tmp_path / "reports", max_request_bytes=8),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": "Vault.sol"},
            expect_error=413,
        )
        assert error["error"]["code"] == "REQUEST_TOO_LARGE"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_http_api_rejects_input_outside_allowed_root(tmp_path: Path) -> None:
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside" / "Vault.sol"
    allowed.mkdir()
    outside.parent.mkdir()
    outside.write_text("pragma solidity ^0.8.19; contract Vault {}", encoding="utf-8")

    server = create_api_server(
        host="127.0.0.1",
        port=0,
        config=ApiConfig(output_dir=tmp_path / "reports", input_root=allowed),
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        error = _json_request(
            f"{base_url}/api/analyses",
            method="POST",
            payload={"input_path": str(outside)},
            expect_error=422,
        )
        assert error["error"]["code"] == "VALIDATION_ERROR"
        assert "input_root" in error["error"]["message"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
```

Update `_json_request()` signature in `tests/test_http_api.py`:

```python
def _json_request(
    url: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    expect_error: int | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers=request_headers,
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            assert expect_error is None
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if expect_error is None:
            raise
        assert exc.code == expect_error
        return json.loads(exc.read().decode("utf-8"))
```

- [ ] **Step 2: Run the tests and verify they fail**

Run:

```bash
uv run pytest tests/test_http_api.py -q
```

Expected: failures mention missing `api_token`, `max_request_bytes`, or `input_root` fields.

- [ ] **Step 3: Add API config fields and authorization checks**

Modify `ApiConfig` in `src/smart_contract_audit/http_api.py`:

```python
@dataclass(frozen=True)
class ApiConfig:
    output_dir: Path = Path("reports-api")
    trace_db: Path | None = None
    input_root: Path | None = None
    api_token: str | None = None
    cors_origin: str = "http://127.0.0.1:5173"
    max_request_bytes: int = 1_048_576

    def resolved_trace_db(self) -> Path:
        return self.trace_db or self.output_dir / "analysis_trace.sqlite"
```

Add this helper to `_SmartContractAPIHandler`:

```python
def _authorize_request(self) -> bool:
    token = self.server.config.api_token
    if not token:
        return True
    if self.headers.get("Authorization", "") == f"Bearer {token}":
        return True
    self._send_error_response(HTTPStatus.UNAUTHORIZED, "UNAUTHORIZED", "Invalid API token.")
    return False
```

Call it at the start of `do_POST`, `do_GET`, and `do_PATCH`:

```python
if not self._authorize_request():
    return
```

- [ ] **Step 4: Add request size, CORS, and input root validation**

Modify `_read_json_body()`:

```python
try:
    length = int(self.headers.get("Content-Length", "0"))
except ValueError as exc:
    raise ValueError("Invalid Content-Length.") from exc
if length > self.server.config.max_request_bytes:
    raise RequestBodyTooLarge("Request body exceeds max_request_bytes.")
if length <= 0:
    return {}
```

Add the exception class near constants:

```python
class RequestBodyTooLarge(ValueError):
    pass
```

Catch it in `do_POST` and `do_PATCH`:

```python
except RequestBodyTooLarge as exc:
    self._send_error_response(
        HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        "REQUEST_TOO_LARGE",
        str(exc),
    )
    return
```

Modify `_send_common_headers()`:

```python
origin = self.server.config.cors_origin
if origin:
    self.send_header("Access-Control-Allow-Origin", origin)
    self.send_header("Vary", "Origin")
self.send_header("X-Content-Type-Options", "nosniff")
```

Add this helper:

```python
def _validate_allowed_input_path(input_path: str, input_root: Path | None) -> str:
    resolved = Path(input_path).expanduser().resolve()
    if input_root is None:
        return str(resolved)
    root = input_root.expanduser().resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"input_path must be inside input_root: {root}")
    return str(resolved)
```

Change `_parse_create_analysis()` signature and call:

```python
def _parse_create_analysis(payload: dict[str, Any], input_root: Path | None = None) -> dict[str, Any]:
    ...
    input_path = _validate_allowed_input_path(input_path, input_root)
```

Change `AnalysisJobManager.create_job()`:

```python
request = _parse_create_analysis(payload, self.config.input_root)
```

- [ ] **Step 5: Add CLI flags**

Modify `src/smart_contract_audit/cli.py` API parser:

```python
api.add_argument("--input-root", type=Path, default=None)
api.add_argument("--api-token", default=None)
api.add_argument("--cors-origin", default="http://127.0.0.1:5173")
api.add_argument("--max-request-bytes", type=int, default=1_048_576)
```

Pass them to `run_api_server()` and update that function signature in `http_api.py`:

```python
def run_api_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    output_dir: Path = Path("reports-api"),
    trace_db: Path | None = None,
    input_root: Path | None = None,
    api_token: str | None = None,
    cors_origin: str = "http://127.0.0.1:5173",
    max_request_bytes: int = 1_048_576,
) -> None:
    server = create_api_server(
        host=host,
        port=port,
        config=ApiConfig(
            output_dir=output_dir,
            trace_db=trace_db,
            input_root=input_root,
            api_token=api_token,
            cors_origin=cors_origin,
            max_request_bytes=max_request_bytes,
        ),
    )
```

- [ ] **Step 6: Verify and commit**

Run:

```bash
uv run pytest tests/test_http_api.py -q
uv run ruff check .
git add src/smart_contract_audit/http_api.py src/smart_contract_audit/cli.py tests/test_http_api.py
git commit -m "fix: harden local api request boundary"
```

Expected: all tests pass.

---

### Task 2: Native Build Policy

**Files:**
- Modify: `src/smart_contract_audit/analyzer.py`
- Modify: `src/smart_contract_audit/slither_runner.py`
- Modify: `src/smart_contract_audit/http_api.py`
- Modify: `src/smart_contract_audit/cli.py`
- Modify: `tests/test_slither.py`
- Modify: `tests/test_http_api.py`

- [ ] **Step 1: Write failing native build policy tests**

Append to `tests/test_slither.py`:

```python
def test_slither_can_disable_native_build_for_untrusted_projects(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "foundry"
    source_dir = project / "src"
    source_dir.mkdir(parents=True)
    (project / "foundry.toml").write_text('[profile.default]\nsrc = "src"\n', encoding="utf-8")
    (source_dir / "Vault.sol").write_text(
        "pragma solidity ^0.8.19;\ncontract Vault {}\n",
        encoding="utf-8",
    )
    commands: list[list[str]] = []

    def fake_which(name: str) -> str | None:
        return {"forge": "forge", "slither": "slither", "solc": "solc"}.get(name)

    def fake_run(
        command: list[str],
        check: bool = False,
        capture_output: bool = True,
        text: bool = True,
        timeout: int = 15,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if command[0] == "solc":
            return subprocess.CompletedProcess(command, 0, stdout="Version: 0.8.34", stderr="")
        if command[:2] == ["slither", "--version"]:
            return subprocess.CompletedProcess(command, 0, stdout="0.11.5", stderr="")
        if command[0] == "slither":
            output_path = Path(command[command.index("--json") + 1])
            output_path.write_text(
                '{"success": true, "results": {"detectors": []}}',
                encoding="utf-8",
            )
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
        raise AssertionError(f"unexpected command: {command}")

    monkeypatch.setattr("smart_contract_audit.slither_runner.shutil.which", fake_which)
    monkeypatch.setattr("smart_contract_audit.slither_runner.subprocess.run", fake_run)

    result = run_slither(project, native_build_policy="disabled")

    assert not any(command[0] == "forge" for command in commands)
    assert any("--compile-force-framework" in command for command in commands if command[0] == "slither")
    assert "Native build disabled by policy." in result.warnings
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
uv run pytest tests/test_slither.py::test_slither_can_disable_native_build_for_untrusted_projects -q
```

Expected: failure says `run_slither()` does not accept `native_build_policy`.

- [ ] **Step 3: Implement the policy in Slither runner**

Modify `run_slither()` signature:

```python
def run_slither(
    contract_path: Path,
    timeout_seconds: int = 300,
    native_build_policy: str = "trusted",
) -> SlitherRunResult:
```

Replace native build assignment:

```python
native_build = prepare_native_build(target, timeout_seconds, native_build_policy)
```

Modify `prepare_native_build()` signature and first branch:

```python
def prepare_native_build(
    target: SolidityTarget,
    timeout_seconds: int = 90,
    native_build_policy: str = "trusted",
) -> NativeBuildResult:
    if native_build_policy not in {"trusted", "disabled"}:
        return NativeBuildResult(
            attempted=False,
            succeeded=False,
            tool_name=target.project_type,
            summary=f"Unsupported native build policy: {native_build_policy}.",
        )
    if native_build_policy == "disabled":
        return NativeBuildResult(
            attempted=False,
            succeeded=False,
            tool_name=target.project_type,
            summary="Native build disabled by policy.",
        )
    if target.project_type not in {"foundry", "hardhat"}:
        return NativeBuildResult(False, False, "", "")
```

- [ ] **Step 4: Pass policy through analyzer and API**

Modify `analyze_contract()` signature in `src/smart_contract_audit/analyzer.py`:

```python
native_build_policy: str = "trusted",
```

Change Slither call:

```python
slither_result = slither_runner(
    context.target.input_path,
    native_build_policy=native_build_policy,
)
```

Add `native_build_policy` to `AnalysisJob`, `_parse_create_analysis()`, and `_run_job()` in `http_api.py`:

```python
NATIVE_BUILD_POLICIES = {"trusted", "disabled"}
```

```python
native_build_policy = payload.get("native_build_policy", "trusted")
if native_build_policy not in NATIVE_BUILD_POLICIES:
    raise ValueError("native_build_policy must be one of: disabled, trusted.")
```

```python
native_build_policy=job.native_build_policy,
```

- [ ] **Step 5: Add CLI flags**

Add to `scsa analyze` parser:

```python
analyze.add_argument(
    "--native-build-policy",
    choices=["trusted", "disabled"],
    default="trusted",
)
```

Pass into `analyze_contract()`:

```python
native_build_policy=args.native_build_policy,
```

Add to API parser:

```python
api.add_argument(
    "--native-build-policy",
    choices=["trusted", "disabled"],
    default="trusted",
)
```

- [ ] **Step 6: Verify and commit**

Run:

```bash
uv run pytest tests/test_slither.py tests/test_http_api.py -q
uv run ruff check .
git add src/smart_contract_audit/analyzer.py src/smart_contract_audit/slither_runner.py src/smart_contract_audit/http_api.py src/smart_contract_audit/cli.py tests/test_slither.py tests/test_http_api.py
git commit -m "feat: add native build trust policy"
```

Expected: all selected tests pass.

---

### Task 3: Frontend Trust Controls

**Files:**
- Modify: `frontend/src` request/config files used by analysis submission.
- Modify: frontend tests near the analysis form/store.
- Modify: `README.md`
- Modify: `README.en.md`

- [ ] **Step 1: Locate frontend request owner**

Run:

```bash
rg -n "POST /api/analyses|api/analyses|fetch\\(" frontend/src
```

Expected: one request path that builds the analysis payload.

- [ ] **Step 2: Add failing frontend test**

Add a test in the existing frontend test file that verifies payload contains `native_build_policy: "disabled"` when the user selects safe mode, and that `Authorization: Bearer dev-token` is sent when an API token is configured.

Use this assertion shape:

```ts
expect(fetchMock).toHaveBeenCalledWith(
  expect.stringContaining('/api/analyses'),
  expect.objectContaining({
    method: 'POST',
    headers: expect.objectContaining({
      Authorization: 'Bearer dev-token',
    }),
    body: expect.stringContaining('"native_build_policy":"disabled"'),
  }),
)
```

- [ ] **Step 3: Implement UI and request changes**

Add a two-option control near analysis settings:

```ts
const nativeBuildOptions = [
  { value: 'trusted', label: 'Trusted project build' },
  { value: 'disabled', label: 'Safe fallback' },
] as const
```

The submitted JSON body must include:

```ts
native_build_policy: settings.nativeBuildPolicy,
```

The request headers must include:

```ts
...(settings.apiToken ? { Authorization: `Bearer ${settings.apiToken}` } : {}),
```

- [ ] **Step 4: Verify and commit**

Run:

```bash
cd frontend && npm run test && npm run build
git add frontend README.md README.en.md
git commit -m "feat: expose trust controls in frontend"
```

Expected: frontend tests and build pass.

---

### Task 4: Benchmark Trust Metrics

**Files:**
- Modify: `src/smart_contract_audit/evaluation/public_benchmark.py`
- Modify: `tests/test_public_benchmark.py`
- Modify: `docs/review_checklist.md`
- Modify: `docs/reference/001-validation-procedure-log.md`

- [ ] **Step 1: Write failing metric tests**

Append to `tests/test_public_benchmark.py`:

```python
def test_public_benchmark_summary_includes_confusion_metrics(tmp_path: Path) -> None:
    results = [
        {"external_class": "safe", "detected_supported_labels": [], "expected_supported_labels": []},
        {"external_class": "safe", "detected_supported_labels": ["reentrancy"], "expected_supported_labels": []},
        {"external_class": "vulnerable", "detected_supported_labels": ["reentrancy"], "expected_supported_labels": ["reentrancy"]},
        {"external_class": "vulnerable", "detected_supported_labels": [], "expected_supported_labels": ["reentrancy"]},
    ]

    summary = summarize_public_benchmark_results(results)

    assert summary["confusion_matrix"] == {
        "true_positive": 1,
        "true_negative": 1,
        "false_positive": 1,
        "false_negative": 1,
    }
    assert summary["classification_metrics"] == {
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```bash
uv run pytest tests/test_public_benchmark.py::test_public_benchmark_summary_includes_confusion_metrics -q
```

Expected: failure says `summarize_public_benchmark_results` is missing or summary fields are missing.

- [ ] **Step 3: Extract and implement summary function**

Add to `src/smart_contract_audit/evaluation/public_benchmark.py`:

```python
def summarize_public_benchmark_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    true_positive = true_negative = false_positive = false_negative = 0
    for result in results:
        expected_vulnerable = result.get("external_class") == "vulnerable"
        detected_vulnerable = bool(result.get("detected_supported_labels"))
        if expected_vulnerable and detected_vulnerable:
            true_positive += 1
        elif expected_vulnerable and not detected_vulnerable:
            false_negative += 1
        elif not expected_vulnerable and detected_vulnerable:
            false_positive += 1
        else:
            true_negative += 1

    precision = _safe_ratio(true_positive, true_positive + false_positive)
    recall = _safe_ratio(true_positive, true_positive + false_negative)
    f1 = _safe_ratio(2 * precision * recall, precision + recall)
    return {
        "confusion_matrix": {
            "true_positive": true_positive,
            "true_negative": true_negative,
            "false_positive": false_positive,
            "false_negative": false_negative,
        },
        "classification_metrics": {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
        },
    }


def _safe_ratio(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0
```

Merge this into the existing summary returned by `run_public_benchmark()`.

- [ ] **Step 4: Add thresholds**

Add CLI flags to `eval/run_public_benchmark.py`:

```python
parser.add_argument("--min-precision", type=float, default=0.0)
parser.add_argument("--min-recall", type=float, default=0.0)
parser.add_argument("--min-f1", type=float, default=0.0)
```

Enforce after summary:

```python
metrics = summary["classification_metrics"]
if metrics["precision"] < args.min_precision:
    raise SystemExit(f"precision {metrics['precision']} below threshold {args.min_precision}")
if metrics["recall"] < args.min_recall:
    raise SystemExit(f"recall {metrics['recall']} below threshold {args.min_recall}")
if metrics["f1"] < args.min_f1:
    raise SystemExit(f"f1 {metrics['f1']} below threshold {args.min_f1}")
```

- [ ] **Step 5: Verify and commit**

Run:

```bash
uv run pytest tests/test_public_benchmark.py -q
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5
uv run ruff check .
git add src/smart_contract_audit/evaluation/public_benchmark.py eval/run_public_benchmark.py tests/test_public_benchmark.py docs/review_checklist.md docs/reference/001-validation-procedure-log.md
git commit -m "feat: add benchmark trust metrics"
```

Expected: benchmark prints `confusion_matrix` and `classification_metrics`.

---

### Task 5: Release Verification and Documentation

**Files:**
- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `docs/handoff.md`
- Modify: `docs/guides/001-usage-manual.md`
- Modify: `docs/review_checklist.md`
- Modify: `docs/reference/001-validation-procedure-log.md`

- [ ] **Step 1: Update usage docs with exact hardening commands**

Add this command block to the API section:

```bash
uv run scsa api \
  --host 127.0.0.1 \
  --port 8787 \
  --out-dir reports-api \
  --input-root "$PWD" \
  --api-token dev-token \
  --cors-origin http://127.0.0.1:5173 \
  --max-request-bytes 1048576 \
  --native-build-policy disabled
```

Add this sentence:

```markdown
`--native-build-policy disabled` skips Foundry/Hardhat build scripts for untrusted projects and uses Slither/solc fallback.
```

- [ ] **Step 2: Update review checklist gates**

Add these gates to `docs/review_checklist.md`:

```markdown
| API boundary | Token auth, `input_root`, body limit, and non-wildcard CORS tests pass |
| Native build safety | Untrusted API mode uses `--native-build-policy disabled`; trusted CLI mode keeps native build support |
| Benchmark metrics | Public benchmark summary includes confusion matrix, precision, recall, and F1 |
```

- [ ] **Step 3: Run full verification**

Run:

```bash
uv run ruff check .
uv run pytest
cd frontend && npm run test && npm run build
uv run python eval/run_public_benchmark.py --min-supported-hit-rate 0.95 --min-score-gap 30 --min-recall 0.5 --min-f1 0.5
uv run python eval/run_public_project_builds.py --preflight-only
```

Expected:

```text
ruff: All checks passed
pytest: all tests passed
frontend: all tests passed and build completed
public benchmark: thresholds passed
public project preflight: missing_required_tools = []
```

- [ ] **Step 4: Commit docs and final verification record**

Run:

```bash
git add README.md README.en.md docs/handoff.md docs/guides/001-usage-manual.md docs/review_checklist.md docs/reference/001-validation-procedure-log.md
git commit -m "docs: document hardening and trust verification"
```

Expected: clean commit.

---

## Self-Review

- Spec coverage: API hardening is Task 1; untrusted native build reduction is Task 2; frontend operator controls are Task 3; benchmark trust metrics are Task 4; user-facing docs and release verification are Task 5.
- Placeholder scan: no placeholder wording or undefined task references remain.
- Type consistency: `native_build_policy` uses `"trusted"` and `"disabled"` in CLI, API, analyzer, and Slither runner.

## Execution Options

1. Subagent-Driven: run one worker per task, review each task before the next task.
2. Inline Execution: run tasks in this session using `superpowers:executing-plans`, with verification after each task.
