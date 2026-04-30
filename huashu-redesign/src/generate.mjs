import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const ROOT = path.resolve(".");
const slidesDir = path.join(ROOT, "slides");
const sharedDir = path.join(ROOT, "shared");
const outputDir = path.join(ROOT, "output");
const screenshotDir = path.join(ROOT, "screenshots");

await Promise.all([
  mkdir(slidesDir, { recursive: true }),
  mkdir(sharedDir, { recursive: true }),
  mkdir(outputDir, { recursive: true }),
  mkdir(screenshotDir, { recursive: true }),
]);

const css = String.raw`
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --bg: #0B0D0E;
  --panel: #101719;
  --panel2: #151E20;
  --paper: #F3F0E6;
  --paper2: #D8D2C3;
  --ink: #F7F2DF;
  --muted: #9AA39B;
  --line: #284037;
  --green: #39FF88;
  --green2: #1FB36A;
  --orange: #FFB000;
  --red: #FF4D4D;
  --blue: #2CA7FF;
  --violet: #B47CFF;
}
html, body {
  width: 960pt;
  height: 540pt;
  overflow: hidden;
  background: var(--bg);
  font-family: "PingFang TC", "PingFang SC", "Microsoft JhengHei", system-ui, -apple-system, sans-serif;
  color: var(--ink);
}
body {
  position: relative;
  letter-spacing: 0;
}
h1, h2, h3, h4, p, li {
  font-weight: 500;
  line-height: 1.12;
}
h1 {
  font-size: 55pt;
  font-weight: 800;
  color: var(--ink);
}
h2 {
  font-size: 30pt;
  font-weight: 800;
  color: var(--ink);
}
h3 {
  font-size: 18pt;
  font-weight: 800;
  color: var(--ink);
}
p {
  font-size: 14pt;
  color: var(--muted);
  line-height: 1.38;
}
.paper { background: var(--paper); color: #101211; }
.paper h1, .paper h2, .paper h3 { color: #101211; }
.paper p { color: #5E665F; }
.abs { position: absolute; }
.title {
  position: absolute;
  left: 46pt;
  top: 44pt;
  width: 670pt;
}
.subtitle {
  margin-top: 12pt;
  width: 575pt;
}
.eyebrow p {
  color: var(--green);
  font-size: 10pt;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.kicker p {
  color: var(--green);
  font-size: 12pt;
  font-weight: 800;
}
.small p { font-size: 10pt; line-height: 1.28; }
.micro p { font-size: 8.5pt; line-height: 1.25; color: #778179; }
.mono p, p.mono {
  font-family: Menlo, Monaco, Consolas, monospace;
}
.code p {
  font-family: Menlo, Monaco, Consolas, monospace;
  font-size: 10.5pt;
  line-height: 1.38;
  color: #D8FFE4;
  white-space: pre-wrap;
}
.code.dark p { color: #111315; }
.paper .code p { color: #111315; }
.panel {
  position: absolute;
  background: rgba(255,255,255,0.055);
  border: 1px solid rgba(216,210,195,0.18);
  border-radius: 7pt;
}
.paper .panel {
  background: rgba(11,13,14,0.035);
  border-color: rgba(11,13,14,0.15);
}
.chip {
  position: absolute;
  background: #12251C;
  border: 1px solid rgba(57,255,136,0.55);
  border-radius: 99pt;
}
.chip p {
  color: var(--green);
  font-size: 10pt;
  font-weight: 800;
  text-align: center;
}
.bar { position: absolute; background: var(--green); }
.bar.orange { background: var(--orange); }
.bar.red { background: var(--red); }
.bar.blue { background: var(--blue); }
.bar.violet { background: var(--violet); }
.line { position: absolute; background: rgba(57,255,136,0.22); }
.line.strong { background: rgba(57,255,136,0.65); }
.line.muted { background: rgba(216,210,195,0.16); }
.paper .line.muted { background: rgba(11,13,14,0.16); }
.metric h2 {
  font-size: 42pt;
  color: var(--green);
}
.metric p {
  margin-top: 5pt;
  color: var(--muted);
  font-size: 10pt;
}
.paper .metric h2 { color: #0AA768; }
.paper .metric p { color: #667168; }
.node-index {
  position: absolute;
  width: 24pt;
  height: 24pt;
  border-radius: 99pt;
  background: var(--green);
}
.node-index p {
  color: #07100B;
  text-align: center;
  font-size: 11pt;
  line-height: 24pt;
  font-weight: 900;
}
.node-title {
  position: absolute;
  left: 34pt;
  top: 0;
  width: 170pt;
}
.node-title h3 {
  font-size: 16pt;
}
.node-title p {
  font-size: 9.5pt;
  margin-top: 4pt;
}
.rail {
  position: absolute;
  left: 46pt;
  right: 46pt;
  bottom: 26pt;
  height: 1pt;
  background: rgba(216,210,195,0.26);
}
.foot {
  position: absolute;
  left: 46pt;
  bottom: 30pt;
  width: 520pt;
}
.foot p {
  font-family: Menlo, Monaco, Consolas, monospace;
  color: rgba(216,210,195,0.60);
  font-size: 8.5pt;
}
.paper .foot p { color: rgba(11,13,14,0.55); }
.table-row {
  position: absolute;
  border-top: 1px solid rgba(216,210,195,0.18);
}
.paper .table-row { border-top-color: rgba(11,13,14,0.14); }
.table-row h3 {
  position: absolute;
  left: 0;
  top: 8pt;
  font-size: 13pt;
}
.table-row p {
  position: absolute;
  left: 190pt;
  top: 8pt;
  width: 250pt;
  font-size: 10.5pt;
}
`;

function esc(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function p(text, cls = "") {
  return `<p${cls ? ` class="${cls}"` : ""}>${text}</p>`;
}

function h(level, text) {
  return `<h${level}>${text}</h${level}>`;
}

function div(cls, style, content = "") {
  return `<div class="${cls}" style="${style}">${content}</div>`;
}

function line(style, cls = "line") {
  return div(cls, style);
}

function chip(x, y, w, text) {
  return div("chip", `left:${x}pt;top:${y}pt;width:${w}pt;height:24pt;padding-top:5pt;`, p(text));
}

function metric(x, y, value, label, color = "var(--green)") {
  return div("metric abs", `left:${x}pt;top:${y}pt;width:150pt;`, `${h(2, `<span style="color:${color}">${value}</span>`)}${p(label)}`);
}

function node(x, y, idx, title, body, color = "var(--green)", w = 205) {
  return div("abs", `left:${x}pt;top:${y}pt;width:${w}pt;height:54pt;`,
    div("node-index", `left:0;top:0;background:${color};`, p(idx)) +
    div("node-title", `width:${w - 34}pt;`, `${h(3, title)}${p(body)}`),
  );
}

function panel(x, y, w, ht, content, extra = "") {
  return div("panel", `left:${x}pt;top:${y}pt;width:${w}pt;height:${ht}pt;${extra}`, content);
}

function footer(text) {
  return div("rail", "") + div("foot", "", p(text));
}

function bgGrid() {
  return [
    line("left:46pt;top:168pt;width:868pt;height:1pt;", "line muted"),
    line("left:46pt;top:298pt;width:868pt;height:1pt;", "line muted"),
    line("left:46pt;top:428pt;width:868pt;height:1pt;", "line muted"),
    line("left:272pt;top:40pt;width:1pt;height:452pt;", "line muted"),
    line("left:498pt;top:40pt;width:1pt;height:452pt;", "line muted"),
    line("left:724pt;top:40pt;width:1pt;height:452pt;", "line muted"),
  ].join("");
}

function slideShell(fileTitle, bodyClass, content) {
  return `<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1280,height=720">
<title>${esc(fileTitle)}</title>
<link rel="stylesheet" href="../shared/tokens.css">
</head>
<body class="${bodyClass}">
${content}
</body>
</html>
`;
}

const slides = [
  {
    file: "01-cover.html",
    label: "封面",
    title: "智能合約安全分析助理",
    bodyClass: "",
    content: [
      bgGrid(),
      line("left:0;top:0;width:235pt;height:540pt;background:#112119;"),
      line("left:235pt;top:0;width:4pt;height:540pt;", "line strong"),
      div("eyebrow abs", "left:46pt;top:42pt;width:250pt;", p("SMART CONTRACT SECURITY ASSISTANT")),
      div("abs", "left:46pt;top:148pt;width:720pt;", h(1, "智能合約<br>安全分析助理")),
      div("abs", "left:48pt;top:308pt;width:520pt;", p("本地漏洞初篩、RAG 修復依據、MLX-ready 推理與 SQLite trace 組成一條可交付的安全分析管線。")),
      chip(48, 402, 120, "Slither"),
      chip(180, 402, 96, "RAG"),
      chip(288, 402, 116, "MLX"),
      chip(416, 402, 130, "Trace"),
      panel(640, 122, 230, 250, div("code", "left:20pt;top:20pt;width:190pt;height:200pt;position:absolute;", p("scsa analyze VulnerableVault.sol<br>  --rag-mode fallback<br>  --out reports<br><br>finding_id → raw<br>raw → schema<br>schema → chunks<br>chunks → report<br>report → trace", "mono"))),
      footer("Huashu redesign · HTML-native deck · editable PPTX path"),
    ].join(""),
  },
  {
    file: "02-one-line.html",
    label: "一句話",
    title: "一句話定位",
    bodyClass: "paper",
    content: [
      div("title", "", `${div("eyebrow", "", p("POSITIONING"))}${h(1, "把審計前重複工作變成可驗證 pipeline")}${div("subtitle", "", p("上傳單檔 Solidity 合約，在本機完成漏洞初篩、修復建議、報告輸出與全鏈路回放。"))}`),
      metric(58, 274, "500 行", "單檔合約上限"),
      metric(270, 274, "0.11.5", "Slither 串接版本", "var(--blue)"),
      metric(482, 274, "51.6 MiB", "E2E 記憶體峰值", "var(--orange)"),
      panel(690, 150, 210, 245,
        node(18, 20, "01", "確定性判定", "detector finding 先於生成。", "var(--green)", 175) +
        node(18, 88, "02", "乾淨知識庫", "dirty reports → chunks。", "var(--blue)", 175) +
        node(18, 156, "03", "可追溯輸出", "prompt / raw / report 都能查。", "var(--orange)", 175),
      ),
      footer("local-first · deterministic core · generated explanation is traceable"),
    ].join(""),
  },
  {
    file: "03-scenario.html",
    label: "場景",
    title: "正式審計前的工程化初篩",
    bodyClass: "",
    content: [
      bgGrid(),
      div("title", "", `${div("eyebrow", "", p("SCENARIO"))}${h(1, "使用者要更快知道先查哪裡")}${div("subtitle", "", p("工具的價值不是取代審計師，而是把可重複、可驗證、可追蹤的初篩流程固定下來。"))}`),
      panel(48, 255, 188, 150, `${h(3, "個人開發者")}${p("提交前抓 reentrancy、unchecked call 與 delegatecall 風險。")}`),
      panel(272, 255, 188, 150, `${h(3, "Web3 團隊")}${p("把 Slither 結果整理成可交給審計師複查的報告。")}`),
      panel(496, 255, 188, 150, `${h(3, "課程 Demo")}${p("展示從靜態分析到報告生成的完整安全 pipeline。")}`),
      panel(720, 255, 188, 150, `${h(3, "履歷作品")}${p("呈現 SAST、RAG、MLX、CI 評測與可觀測性能力。")}`),
      line("left:48pt;top:232pt;width:860pt;height:3pt;", "bar"),
      footer("target user: developer / Web3 team / security course / interview portfolio"),
    ].join(""),
  },
  {
    file: "04-flow.html",
    label: "流程",
    title: "從合約到可追溯報告",
    bodyClass: "paper",
    content: [
      div("title", "", `${div("eyebrow", "", p("FLOW"))}${h(1, "LLM 只處理解釋，漏洞來源保留在工具輸出")}${div("subtitle", "", p("每一步都落地為可檢查的中間結果，避免模型把不存在的漏洞寫進正式報告。"))}`),
      line("left:90pt;top:292pt;width:780pt;height:2pt;background:#111315;"),
      node(70, 250, "01", ".sol 輸入", "單檔、500 行、0.6.x–0.8.x", "var(--green)", 132),
      node(210, 250, "02", "Slither", "detector findings + AST", "var(--blue)", 132),
      node(350, 250, "03", "Adapter", "FindingSchema", "var(--orange)", 132),
      node(490, 250, "04", "RAG", "BM25 / Dense / Rerank", "var(--green)", 132),
      node(630, 250, "05", "MLX-ready", "逐 finding 生成", "var(--blue)", 132),
      node(770, 250, "06", "Report", "JSON / MD / SQLite", "var(--orange)", 132),
      panel(78, 386, 804, 52, div("code dark", "left:16pt;top:14pt;width:760pt;height:24pt;position:absolute;", p("scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports --rag-mode fallback", "mono"))),
      footer("deterministic finding → retrieval context → constrained generation → traceable report"),
    ].join(""),
  },
  {
    file: "05-architecture.html",
    label: "架構",
    title: "模組邊界以交付流程切分",
    bodyClass: "",
    content: [
      bgGrid(),
      div("title", "", `${div("eyebrow", "", p("ARCHITECTURE"))}${h(1, "CLI-first package，外部工具可替換")}${div("subtitle", "", p("核心模組圍繞 analyze lifecycle：讀合約、跑工具、正規化、檢索、生成、驗證、追蹤。"))}`),
      panel(54, 210, 285, 252, div("code", "left:18pt;top:18pt;width:245pt;height:210pt;position:absolute;", p("src/smart_contract_audit/<br>├─ cli.py<br>├─ analyzer.py<br>├─ slither_runner.py<br>├─ finding_adapter.py<br>├─ rag/<br>├─ llm/<br>├─ validation/<br>└─ trace/", "mono"))),
      panel(392, 210, 235, 105, `${h(3, "slither_runner")}${p("準備 solc、呼叫 Slither、解析 JSON。")}`),
      panel(660, 210, 235, 105, `${h(3, "finding_adapter")}${p("detector → vulnerability_type / severity。")}`),
      panel(392, 352, 235, 105, `${h(3, "rag")}${p("文件萃取、chunk、JSONL、BM25 fallback。")}`),
      panel(660, 352, 235, 105, `${h(3, "trace")}${p("analysis_trace 與 trace_findings 可查。")}`),
      footer("module boundary follows audit lifecycle, not UI pages"),
    ].join(""),
  },
  {
    file: "06-static-core.html",
    label: "靜態核心",
    title: "漏洞判定不交給模型猜",
    bodyClass: "paper",
    content: [
      div("title", "", `${div("eyebrow", "", p("STATIC ANALYSIS"))}${h(1, "Slither finding 是正式報告的根")}${div("subtitle", "", p("未映射 detector 只進 trace，不進正式 finding；模型負責說明與修復建議。"))}`),
      div("abs", "left:64pt;top:198pt;width:370pt;", `${h(2, "Detector mapping")}`),
      div("table-row", "left:64pt;top:252pt;width:390pt;height:44pt;", `${h(3, "reentrancy-eth")}${p("reentrancy / High")}`),
      div("table-row", "left:64pt;top:304pt;width:390pt;height:44pt;", `${h(3, "unchecked-lowlevel")}${p("unchecked_external_call / Medium")}`),
      div("table-row", "left:64pt;top:356pt;width:390pt;height:44pt;", `${h(3, "controlled-delegatecall")}${p("dangerous_delegatecall / High")}`),
      div("table-row", "left:64pt;top:408pt;width:390pt;height:44pt;", `${h(3, "controlled-array-length")}${p("array_length_manipulation / Medium")}`),
      panel(570, 205, 290, 225, div("code dark", "left:18pt;top:18pt;width:250pt;height:180pt;position:absolute;", p("finding_id<br>vulnerability_type<br>severity<br>location<br>evidence<br>finding_confidence<br>explanation_confidence<br>static_tool_source<br>detector_name<br>partial", "mono"))),
      footer("finding_confidence comes from static source, explanation_confidence comes from generation quality"),
    ].join(""),
  },
  {
    file: "07-rag.html",
    label: "RAG",
    title: "髒資料先清成可檢索知識",
    bodyClass: "",
    content: [
      bgGrid(),
      div("title", "", `${div("eyebrow", "", p("UNSTRUCTURED DATA + RAG"))}${h(1, "公開審計報告要先拆成乾淨 chunks")}${div("subtitle", "", p("PDF、HTML、Markdown、表格與 Solidity 程式碼混在一起；流程先分離純文字與程式碼，再寫 metadata。"))}`),
      node(72, 230, "01", "格式偵測", "PDF / HTML / Markdown 分流。", "var(--green)", 210),
      node(72, 306, "02", "程式碼保留", "Solidity code block 不在中間切斷。", "var(--blue)", 210),
      node(72, 382, "03", "Metadata", "source_id、severity、vuln_type、sha256。", "var(--orange)", 210),
      panel(470, 218, 390, 190,
        `${h(2, "RAG modes")}` +
        div("table-row", "left:20pt;top:64pt;width:340pt;height:32pt;", `${h(3, "quality")}${p("BM25 50 + Dense 50 → top 5")}`) +
        div("table-row", "left:20pt;top:102pt;width:340pt;height:32pt;", `${h(3, "balanced")}${p("BM25 30 + Dense 30 → top 3")}`) +
        div("table-row", "left:20pt;top:140pt;width:340pt;height:32pt;", `${h(3, "fallback")}${p("BM25 20 only → top 3")}`),
      ),
      metric(708, 428, "1.0", "fixture recall@k", "var(--green)"),
      footer("data cleaning reduces retrieval noise before prompt packing"),
    ].join(""),
  },
  {
    file: "08-mlx.html",
    label: "MLX",
    title: "Apple MLX-ready 本地推理策略",
    bodyClass: "paper",
    content: [
      div("title", "", `${div("eyebrow", "", p("LOCAL INFERENCE"))}${h(1, "16GB 環境下先控制上下文，再控制模型")}${div("subtitle", "", p("逐 finding 生成、4-bit 權重量化、固定輸出上限與 timeout 降級，讓本地小模型不拖垮完整流程。"))}`),
      metric(64, 240, "4.0 GB", "8B 4-bit 權重估算"),
      metric(64, 345, "1024 tokens", "單 finding 輸出上限", "var(--blue)"),
      panel(470, 210, 370, 240,
        node(20, 22, "80s", "fast mode", "後續 finding 強制 fast mode。", "var(--green)", 300) +
        node(20, 88, "100s", "fallback mode", "後續 finding 強制 fallback mode。", "var(--blue)", 300) +
        node(20, 154, "115s", "stop generation", "停止 LLM，保留 deterministic findings。", "var(--red)", 300),
      ),
      footer("resource control: per-finding batching · context cap · timeout fallback"),
    ].join(""),
  },
  {
    file: "09-trace.html",
    label: "Trace",
    title: "Trace 把每個結論接回來源",
    bodyClass: "",
    content: [
      bgGrid(),
      div("title", "", `${div("eyebrow", "", p("OBSERVABILITY"))}${h(1, "可回放是資安輔助工具的信任基礎")}${div("subtitle", "", p("報告不是黑箱文字；每個 finding 都能查到 Slither 原始資料、RAG chunks、prompt 與最終欄位。"))}`),
      panel(72, 232, 315, 190, div("code", "left:22pt;top:22pt;width:270pt;height:145pt;position:absolute;", p("finding_id<br>  → slither_raw<br>  → normalized_schema<br>  → rag_chunk_ids<br>  → packed_prompt<br>  → llm_raw_output<br>  → final_report_field", "mono"))),
      panel(540, 210, 310, 64, `${h(3, "analysis_trace")}${p("contract_id、model_version、dataset_version、final_status。")}`),
      panel(540, 302, 310, 64, `${h(3, "trace_findings")}${p("per-finding rag_mode、耗時、chunks_used。")}`),
      panel(540, 394, 310, 64, `${h(3, "trace_lookup")}${p("CLI 查詢，支援定位單一 finding。")}`),
      footer("trace table stores evidence chain instead of only storing final answer"),
    ].join(""),
  },
  {
    file: "10-case.html",
    label: "案例",
    title: "VulnerableVault Reentrancy 實例",
    bodyClass: "paper",
    content: [
      div("title", "", `${div("eyebrow", "", p("REAL CASE"))}${h(1, "外部 call 發生在餘額歸零之前")}${div("subtitle", "", p("Slither 在測試合約中找到 reentrancy-eth，adapter 映射成 High severity finding。"))}`),
      panel(60, 205, 420, 250, div("code", "left:18pt;top:18pt;width:375pt;height:205pt;position:absolute;", p("function withdraw() external {<br>  uint256 amount = balances[msg.sender];<br>  (bool success,) = msg.sender.call{value: amount}(\"\");<br>  require(success, \"transfer failed\");<br>  balances[msg.sender] = 0;<br>}", "mono"))),
      panel(540, 216, 320, 54, `${h(3, "偵測器")}${p("reentrancy-eth")}`),
      panel(540, 288, 320, 54, `${h(3, "位置")}${p("tests/contracts/VulnerableVault.sol:11-16")}`),
      panel(540, 360, 320, 54, `${h(3, "修復")}${p("checks-effects-interactions + nonReentrant")}`),
      footer("case finding: external interaction precedes state update"),
    ].join(""),
  },
  {
    file: "11-validation.html",
    label: "驗收",
    title: "驗收結果已過品質門檻",
    bodyClass: "",
    content: [
      bgGrid(),
      div("title", "", `${div("eyebrow", "", p("VALIDATION"))}${h(1, "不是設計稿假資料，是本專案實測輸出")}${div("subtitle", "", p("測試集中在基礎模組、RAG 檢索、AI judge、自動化端到端流程與硬體資源控制。"))}`),
      metric(72, 240, "10 passed", "pytest 全量回歸"),
      metric(290, 240, "All passed", "ruff", "var(--blue)"),
      metric(532, 240, "1.0", "RAG recall@k", "var(--orange)"),
      metric(740, 240, "5.0", "Judge score", "var(--red)"),
      panel(70, 405, 820, 50, div("code", "left:18pt;top:15pt;width:780pt;height:22pt;position:absolute;", p("E2E: 2 passed · 1.67s · maximum resident set size = 54,083,584 bytes", "mono"))),
      footer("test commands: uv run pytest · uv run ruff check . · eval/run_eval.py · eval/run_judge.py"),
    ].join(""),
  },
  {
    file: "12-applications.html",
    label: "應用",
    title: "展示給面試官看的不是單一模型",
    bodyClass: "paper",
    content: [
      div("title", "", `${div("eyebrow", "", p("APPLICATION"))}${h(1, "這是一條完整可交付的安全分析工程管線")}${div("subtitle", "", p("從資安工具、資料工程、AI 工程到 CI 評測，作品展示的是工程化整合能力。"))}`),
      panel(64, 210, 250, 70, `${h(3, "Security tooling")}${p("Slither / solc / detector mapping / SWC。")}`),
      panel(354, 210, 250, 70, `${h(3, "AI engineering")}${p("RAG / prompt packing / LLM-as-Judge / MLX-ready。")}`),
      panel(644, 210, 250, 70, `${h(3, "Data engineering")}${p("PDF / HTML / Markdown 萃取、metadata、manifest。")}`),
      panel(64, 322, 250, 70, `${h(3, "Software delivery")}${p("pytest、ruff、GitHub Actions、CI 評測。")}`),
      panel(354, 322, 250, 70, `${h(3, "Observability")}${p("SQLite trace、per-finding rag mode、耗時。")}`),
      panel(644, 322, 250, 70, `${h(3, "Resource control")}${p("逐 finding 批次、timeout、fallback。")}`),
      footer("portfolio story: security + data + local AI + delivery discipline"),
    ].join(""),
  },
  {
    file: "13-huashu.html",
    label: "Huashu",
    title: "Huashu-Design 版型方法",
    bodyClass: "",
    content: [
      bgGrid(),
      div("title", "", `${div("eyebrow", "", p("DESIGN METHOD"))}${h(1, "HTML 做設計，PPTX 仍可交付")}${div("subtitle", "", p("本版採 Huashu 的 HTML-native slide deck 流程：多文件、可驗證、可轉 PPTX。"))}`),
      panel(66, 230, 250, 68, `${h(3, "01 HTML-native")}${p("每頁獨立 HTML，樣式隔離，瀏覽器可演示。")}`),
      panel(354, 230, 250, 68, `${h(3, "02 Editable PPTX")}${p("文字在 h/p 內，避開不支援的 gradient 與 background-image。")}`),
      panel(642, 230, 250, 68, `${h(3, "03 Playwright QA")}${p("逐頁 render 截圖，檢查白屏、裁切、遮擋。")}`),
      panel(66, 338, 826, 76, div("code", "left:20pt;top:18pt;width:780pt;height:36pt;position:absolute;", p("source: github.com/Eskasia/huashu-design · local skill: /Users/william/.skills-manager/skills/huashu-design", "mono"))),
      footer("deliverables: index.html · screenshots · image-mode PPTX · editable-mode PPTX"),
    ].join(""),
  },
];

await writeFile(path.join(sharedDir, "tokens.css"), css);

for (const spec of slides) {
  await writeFile(path.join(slidesDir, spec.file), slideShell(spec.title, spec.bodyClass, spec.content));
}

const index = `<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>智能合約安全分析助理 · Huashu Redesign</title>
<script>
window.DECK_WIDTH = 1280;
window.DECK_HEIGHT = 720;
window.DECK_MANIFEST = ${JSON.stringify(slides.map(({ file, label }) => ({ file: `slides/${file}`, label })), null, 2)};
</script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width:100%; height:100%; overflow:hidden; background:#050707; font-family:-apple-system, "PingFang TC", sans-serif; }
#stage { position:fixed; top:0; left:0; width:1280px; height:720px; transform-origin:top left; background:#0B0D0E; box-shadow:0 24px 90px rgba(0,0,0,.55); }
iframe { width:100%; height:100%; border:0; display:block; background:#0B0D0E; }
.counter { position:fixed; right:18px; bottom:18px; z-index:10; color:#F7F2DF; background:rgba(0,0,0,.58); border:1px solid rgba(57,255,136,.28); border-radius:999px; padding:7px 12px; font-size:12px; }
.zone { position:fixed; top:0; bottom:0; width:18%; z-index:8; }
.left { left:0; } .right { right:0; }
@media print { @page { size: 1280px 720px; margin:0; } .counter,.zone{display:none} #stage{position:static;transform:none!important;box-shadow:none} }
</style>
</head>
<body>
<div id="stage"><iframe id="frame"></iframe></div>
<div class="zone left" id="prev"></div><div class="zone right" id="next"></div>
<div class="counter" id="counter"></div>
<script>
const W=window.DECK_WIDTH,H=window.DECK_HEIGHT,deck=window.DECK_MANIFEST;
const stage=document.getElementById("stage"),frame=document.getElementById("frame"),counter=document.getElementById("counter");
let i=0;
function fit(){const s=Math.min(innerWidth/W,innerHeight/H);stage.style.transform="translate("+((innerWidth-W*s)/2)+"px,"+((innerHeight-H*s)/2)+"px) scale("+s+")";}
function show(n){i=Math.max(0,Math.min(deck.length-1,n));frame.src=deck[i].file;counter.textContent=(i+1)+" / "+deck.length+" · "+deck[i].label;history.replaceState(null,"","#"+(i+1));}
addEventListener("resize",fit);
addEventListener("keydown",e=>{if(["ArrowRight"," ","PageDown"].includes(e.key)){e.preventDefault();show(i+1)} if(["ArrowLeft","PageUp"].includes(e.key)){e.preventDefault();show(i-1)} if(e.key==="Home"){show(0)} if(e.key==="End"){show(deck.length-1)}});
document.getElementById("prev").onclick=()=>show(i-1);document.getElementById("next").onclick=()=>show(i+1);
const h=location.hash.match(/^#(\\d+)$/); if(h) i=Number(h[1])-1; fit(); show(i);
</script>
</body>
</html>`;

await writeFile(path.join(ROOT, "index.html"), index);
console.log(`generated ${slides.length} slides`);
