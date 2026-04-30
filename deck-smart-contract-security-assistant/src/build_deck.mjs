const {
  Presentation,
  PresentationFile,
  row,
  column,
  grid,
  layers,
  panel,
  text,
  shape,
  rule,
  fill,
  hug,
  fixed,
  wrap,
  grow,
  fr,
  auto,
} = await import("@oai/artifact-tool");
const { writeFile } = await import("node:fs/promises");

const SLIDE = { width: 1920, height: 1080 };
const C = {
  ink: "#111315",
  paper: "#F4F0E6",
  paper2: "#FFF9EC",
  green: "#21A67A",
  green2: "#DDF6E8",
  amber: "#F4B942",
  blue: "#1D8FE1",
  red: "#E85252",
  muted: "#6E746F",
  line: "#D9D0C1",
  dark: "#18201D",
};

const presentation = Presentation.create({ slideSize: SLIDE });

function T(value, options = {}) {
  return text(value, {
    width: options.width ?? fill,
    height: options.height ?? hug,
    name: options.name,
    columnSpan: options.columnSpan,
    rowSpan: options.rowSpan,
    style: {
      fontSize: options.size ?? 28,
      bold: options.bold ?? false,
      color: options.color ?? C.ink,
      fontFamily: options.font ?? "PingFang TC",
      ...options.style,
    },
  });
}

function mono(value, options = {}) {
  return T(value, {
    ...options,
    font: "Menlo",
    style: { ...options.style, fontFamily: "Menlo" },
  });
}

function bg(content, options = {}) {
  return layers(
    { name: "root", width: fill, height: fill },
    [
      shape({
        name: "bg",
        width: fill,
        height: fill,
        fill: options.fill ?? C.paper,
        line: { width: 0, fill: options.fill ?? C.paper },
      }),
      content,
    ],
  );
}

function addSlide(root, notes = "") {
  const slide = presentation.slides.add();
  slide.compose(bg(root), {
    frame: { left: 0, top: 0, width: SLIDE.width, height: SLIDE.height },
    baseUnit: 8,
  });
  if (notes) slide.speakerNotes.setText(notes);
  return slide;
}

function pill(label, color = C.green, width = 270) {
  return panel(
    {
      name: `pill-${label}`,
      width: fixed(width),
      height: hug,
      padding: { x: 20, y: 10 },
      fill: color,
      line: { width: 0, fill: color },
      borderRadius: "rounded-full",
    },
    T(label, { size: 20, bold: true, color: "#FFFFFF", width: fill }),
  );
}

function metric(label, value, accent = C.green) {
  return column(
    { name: `metric-${label}`, width: fill, height: hug, gap: 10 },
    [
      T(value, { size: 58, bold: true, color: accent }),
      T(label, { size: 20, color: C.muted }),
    ],
  );
}

function stepNode(index, title, body, color = C.green) {
  return panel(
    {
      name: `step-${index}`,
      width: fill,
      height: hug,
      padding: { x: 26, y: 22 },
      fill: "#FFFFFF",
      line: { width: 1, fill: C.line },
      borderRadius: "rounded-lg",
    },
    row(
      { width: fill, height: hug, gap: 18 },
      [
        panel(
          {
            width: fixed(58),
            height: fixed(58),
            fill: color,
            line: { width: 0, fill: color },
            borderRadius: "rounded-full",
            align: "center",
            justify: "center",
          },
          T(String(index), { size: 24, bold: true, color: "#FFFFFF", width: hug }),
        ),
        column(
          { width: fill, height: hug, gap: 8 },
          [
            T(title, { size: 26, bold: true }),
            T(body, { size: 19, color: C.muted, width: fill }),
          ],
        ),
      ],
    ),
  );
}

addSlide(
  layers(
    { width: fill, height: fill },
    [
      shape({
        width: fill,
        height: fill,
        fill: C.ink,
        line: { width: 0, fill: C.ink },
      }),
      shape({
        name: "left-field",
        width: fixed(690),
        height: fill,
        fill: C.green,
        line: { width: 0, fill: C.green },
      }),
      column(
        {
          name: "cover-copy",
          width: fill,
          height: fill,
          padding: { x: 104, y: 94 },
          justify: "between",
        },
        [
          row(
            { width: fill, height: hug, gap: 18 },
            [
              pill("Solidity Security", C.dark, 270),
              pill("Local-first AI", C.blue, 230),
            ],
          ),
          column(
            { width: fill, height: hug, gap: 24 },
            [
              T("智能合約安全分析助理", {
                size: 86,
                bold: true,
                color: "#FFFFFF",
                width: wrap(1180),
              }),
              T("一個可跑、可追蹤、可驗證的本地漏洞初篩 MVP", {
                size: 34,
                color: "#D6F5E3",
                width: wrap(980),
              }),
            ],
          ),
          row(
            { width: fill, height: hug, gap: 44 },
            [
              mono("Slither → RAG → MLX → JSON/MD → SQLite Trace", {
                size: 24,
                color: "#D6F5E3",
                width: wrap(980),
              }),
              T("專案展示稿", { size: 24, color: "#FFFFFF", width: hug }),
            ],
          ),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1.1), fr(0.9)],
      rows: [auto, fr(1)],
      padding: { x: 90, y: 74 },
      columnGap: 64,
      rowGap: 56,
    },
    [
      column(
        { width: fill, height: hug, gap: 16, columnSpan: 2 },
        [
          T("專案一句話", { size: 58, bold: true }),
          T("讓開發者上傳單檔 Solidity 合約，在本機完成漏洞初篩、報告生成與全鏈路追蹤。", {
            size: 27,
            color: C.muted,
            width: wrap(1240),
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 26 },
        [
          metric("單檔合約上限", "500 行", C.green),
          metric("核心偵測來源", "Slither", C.blue),
          metric("端到端測試記憶體峰值", "51.6 MiB", C.amber),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 22 },
        [
          stepNode(1, "靜態分析判定漏洞", "deterministic finding 不交給 LLM 猜測。", C.green),
          stepNode(2, "RAG 補上下文", "審計報告、SWC 與文件 chunk 提供修復依據。", C.blue),
          stepNode(3, "Trace 保證可回溯", "finding、raw output、prompt、LLM output 都能查。", C.amber),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(0.95), fr(1.05)],
      rows: [auto, fr(1)],
      padding: { x: 86, y: 72 },
      columnGap: 52,
      rowGap: 44,
    },
    [
      column(
        { width: fill, height: hug, gap: 14, columnSpan: 2 },
        [
          T("使用場景：正式審計前的工程化初篩", { size: 54, bold: true }),
          T("目標不是取代審計，而是把重複、可驗證、可追蹤的風險整理流程自動化。", {
            size: 25,
            color: C.muted,
            width: wrap(1180),
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 24 },
        [
          T("痛點", { size: 32, bold: true, color: C.red }),
          T("公開報告格式混亂；多數工具只吐 detector 結果；LLM 容易補出靜態工具沒有的漏洞；本機 16GB 記憶體限制要求逐 finding 處理。", {
            size: 30,
            width: wrap(720),
          }),
        ],
      ),
      grid(
        {
          width: fill,
          height: fill,
          columns: [fr(1), fr(1)],
          rows: [fr(1), fr(1)],
          gap: 18,
        },
        [
          stepNode(1, "個人開發者", "提交前找出 reentrancy / unchecked call。", C.green),
          stepNode(2, "Web3 團隊", "把初篩結果交給審計師複查。", C.blue),
          stepNode(3, "課程 / Demo", "展示完整安全分析 pipeline。", C.amber),
          stepNode(4, "履歷作品", "證明能做工具整合、RAG、trace 與評測。", C.red),
        ],
      ),
    ],
  ),
);

addSlide(
  column(
    {
      width: fill,
      height: fill,
      padding: { x: 76, y: 66 },
      gap: 42,
    },
    [
      column(
        { width: fill, height: hug, gap: 12 },
        [
          T("核心流程：從合約到可追溯報告", { size: 54, bold: true }),
          T("每個步驟都保留可驗證輸出；LLM 只負責解釋與修復建議。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      row(
        { width: fill, height: hug, gap: 16 },
        [
          stepNode(1, ".sol 輸入", "單檔、500 行、0.6.x–0.8.x", C.green),
          stepNode(2, "Slither", "detector findings + AST", C.blue),
          stepNode(3, "Adapter", "映射 FindingSchema", C.amber),
        ],
      ),
      row(
        { width: fill, height: hug, gap: 16 },
        [
          stepNode(4, "RAG", "BM25 / Dense / Rerank / fallback", C.green),
          stepNode(5, "MLX-ready LLM", "逐 finding 生成，支援 4-bit 模型", C.blue),
          stepNode(6, "Report + Trace", "JSON、Markdown、SQLite", C.amber),
        ],
      ),
      panel(
        {
          width: fill,
          height: hug,
          padding: { x: 28, y: 20 },
          fill: C.dark,
          line: { width: 0, fill: C.dark },
          borderRadius: "rounded-lg",
        },
        mono("scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --rag-mode fallback", {
          size: 24,
          color: "#E7F8EE",
        }),
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(0.9), fr(1.1)],
      rows: [auto, fr(1)],
      padding: { x: 84, y: 70 },
      columnGap: 58,
      rowGap: 42,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 2 },
        [
          T("架構內容：模組邊界清楚", { size: 54, bold: true }),
          T("Python package 採 CLI-first 結構，外部工具與展示層都是可選依賴。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      column(
        { width: fill, height: fill, gap: 16 },
        [
          mono("src/smart_contract_audit/", { size: 26, bold: true, color: C.green }),
          mono("├─ cli.py\n├─ analyzer.py\n├─ slither_runner.py\n├─ finding_adapter.py\n├─ rag/\n├─ llm/\n├─ confidence/\n├─ validation/\n└─ trace/", {
            size: 24,
            color: C.ink,
            width: wrap(660),
          }),
        ],
      ),
      grid(
        { width: fill, height: fill, columns: [fr(1), fr(1)], rows: [fr(1), fr(1)], gap: 18 },
        [
          stepNode(1, "slither_runner", "準備 solc，呼叫 Slither，解析 JSON。", C.blue),
          stepNode(2, "finding_adapter", "Detector → vulnerability_type / severity。", C.green),
          stepNode(3, "rag", "文件萃取、chunk、JSONL、BM25 fallback。", C.amber),
          stepNode(4, "trace", "analysis_trace 與 trace_findings 可查。", C.red),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1), fr(1)],
      rows: [auto, fr(1)],
      padding: { x: 86, y: 72 },
      columnGap: 54,
      rowGap: 44,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 2 },
        [
          T("技術核心 01：漏洞判定不交給模型猜", { size: 54, bold: true }),
          T("Slither 是 deterministic source；未映射 detector 進 trace，不進正式報告。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      column(
        { width: fill, height: fill, gap: 20 },
        [
          T("支援 detector", { size: 32, bold: true }),
          mono("reentrancy-eth      → reentrancy / High\nunchecked-lowlevel  → unchecked_external_call / Medium\ncontrolled-delegatecall → dangerous_delegatecall / High\ncontrolled-array-length → array_length_manipulation / Medium", {
            size: 23,
            width: fill,
          }),
        ],
      ),
      column(
        { width: fill, height: fill, gap: 20 },
        [
          T("報告欄位", { size: 32, bold: true }),
          mono("finding_id\nvulnerability_type\nseverity\nlocation\nevidence\nfinding_confidence\nexplanation_confidence\nstatic_tool_source\ndetector_name\npartial", {
            size: 23,
            width: fill,
          }),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1.05), fr(0.95)],
      rows: [auto, fr(1)],
      padding: { x: 86, y: 70 },
      columnGap: 56,
      rowGap: 42,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 2 },
        [
          T("技術核心 02：髒資料先清成可檢索知識", { size: 54, bold: true }),
          T("公開審計報告常混合 PDF、HTML、Markdown、表格與 Solidity 程式碼。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 18 },
        [
          stepNode(1, "格式偵測", "PDF / HTML / Markdown 分流。", C.green),
          stepNode(2, "程式碼保留", "Solidity code block 不在中間切斷。", C.blue),
          stepNode(3, "Metadata", "source_id、severity、vuln_type、sha256。", C.amber),
          stepNode(4, "Unknown 搶救", "低信心標記 unknown，不污染 eval set。", C.red),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 24 },
        [
          T("RAG 模式", { size: 32, bold: true }),
          mono("quality  : BM25 50 + Dense 50 → top 5\nbalanced : BM25 30 + Dense 30 → top 3\nfast     : BM25 20 + Dense 20 → top 3\nfallback : BM25 20 only     → top 3", {
            size: 25,
            width: fill,
          }),
          T("目前 fixture 評測 recall@k = 1.0", {
            size: 28,
            bold: true,
            color: C.green,
          }),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1), fr(1)],
      rows: [auto, fr(1)],
      padding: { x: 86, y: 72 },
      columnGap: 56,
      rowGap: 46,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 2 },
        [
          T("技術核心 03：Apple MLX-ready 本地推理策略", { size: 54, bold: true }),
          T("在 16GB MacBook Pro 環境下，設計重點是逐 finding 生成、4-bit 權重與可降級流程。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 28 },
        [
          metric("8B 4-bit 權重估算", "4.0 GB", C.green),
          metric("單 finding 輸出上限", "1024 tokens", C.blue),
          metric("E2E 記憶體峰值", "51.6 MiB", C.amber),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 18 },
        [
          stepNode(1, "80s", "後續 finding 強制 fast mode。", C.green),
          stepNode(2, "100s", "後續 finding 強制 fallback mode。", C.blue),
          stepNode(3, "115s", "停止 LLM 生成，輸出 deterministic findings。", C.red),
          stepNode(4, "timeout 測試", "模擬 116s 會輸出 partial_analysis。", C.amber),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1.15), fr(0.85)],
      rows: [auto, fr(1)],
      padding: { x: 86, y: 70 },
      columnGap: 52,
      rowGap: 42,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 2 },
        [
          T("技術核心 04：Trace 讓每個 finding 可回放", { size: 54, bold: true }),
          T("這是審計輔助工具的信任基礎：任何結論都能查回來源、prompt 與輸出。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 20 },
        [
          mono("finding_id\n  → slither_raw\n  → normalized FindingSchema\n  → rag_chunk_ids\n  → packed_prompt\n  → llm_raw_output\n  → final report field", {
            size: 30,
            color: C.ink,
            width: wrap(820),
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 22 },
        [
          stepNode(1, "analysis_trace", "contract_id、model_version、dataset_version、final_status。", C.green),
          stepNode(2, "trace_findings", "per-finding rag_mode、耗時、chunks_used。", C.blue),
          stepNode(3, "trace_lookup", "CLI 查詢，支援定位單一 finding。", C.amber),
        ],
      ),
    ],
  ),
);

addSlide(
  column(
    {
      width: fill,
      height: fill,
      padding: { x: 84, y: 70 },
      gap: 42,
    },
    [
      column(
        { width: fill, height: hug, gap: 12 },
        [
          T("實際案例：VulnerableVault Reentrancy", { size: 54, bold: true }),
          T("Slither 在測試合約中找到 `reentrancy-eth`，並映射成正式報告 finding。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      grid(
        { width: fill, height: fill, columns: [fr(1), fr(1)], rows: [fr(1)], columnGap: 42 },
        [
          panel(
            {
              width: fill,
              height: fill,
              padding: { x: 28, y: 24 },
              fill: C.dark,
              line: { width: 0, fill: C.dark },
              borderRadius: "rounded-lg",
            },
            mono("function withdraw() external {\n  uint256 amount = balances[msg.sender];\n  (bool success,) = msg.sender.call{value: amount}(\"\");\n  require(success, \"transfer failed\");\n  balances[msg.sender] = 0;\n}", {
              size: 23,
              color: "#E7F8EE",
              width: fill,
            }),
          ),
          column(
            { width: fill, height: fill, justify: "center", gap: 24 },
            [
              stepNode(1, "偵測器", "reentrancy-eth", C.red),
              stepNode(2, "位置", "tests/contracts/VulnerableVault.sol:11-16", C.blue),
              stepNode(3, "風險", "外部 call 發生在 balances[msg.sender] = 0 之前。", C.amber),
              stepNode(4, "建議", "checks-effects-interactions + nonReentrant。", C.green),
            ],
          ),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1), fr(1), fr(1), fr(1)],
      rows: [auto, fr(1), auto],
      padding: { x: 76, y: 68 },
      columnGap: 24,
      rowGap: 34,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 4 },
        [
          T("驗收結果：已通過的品質門檻", { size: 54, bold: true }),
          T("這份展示不是設計稿假資料，而是讀取本專案實際測試結果。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      metric("pytest 全量回歸", "10 passed", C.green),
      metric("ruff", "All passed", C.blue),
      metric("RAG recall@k", "1.0", C.amber),
      metric("Judge score", "5.0", C.red),
      panel(
        {
          width: fill,
          height: hug,
          columnSpan: 4,
          padding: { x: 24, y: 18 },
          fill: "#FFFFFF",
          line: { width: 1, fill: C.line },
          borderRadius: "rounded-lg",
        },
        T("端到端：2 passed；1.67s；maximum resident set size = 54,083,584 bytes。", {
          size: 26,
          bold: true,
          color: C.ink,
        }),
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1), fr(1)],
      rows: [auto, fr(1)],
      padding: { x: 86, y: 72 },
      columnGap: 56,
      rowGap: 42,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 2 },
        [
          T("履歷與面試可展示的技術能力", { size: 54, bold: true }),
          T("這不是單一模型 demo，而是一條完整可交付的安全分析工程管線。", {
            size: 24,
            color: C.muted,
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 18 },
        [
          stepNode(1, "Security tooling", "Slither / solc / detector mapping / SWC。", C.green),
          stepNode(2, "AI engineering", "RAG、prompt packing、LLM-as-Judge、MLX-ready。", C.blue),
          stepNode(3, "Data engineering", "PDF/HTML/Markdown 萃取、metadata、manifest。", C.amber),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 18 },
        [
          stepNode(4, "Software delivery", "pytest、ruff、GitHub Actions、CI 評測。", C.red),
          stepNode(5, "Observability", "SQLite trace、per-finding rag_mode、耗時。", C.green),
          stepNode(6, "Resource control", "逐 finding 批次、timeout、fallback。", C.blue),
        ],
      ),
    ],
  ),
);

addSlide(
  grid(
    {
      width: fill,
      height: fill,
      columns: [fr(1), fr(1)],
      rows: [auto, fr(1), auto],
      padding: { x: 84, y: 70 },
      columnGap: 52,
      rowGap: 36,
    },
    [
      column(
        { width: fill, height: hug, gap: 12, columnSpan: 2 },
        [
          T("用於製作本 PPT 的 skill 選型", { size: 54, bold: true }),
          T("搜尋結果有可用候選，但實作選擇內建 Presentations skill 以保證可編輯 PPTX 與 QA。", {
            size: 24,
            color: C.muted,
            width: wrap(1280),
          }),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 22 },
        [
          stepNode(1, "Presentations", "內建；產出 editable PPTX、PNG preview、package QA。", C.green),
          stepNode(2, "find-skills", "搜尋 PowerPoint / pitch deck 類 skills。", C.blue),
          stepNode(3, "PowerPoint candidate", "igorwarzocha/opencode-workflows@powerpoint：1.2K installs、109 stars。", C.amber),
        ],
      ),
      column(
        { width: fill, height: fill, justify: "center", gap: 22 },
        [
          stepNode(4, "Pitch candidate", "ailabs-393/ai-labs-claude-skills@pitch-deck：712 installs、356 stars。", C.red),
          stepNode(5, "未新增安裝", "內建工具已覆蓋生成、匯出、驗證；降低額外 skill 供應鏈風險。", C.green),
          stepNode(6, "輸出定位", "中文技術展示 / 面試講解 / 專案 demo。", C.blue),
        ],
      ),
      panel(
        {
          width: fill,
          height: hug,
          columnSpan: 2,
          padding: { x: 26, y: 18 },
          fill: C.dark,
          line: { width: 0, fill: C.dark },
          borderRadius: "rounded-lg",
        },
        T("下一步可擴充：Mythril、多檔 import resolution、Foundry/Hardhat 專案支援、Dense retrieval 與真實外部 Judge。", {
          size: 25,
          color: "#E7F8EE",
        }),
      ),
    ],
  ),
);

const pptx = await PresentationFile.exportPptx(presentation);
await pptx.save("output/output.pptx");

for (const [index, slide] of presentation.slides.items.entries()) {
  const png = await slide.export({ format: "png" });
  const name = `scratch/slide-${String(index + 1).padStart(2, "0")}.png`;
  await writeFile(name, Buffer.from(await png.arrayBuffer()));
}
