# 智能合約安全分析助理 v0.8

## 專案定位

面向 Solidity 智能合約的 AI 輔助審計工具——漏洞初篩與審計報告生成助手。開發者上傳 `.sol` 檔，系統自動執行靜態分析、檢索相關漏洞知識，並生成結構化報告與可追溯的修復建議。

核心原則：靜態分析負責漏洞判定，LLM 負責解釋生成與修復建議。兩者 confidence 獨立計算，不混用。

v1.0 目標不是取代正式審計，而是建立一個能在 MacBook Pro M2 Pro / 16GB 統一記憶體環境中穩定運行、可展示、可追蹤、可驗證的安全分析 MVP。

---

## MVP v1.0 範圍

### 輸入約束

| 約束 | 值 | 理由 |
|---|---|---|
| 檔案格式 | 單檔 `.sol` | 多檔分析需 import resolution，延至 v1.1 |
| 行數上限 | 500 行，含空行與註解 | 所選 8B 模型有效上下文以 8K tokens 作為 MVP 預算基準；500 行 Solidity 約 2K–3K tokens，預留 RAG context 與輸出空間 |
| Solidity 版本 | 0.6.x–0.8.x | Slither 支援較穩定 |
| 介面 | CLI 優先，Gradio Web UI 後段補上 | CLI 先確保核心流程可跑，Gradio 作為展示層 |

### 支援漏洞類型

| 漏洞類型 | Slither Detector(s) | 分類來源 |
|---|---|---|
| Reentrancy | `reentrancy-eth`, `reentrancy-no-eth`, `reentrancy-benign` | SWC-107 |
| Access Control | `unprotected-upgrade`, `suicidal`, `arbitrary-send-eth` | SWC-105, SWC-106 |
| Unchecked External Call | `unchecked-lowlevel`, `unchecked-send` | SWC-104 |
| Dangerous Delegatecall | `controlled-delegatecall`, `delegatecall-loop` | SWC-112 |
| Array Length Manipulation | `controlled-array-length` | Slither-specific |

Integer Overflow / Underflow 延後至 v1.1，由 Mythril bytecode 分析補強；v1.0 不將 `controlled-array-length` 等同於完整 overflow / underflow。

### 暫緩項目

- Mythril bytecode 分析
- Price oracle manipulation
- QLoRA 微調
- 多檔合約 / import resolution
- CI/CD 插件：GitHub Action / Foundry plugin / Hardhat plugin

---

## 系統流程

```text
Solidity .sol
  │
  ├─① solc 版本偵測與自動安裝
  │     └─ py-solc-x 管理 solc 版本
  │
  ├─② Slither 靜態分析
  │     └─ 輸出 detector findings + AST
  │
  ├─③ Finding Normalization
  │     └─ Slither JSON → 統一 FindingSchema
  │
  ├─④ JSON Schema Validation
  │     └─ 先產生 deterministic JSON 報告
  │
  ├─⑤ RAG 檢索
  │     ├─ BM25 top-k
  │     ├─ Dense retrieval top-k
  │     ├─ 合併去重
  │     └─ Cross-encoder rerank top-k
  │
  ├─⑥ Context Packing
  │     └─ 單一 finding + RAG chunks → prompt
  │
  ├─⑦ LLM 逐 finding 生成
  │     └─ explanation + attack_path + fix_suggestion
  │
  ├─⑧ 報告輸出
  │     └─ JSON + Markdown
  │
  └─⑨ Analysis Trace 儲存
        └─ finding_id ↔ slither_raw ↔ rag_chunks ↔ prompt ↔ llm_output
```

---

## 硬體資源限制與批次處理策略

開發環境為 MacBook Pro M2 Pro / 16GB 統一記憶體。8B 4-bit 模型可在本地端運行，但若一次將多個 findings、AST 摘要、RAG chunks 與完整輸出需求塞入模型，容易造成記憶體壓力。

v1.0 採用「逐 finding 批次生成」策略。

### 處理規則

- 每次只處理 1 個 finding
- 每個 finding 預設使用 top-3 RAG chunks
- 單 finding 輸出上限：1024 tokens
- 單 finding 完成後立即寫入 trace 與 report buffer
- 不將多個 findings 合併成單次 LLM request
- 若記憶體壓力過高，RAG chunks 從 top-3 降為 top-2
- 若 LLM timeout，該 finding 標記為 `partial`

### 批次流程

```text
findings[]
  → finding_001 → RAG → LLM → write result → release context
  → finding_002 → RAG → LLM → write result → release context
  → finding_003 → RAG → LLM → write result → release context
  → merge final JSON / Markdown report
```

此設計確保 16GB 記憶體環境下可穩定執行，避免一次處理整份合約所有漏洞造成 OOM。

---

## 技術架構

| 層級 | 技術 | 職責 | 備註 |
|---|---|---|---|
| solc 管理 | py-solc-x | 偵測 pragma 版本、自動下載對應 solc | 不做獨立 AST 解析 |
| 靜態分析 | Slither Python API | 產生 deterministic findings + AST | 使用 `Slither()` class |
| 標準化 | Finding Adapter | Slither detector output → FindingSchema | 統一後才進入 RAG 與 LLM |
| 知識庫 | 審計報告 + SWC + OpenZeppelin Docs | chunk 化後存入索引 | 100 份報告作為 v1.0 目標 |
| 檢索 | BM25 + Chroma + Cross-encoder | 平行召回 + 精排 | 支援降級模式 |
| 推理 | MLX + 4-bit 8B model | 本地生成解釋與修復建議 | 逐 finding 生成 |
| 驗證 | jsonschema | 結構驗證 | Draft 2020-12 |
| 追蹤 | SQLite Analysis Trace | 全鏈路回溯 | finding ↔ raw ↔ chunk ↔ prompt ↔ output |

---

## 架構決策記錄

### 為何不獨立做 AST 解析

Slither 內部已呼叫 solc 並產出完整 AST；py-solc-x 僅用於 solc 版本管理與自動安裝，不重複編譯。這能減少一次 solc invocation，並避免 AST 版本不一致。

### 為何先不用 Mythril

Mythril 偏 bytecode / EVM 分析，整合成本較高，且會拉長 v1.0 開發週期。v1.0 先用 Slither 建立穩定 deterministic pipeline，v1.1 再加入 Mythril 補強 overflow / underflow 與 bytecode 層風險。

### 為何先做 CLI

CLI 是最小可驗證介面，可直接測試 `.sol → JSON → Markdown` 流程。Gradio 只做展示，不應阻塞核心分析管線。

---

## Finding Adapter 映射規則

```python
DETECTOR_MAPPING = {
    "reentrancy-eth":          ("reentrancy",                3),
    "reentrancy-no-eth":       ("reentrancy",                2),
    "reentrancy-benign":       ("reentrancy",                1),

    "unprotected-upgrade":     ("access_control",            3),
    "suicidal":                ("access_control",            3),
    "arbitrary-send-eth":      ("access_control",            3),

    "unchecked-lowlevel":      ("unchecked_external_call",   2),
    "unchecked-send":          ("unchecked_external_call",   2),

    "controlled-delegatecall": ("dangerous_delegatecall",    3),
    "delegatecall-loop":       ("dangerous_delegatecall",    2),

    "controlled-array-length": ("array_length_manipulation", 2),
}
```

severity 定義：

```text
1 = Low
2 = Medium
3 = High
```

未在映射表中的 detector 不輸出到正式報告，但必須記錄至 trace，方便後續擴充。

---

## FindingSchema

```json
{
  "finding_id": "f_001",
  "vulnerability_type": "reentrancy",
  "severity": 3,
  "location": {
    "file": "Vault.sol",
    "function": "withdraw",
    "line_start": 42,
    "line_end": 58
  },
  "evidence": "Slither raw output or source snippet",
  "reference": ["SWC-107", "report_042"],
  "finding_confidence": 0.9,
  "explanation_confidence": 0.8,
  "explanation": "string",
  "attack_path": "string",
  "fix_suggestion": "string",
  "static_tool_source": "slither",
  "detector_name": "reentrancy-eth",
  "partial": false
}
```

---

## RAG Pipeline

### Chunking 策略

| 參數 | 值 | 理由 |
|---|---:|---|
| Chunk 大小 | 384 tokens | 保持段落語意完整，避免過長 |
| Overlap | 64 tokens | 漏洞描述常跨段落 |
| Tokenizer | `cl100k_base` | 統一 chunk 儲存與檢索層計數 |
| 分割方式 | 段落邊界優先，fallback 句號斷句 | 降低切斷語意機率 |

MLX 模型本身可能使用不同 tokenizer，但資料切分與檢索層統一用 `cl100k_base`，避免 BM25 與 dense embedding 的長度統計偏差。

### 平行召回流程

```text
Query = normalized_finding.vulnerability_type + normalized_finding.evidence 前 200 chars

BM25 top-50
Dense Retrieval top-50
  ↓
合併去重
  ↓
Cross-encoder rerank
  ↓
top-5 / top-3 chunks
```

### RAG 效能降級策略

| 模式 | BM25 | Dense | Rerank Input | Output | 使用情境 |
|---|---:|---:|---:|---:|---|
| quality | top-50 | top-50 | ≤100 | top-5 | 預設品質模式 |
| balanced | top-30 | top-30 | ≤60 | top-3 | 一般本地模式 |
| fast | top-20 | top-20 | ≤40 | top-3 | 延遲過高或展示模式 |
| fallback | top-20 | disabled | ≤20 | top-3 | embedding / reranker 載入失敗 |

### 自動降級條件

| 條件 | 行為 |
|---|---|
| 單一 finding 的 RAG retrieval 超過 20 秒 | 下一個 finding 改用 balanced |
| 單一 finding 的 RAG retrieval 超過 40 秒 | 下一個 finding 改用 fast |
| Cross-encoder 載入失敗 | 改用 BM25-only fallback |
| 累積總耗時達 80 秒 | 後續 finding 強制 fast mode |
| 累積總耗時達 100 秒 | 後續 finding 強制 fallback mode |
| 累積總耗時達 115 秒 | 停止 LLM 生成，只輸出 deterministic findings |
| 記憶體壓力過高 | top-3 chunks 降為 top-2 |

此策略使用實際累積耗時取代事前預估，確保程式邏輯可實作，並避免系統卡在高成本檢索或生成階段。

### 累積超時監控流程

```text
start_time = now()
for finding in findings:
    elapsed = now() - start_time

    if elapsed >= 115s:
        output deterministic finding only
        mark partial = true
        continue
    elif elapsed >= 100s:
        rag_mode = fallback
    elif elapsed >= 80s:
        rag_mode = fast
    else:
        rag_mode = current_adaptive_mode

    run RAG + LLM for current finding
    write per-finding trace
```

---

## Context Packing Template

```text
[System]
You are a smart contract security analyst.
Given one static analysis finding and related audit knowledge,
provide explanation, attack path, and fix suggestion.

[Finding]
{normalized_finding as JSON}

[Related Knowledge]
{top-k chunks, each prefixed with [source_id], [severity], [vuln_type]}

[Instructions]
- Output valid JSON matching the schema.
- explanation: 3-5 sentences, reference specific code lines.
- attack_path: step-by-step exploit scenario.
- fix_suggestion: concrete code-level fix.
- If evidence is insufficient, set explanation_confidence < 0.5.
- Do not invent vulnerabilities not present in the static finding.
```

---

## 輸出 Schema

```json
{
  "overall_status": "finding | no_finding | partial_analysis | error",
  "contract_id": "sha256(file_content)[:12]",
  "requires_human_review": true,
  "business_logic_review_required": false,
  "review_reason": "string",
  "findings": [
    {
      "finding_id": "f_001",
      "vulnerability_type": "reentrancy",
      "severity": 3,
      "location": {
        "file": "Vault.sol",
        "function": "withdraw",
        "line_start": 42,
        "line_end": 58
      },
      "evidence": "string",
      "reference": ["SWC-107", "report_042"],
      "finding_confidence": 0.9,
      "explanation_confidence": 0.8,
      "explanation": "string",
      "attack_path": "string",
      "fix_suggestion": "string",
      "static_tool_source": "slither",
      "detector_name": "reentrancy-eth",
      "partial": false
    }
  ],
  "analysis_metadata": {
    "dataset_version": "dataset_v1.0",
    "model_version": "mlx-8b-4bit",
    "solc_version": "0.8.19",
    "slither_version": "0.10.0",
    "partial_analysis": false,
    "analysis_trace_id": "trace_xxx",
    "context_tokens_used": 8200,
    "rag_mode": "balanced",
    "total_duration_ms": 12500,
    "errors": []
  }
}
```

### overall_status 定義

| 狀態 | 定義 |
|---|---|
| `finding` | 至少 1 個 finding 完整生成 |
| `no_finding` | Slither 無 detector hit |
| `partial_analysis` | 部分 finding 的 LLM 生成失敗 |
| `error` | solc 或 Slither 執行失敗 |

---

## Confidence 計算

### finding_confidence

漏洞存在可信度，由 Slither detector severity 與 RAG 支撐計算。

```python
def compute_finding_confidence(finding, rag_chunks):
    base = {3: 0.85, 2: 0.70, 1: 0.50}[finding.severity]

    if not rag_chunks:
        rag_boost = 0.0
    else:
        matching = sum(
            1 for c in rag_chunks
            if c.vuln_type == finding.vulnerability_type
        )
        rag_boost = matching / len(rag_chunks) * 0.15

    return min(base + rag_boost, 1.0)
```

### explanation_confidence

解釋可信度，由輸出格式、行號引用、修復建議品質與 RAG 引用計算。

```python
def compute_explanation_confidence(llm_output, schema_valid, rag_chunks):
    score = 0.0

    if schema_valid:
        score += 0.3

    if references_line_numbers(llm_output.explanation):
        score += 0.2

    if has_code_level_fix(llm_output.fix_suggestion):
        score += 0.2

    cited = count_cited_sources(llm_output.explanation, rag_chunks)
    score += min(cited / 3, 1.0) * 0.2

    if count_steps(llm_output.attack_path) >= 3:
        score += 0.1

    return min(score, 1.0)
```

---

## 靜態分析限制與人工複查機制

v1.0 以 Slither 作為 deterministic finding 來源，因此能穩定處理結構型漏洞，但無法覆蓋所有商業邏輯風險。

### 已知限制

- 無法可靠偵測 DeFi 獎勵公式錯誤
- 無法理解協議經濟模型設計缺陷
- 無法分析跨合約、跨協議的複合攻擊路徑
- 無法偵測 Slither detector 未覆蓋的未知漏洞模式
- 無法偵測未公開的 0-day 漏洞模式

### 人工複查規則

| 條件 | 行為 |
|---|---|
| Slither 無 finding | 輸出 `no_finding`，但附人工複查聲明 |
| 合約包含 `reward`, `oracle`, `pool`, `swap`, `staking` | `business_logic_review_required = true` |
| RAG 無相關 chunk | `explanation_confidence` 上限設為 0.5 |
| detector 未映射 | 寫入 trace，不進正式報告 |
| LLM 想新增靜態工具沒有的漏洞 | 拒絕輸出該漏洞 |

### 人工複查欄位

```json
{
  "requires_human_review": true,
  "business_logic_review_required": true,
  "review_reason": "Contract contains DeFi reward/oracle/pool related logic outside Slither v1.0 coverage."
}
```

---

## 錯誤處理與降級策略

| 故障點 | 行為 | overall_status |
|---|---|---|
| solc 版本無法安裝 | 終止，返回錯誤訊息 | `error` |
| Slither 執行失敗 | 終止，返回 stderr | `error` |
| Slither 無 finding | 正常返回空 findings | `no_finding` |
| RAG 檢索返回 0 chunks | 跳過 RAG，LLM 僅用 finding context | `finding`，但 explanation_confidence ≤ 0.5 |
| LLM 生成 timeout 超過 30 秒 | 重試 1 次，仍失敗則該 finding 標記 `partial` | `partial_analysis` |
| LLM 輸出 schema 驗證失敗 | 重試 1 次，仍失敗標記 `partial` | `partial_analysis` |
| LLM 輸出含幻覺行號 | 檢查行號是否在範圍內，超出則扣分 | 不改 status |
| Cross-encoder 載入失敗 | 改用 BM25-only fallback | 不改 status |

---

## 資料清洗與非結構化報告處理

公開審計報告來源包含 PDF、Markdown、HTML，不同格式混雜程式碼、表格與漏洞描述，因此資料清洗是 v1.0 的核心工程之一。

### 資料清洗流程

```text
raw_reports/
  → format detection
  → PDF / HTML / Markdown parser
  → code block preservation
  → vulnerability section extraction
  → chunking
  → metadata tagging
  → manifest checksum
```

### 清洗規則

- 保留 Solidity code block，不在程式碼中間切 chunk
- 優先以漏洞標題、Severity、Recommendation 區塊切分
- 每個 chunk 必須包含 `source_id`, `report_id`, `severity`, `vuln_type`, `sha256`
- 無法判定漏洞類型的 chunk 先標記為 `unknown`
- `unknown` chunk 進入零樣本分類搶救流程，但不直接進入 v1.0 評測集
- 表格內容轉成 Markdown table 後再 chunk
- 圖片與流程圖先略過，記錄為 `unsupported_visual_content: true`

### Unknown Chunk 搶救流程

當 parser 無法透過標題、Severity 區塊或規則表判定漏洞類型時，使用本地小模型進行 zero-shot classification，嘗試將 chunk 對應到 v1.0 支援的漏洞類型或 SWC 類別。

```text
unknown chunk
  → local zero-shot classifier
  → predicted vuln_type + label_confidence
  → confidence >= 0.75：可進入 RAG 知識庫
  → confidence < 0.75：保留為 unknown，不進入正式索引
```

分類結果必須標記來源，避免污染黃金評測資料：

```json
{
  "vuln_type": "reentrancy",
  "label_source": "zero_shot_llm",
  "label_confidence": 0.78,
  "eligible_for_eval": false
}
```

`eligible_for_eval = false` 代表該 chunk 可用於 RAG 補充知識，但不可作為 ground truth 或 confidence 校準資料。

---

## 資料集 v1.0

### 來源

| 來源 | 數量 | 用途 |
|---|---:|---|
| 公開審計報告：Trail of Bits、OpenZeppelin、Consensys、Sherlock | 100 份 | 漏洞案例與修復建議 |
| SWC Registry | 37 entries | 漏洞分類標準 |
| OpenZeppelin Docs v4.x | 核心合約文件 | 安全模式參考 |

### Chunk Metadata Schema

```json
{
  "chunk_id": "string",
  "source_id": "report_042",
  "report_id": "ToB-2023-Uniswap",
  "severity": 3,
  "vuln_type": "reentrancy",
  "content": "string",
  "token_count": 384,
  "created_at": "2025-01-15",
  "sha256": "abc123...",
  "unsupported_visual_content": false,
  "label_source": "rule_based | manual | zero_shot_llm",
  "label_confidence": 0.95,
  "eligible_for_eval": true
}
```

### 可重現性保證

- 全資料集附 `manifest.json`
- 每個 chunk 記錄 `sha256`, `source_id`, `created_at`
- `dataset_v1.0/` 目錄不可變
- 新資料集建立 `dataset_v1.1/`
- 評測腳本讀取 `manifest.json` 並驗證完整性後才執行

---

## Analysis Trace Schema

```sql
CREATE TABLE analysis_trace (
    trace_id            TEXT PRIMARY KEY,
    contract_id         TEXT NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    solc_version        TEXT,
    slither_version     TEXT,
    model_version       TEXT,
    dataset_version     TEXT,
    initial_rag_mode    TEXT,
    final_status        TEXT,
    total_duration_ms   INTEGER
);

CREATE TABLE trace_findings (
    trace_id              TEXT REFERENCES analysis_trace(trace_id),
    finding_id            TEXT NOT NULL,
    detector_name         TEXT,
    rag_mode              TEXT,
    retrieval_duration_ms INTEGER,
    llm_duration_ms       INTEGER,
    chunks_used           INTEGER,
    slither_raw           TEXT,
    normalized_finding    TEXT,
    rag_chunk_ids         TEXT,
    packed_prompt         TEXT,
    llm_raw_output        TEXT,
    schema_valid          BOOLEAN,
    retry_count           INTEGER DEFAULT 0,
    partial               BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (trace_id, finding_id)
);
```



### Per-finding Trace 原則

`rag_mode` 不放在 `analysis_trace` 母表，因為同一份合約在逐 finding 處理時可能動態降級；每個 finding 必須獨立記錄當下使用的 `rag_mode`、檢索耗時、LLM 耗時與實際使用 chunk 數。

| 欄位 | 所屬表 | 原因 |
|---|---|---|
| `initial_rag_mode` | `analysis_trace` | 記錄本次分析起始策略 |
| `final_status` | `analysis_trace` | 記錄整份合約最後狀態 |
| `rag_mode` | `trace_findings` | 每個 finding 可能不同 |
| `retrieval_duration_ms` | `trace_findings` | 判斷是否觸發降級 |
| `llm_duration_ms` | `trace_findings` | 追蹤生成瓶頸 |
| `chunks_used` | `trace_findings` | 確認 context packing 是否降級 |

### Trace 查詢目標

任一 finding 必須可回溯：

```text
finding_id
  → Slither raw output
  → normalized FindingSchema
  → RAG chunk_ids
  → packed prompt
  → LLM raw output
  → final report field
```

---

## LLM-as-a-Judge 自動化評測

人工抽檢保留作最終驗證，但日常回歸測試加入 LLM-as-a-Judge，以高階模型批次檢查本地模型輸出的解釋品質與修復建議。

### Judge 輸入

```json
{
  "contract_snippet": "string",
  "static_finding": "FindingSchema",
  "rag_chunks": ["chunk_id_001", "chunk_id_002"],
  "local_model_output": {
    "explanation": "string",
    "attack_path": "string",
    "fix_suggestion": "string"
  }
}
```

### Judge 評分維度

| 維度 | 分數 | 說明 |
|---|---:|---|
| vulnerability_alignment | 0–1 | 解釋是否對齊 Slither finding |
| evidence_grounding | 0–1 | 是否基於 evidence 與 RAG chunk |
| line_number_validity | 0–1 | 是否捏造不存在的行號 |
| fix_correctness | 0–1 | 修復建議是否具體且不引入新問題 |
| citation_validity | 0–1 | 是否引用有效 `source_id` |

總分為 0–5，並輸出 `fail_reason` 供回歸測試定位問題。

```json
{
  "judge_score": 4.2,
  "fail_reason": "fix_suggestion lacks concrete access-control modifier example",
  "judge_model": "gpt-4o-or-claude-sonnet",
  "eval_timestamp": "2026-04-29T00:00:00Z"
}
```

### 使用策略

- 每次改動 prompt、retriever、reranker 或模型時，執行 judge regression test
- Judge 結果不取代人工審查，只作為自動化品質門檻
- 高風險 findings 仍保留人工抽檢
- 每月 API 預算優先用於 judge 評測，而不是生產推理

---


## 驗收標準

| 任務 | 驗收標準 | 測量方式 |
|---|---|---|
| 資料清洗 | 100 份報告轉 Markdown chunks，chunk 長度 300–450 tokens，離群值 < 5% | `python scripts/validate_chunks.py` |
| 格式解析 | PDF / HTML / Markdown 三類來源均可轉成 Markdown | parser 測試 |
| 程式碼保留 | Solidity code block 被截斷比例 < 3% | chunk 驗證腳本 |
| Metadata 完整率 | chunk 必填 metadata 完整率 > 95% | manifest 檢查 |
| Slither 整合 | 50 份測試合約成功執行 Slither，輸出合法 JSON，允許 findings 為空，錯誤率 = 0 | CI job + JSON schema check |
| Normalization | Slither finding → FindingSchema，未映射 detector < 5% | mapping 覆蓋率報告 |
| RAG 檢索 | 20 題測試集，BM25 ∪ Dense 後 rerank top-5，召回率 > 75% | 人工標註 chunk_id |
| 報告生成 | 50 次生成，JSON schema 驗證通過率 > 95% | `jsonschema.validate()` |
| Confidence 校準 | finding_confidence > 0.8 的 findings 中，人工確認真陽性 > 80% | 人工抽檢 20 個 high-confidence findings |
| LLM Judge 回歸測試 | 50 筆樣本平均 judge_score ≥ 4.0，且 line_number_validity 平均 ≥ 0.9 | `eval/run_judge.py` |
| Unknown chunk 搶救 | unknown chunk 經 zero-shot 後，label_confidence ≥ 0.75 者可進 RAG，但 eligible_for_eval 必須為 false | `scripts/classify_unknown_chunks.py` |
| Trace 回溯 | 任一 finding_id 可查到 Slither raw、RAG chunks、prompt、LLM output | `trace_lookup.py` |
| 端到端延遲 | 單檔 ≤500 行分析完成 < 120 秒 | `time` 命令 |
| MVP 展示 | CLI 上傳 `.sol` → JSON + Markdown 報告 | 手動操作 + 截圖 |

---

## 專案目錄結構

```text
smart-contract-audit/
├── src/
│   ├── cli.py
│   ├── web.py
│   ├── analyzer.py
│   ├── slither_runner.py
│   ├── finding_adapter.py
│   ├── rag/
│   │   ├── chunker.py
│   │   ├── indexer.py
│   │   ├── retriever.py
│   │   └── reranker.py
│   ├── llm/
│   │   ├── generator.py
│   │   └── prompt_template.py
│   ├── validation/
│   │   ├── schema.py
│   │   └── validator.py
│   ├── confidence/
│   │   ├── finding_score.py
│   │   └── explanation_score.py
│   └── trace/
│       ├── store.py
│       └── lookup.py
├── data/
│   └── dataset_v1.0/
│       ├── manifest.json
│       ├── chunks/
│       └── raw_reports/
├── tests/
│   ├── contracts/
│   ├── test_slither.py
│   ├── test_adapter.py
│   ├── test_rag.py
│   ├── test_confidence.py
│   └── test_e2e.py
├── scripts/
│   ├── validate_chunks.py
│   ├── build_index.py
│   ├── classify_unknown_chunks.py
│   └── trace_lookup.py
├── eval/
│   ├── rag_recall_test.json
│   ├── judge_eval_set.json
│   ├── run_eval.py
│   └── run_judge.py
├── schemas/
│   └── finding_schema.json
├── pyproject.toml
└── README.md
```

---

## 最小實作順序

1. Slither Runner
2. Finding Adapter
3. JSON Schema Validator
4. CLI deterministic report
5. Dataset cleaner
6. Basic RAG retrieval
7. LLM Generator
8. Analysis Trace
9. Gradio Web UI
10. Cross-encoder Rerank

第 4 步完成後，系統已能展示 deterministic JSON；後續 RAG、LLM、Trace、Gradio 都是增強層，不阻塞 MVP。

---

## v1.1 路線圖

```text
v1.0 MVP 完成
  ├─ Multi-file Import Resolution
  ├─ Mythril Bytecode 分析
  ├─ Foundry / Hardhat 專案格式支援
  ├─ Multi-vector RAG：code embedding + text embedding
  ├─ 五組消融實驗
  └─ QLoRA 微調
```

| 優先序 | 項目 | 前置依賴 | 預估工時 |
|---|---|---|---:|
| P1 | Multi-file import resolution | v1.0 | 2 週 |
| P1 | Mythril 整合 | v1.0 | 1.5 週 |
| P2 | Foundry / Hardhat 支援 | Multi-file | 1 週 |
| P2 | Multi-vector RAG | v1.0 | 1.5 週 |
| P3 | 消融實驗 | Multi-vector RAG | 1 週 |
| P4 | QLoRA 微調 | 消融實驗結果 | 2 週 |

---

## v0.8 修正重點

v0.8 在 v0.7 的硬體穩定版基礎上，補強 per-finding 追蹤、累積超時控制、自動化評測與 unknown chunk 搶救：

- `rag_mode` 改為 per-finding trace，精準記錄每個漏洞使用的檢索策略
- 端到端預估超時改成累積耗時門檻，降低實作難度
- 加入 LLM-as-a-Judge，自動化評測解釋與修復建議品質
- unknown chunk 加入 zero-shot 分類搶救，但不進入評測集
- LLM 逐 finding 批次處理，避免 OOM
- Slither 盲點明確標記人工複查
- RAG 加入 quality / balanced / fast / fallback 四級模式
- v1.0 優先保證可跑、可追蹤、可展示

---

## 最終定位

v1.0 是「本地可跑的智能合約漏洞初篩 MVP」。

它的價值不在於宣稱取代審計，而在於展示完整工程能力：

- 靜態分析整合
- 非結構化資安報告清洗
- RAG 檢索與降級策略
- 本地 LLM 推理
- JSON Schema 驗證
- SQLite Trace 可回溯
- 硬體限制下的穩定性設計
