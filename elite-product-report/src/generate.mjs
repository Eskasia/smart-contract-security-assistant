import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(".");
const slidesDir = path.join(root, "slides");
const sharedDir = path.join(root, "shared");
const outputDir = path.join(root, "output");
const screenshotDir = path.join(root, "screenshots");

await Promise.all([
  mkdir(slidesDir, { recursive: true }),
  mkdir(sharedDir, { recursive: true }),
  mkdir(outputDir, { recursive: true }),
  mkdir(screenshotDir, { recursive: true }),
]);

const css = String.raw`
* { box-sizing: border-box; margin: 0; padding: 0; }
:root {
  --navy: #003366;
  --blue: #0078D4;
  --blue2: #2B88D8;
  --bg: #F3F2F1;
  --white: #FFFFFF;
  --text: #323130;
  --muted: #605E5C;
  --line: #D2D0CE;
  --green: #107C10;
  --amber: #F2C811;
  --red: #D13438;
}
html, body {
  width: 960pt;
  height: 540pt;
  overflow: hidden;
  background: var(--bg);
  color: var(--text);
  font-family: "Segoe UI", Arial, "PingFang TC", "Microsoft JhengHei", sans-serif;
}
body { position: relative; letter-spacing: 0; }
h1, h2, h3, p, li { line-height: 1.15; font-weight: 400; }
h1 { font-size: 50pt; font-weight: 700; color: var(--navy); }
h2 { font-size: 40pt; font-weight: 700; color: var(--navy); }
h3 { font-size: 20pt; font-weight: 700; color: var(--text); }
p { font-size: 18pt; line-height: 1.42; color: var(--muted); }
.caption p { font-size: 12pt; color: var(--muted); line-height: 1.35; }
.label p {
  font-size: 11pt;
  font-weight: 700;
  letter-spacing: 0.10em;
  color: var(--blue);
  text-transform: uppercase;
}
.abs { position: absolute; }
.title { position: absolute; left: 74pt; top: 58pt; width: 810pt; }
.title p { margin-top: 13pt; width: 640pt; }
.topline { position: absolute; left: 74pt; top: 38pt; width: 812pt; height: 2pt; background: var(--blue); }
.footer { position: absolute; left: 74pt; right: 74pt; bottom: 26pt; height: 20pt; border-top: 1pt solid var(--line); padding-top: 7pt; }
.footer p { font-size: 9pt; color: #797775; }
.panel {
  position: absolute;
  background: var(--white);
  border: 1pt solid var(--line);
  border-radius: 5pt;
  padding: 18pt 20pt;
}
.panel.blue {
  background: var(--navy);
  border-color: var(--navy);
}
.panel.blue h2, .panel.blue h3 { color: var(--white); }
.panel.blue p { color: #DDEAF6; }
.metric h2 { font-size: 60pt; font-weight: 700; }
.metric p { font-size: 14pt; margin-top: 7pt; color: var(--muted); }
.mini h3 { font-size: 15pt; }
.mini p { font-size: 12pt; line-height: 1.35; margin-top: 5pt; }
.step h3 { font-size: 15pt; }
.step p { font-size: 11.5pt; line-height: 1.34; margin-top: 4pt; }
.dot { position: absolute; width: 22pt; height: 22pt; border-radius: 99pt; background: var(--blue); }
.dot p { color: var(--white); font-size: 10pt; line-height: 22pt; text-align: center; font-weight: 700; }
.rule { position: absolute; height: 1pt; background: var(--line); }
.thick { height: 3pt; background: var(--blue); }
.chip { position: absolute; background: #E7F1FB; border-radius: 99pt; padding-top: 6pt; }
.chip p { text-align: center; font-size: 10pt; font-weight: 700; color: var(--navy); }
.code p {
  font-family: Menlo, Consolas, monospace;
  font-size: 10pt;
  line-height: 1.35;
  color: #1B1A19;
}
.table-row { position: absolute; border-top: 1pt solid var(--line); }
.table-row h3 { position: absolute; left: 0; top: 8pt; font-size: 13pt; }
.table-row p { position: absolute; left: 168pt; top: 8pt; width: 245pt; font-size: 11pt; line-height: 1.28; }
.bar-bg { position: absolute; height: 10pt; background: #E1DFDD; border-radius: 99pt; }
.bar-fill { position: absolute; height: 10pt; background: var(--blue); border-radius: 99pt; }
`;

const p = (text, cls = "") => `<p${cls ? ` class="${cls}"` : ""}>${text}</p>`;
const h = (level, text) => `<h${level}>${text}</h${level}>`;
const div = (cls, style, content = "") => `<div class="${cls}" style="${style}">${content}</div>`;
const line = (style, cls = "rule") => div(cls, style);
const label = (text) => div("label", "", p(text));
const footer = (text) => div("footer", "", p(text));
const title = (kicker, headline, sub) =>
  line("", "topline") + div("title", "", `${label(kicker)}${h(1, headline)}${p(sub)}`);
const panel = (x, y, w, ht, content, cls = "panel") =>
  div(cls, `left:${x}pt;top:${y}pt;width:${w}pt;height:${ht}pt;`, content);
const metric = (x, y, value, labelText, color = "var(--blue)") =>
  div("metric abs", `left:${x}pt;top:${y}pt;width:160pt;`, `${h(2, `<span style="color:${color}">${value}</span>`)}${p(labelText)}`);
const chip = (x, y, w, text) => div("chip", `left:${x}pt;top:${y}pt;width:${w}pt;height:25pt;`, p(text));
const dot = (x, y, text, color = "var(--blue)") => div("dot", `left:${x}pt;top:${y}pt;background:${color};`, p(text));
const step = (x, y, idx, name, body, color = "var(--blue)", w = 128) =>
  div("step abs", `left:${x}pt;top:${y}pt;width:${w}pt;height:74pt;`,
    dot(0, 0, idx, color) + div("abs", `left:0;top:34pt;width:${w}pt;`, `${h(3, name)}${p(body)}`),
  );
const tableRow = (x, y, w, key, value) => div("table-row", `left:${x}pt;top:${y}pt;width:${w}pt;height:38pt;`, `${h(3, key)}${p(value)}`);

function shell(name, content) {
  return `<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1280,height=720">
<title>${name}</title>
<link rel="stylesheet" href="../shared/tokens.css">
</head>
<body>
${content}
</body>
</html>
`;
}

const slides = [
  {
    file: "01-title.html",
    label: "Title",
    name: "智能合約安全分析助理",
    content: [
      title("PRODUCT REPORT", "智能合約安全分析助理", "企業產品狀態報告 · Corporate Professional style"),
      panel(620, 150, 230, 220, `${h(2, "MVP Ready")}${p("CLI、Slither、RAG、MLX-ready、Trace 與 CI 已串接。")}`, "panel blue"),
      chip(635, 330, 50, "SAST"),
      chip(696, 330, 50, "RAG"),
      chip(757, 330, 50, "MLX"),
      chip(818, 330, 50, "Trace"),
      footer("style: corporate-professional · colors: #003366 / #0078D4 / #F3F2F1"),
    ].join(""),
  },
  {
    file: "02-executive-summary.html",
    label: "Summary",
    name: "Executive Summary",
    content: [
      title("EXECUTIVE SUMMARY", "MVP 已達產品驗收線", "核心流程可以從 Solidity 合約輸入一路跑到可追溯報告輸出。"),
      metric(86, 230, "15", "pytest passed", "var(--green)"),
      metric(292, 230, "1.0", "RAG recall@k"),
      metric(498, 230, "5.0", "judge score", "var(--blue)"),
      metric(704, 230, "51.7 MiB", "E2E memory peak", "var(--green)"),
      panel(86, 400, 760, 52, `${h(3, "Management readout")}${p("可作為正式審計前初篩產品 demo；下一版需補真實專案支援與外部 judge API。")}`),
      footer("validation: uv run pytest · ruff · eval/run_eval.py · eval/run_judge.py"),
    ].join(""),
  },
  {
    file: "03-positioning.html",
    label: "Positioning",
    name: "Product Positioning",
    content: [
      title("PRODUCT POSITIONING", "正式審計前的工程化初篩", "產品把靜態分析、檢索、生成與 trace 整合成固定工作流。"),
      panel(84, 220, 230, 150, `${h(3, "Target users")}${p("Solidity 開發者、Web3 團隊、資安課程與履歷作品審查。")}`, "panel mini"),
      panel(364, 220, 230, 150, `${h(3, "Primary job")}${p("找出高風險 finding，產出修復建議，保留每個結論來源。")}`, "panel mini"),
      panel(644, 220, 230, 150, `${h(3, "Current scope")}${p("單檔 Solidity 合約，500 行以內；多檔專案放入 v0.9。")}`, "panel mini"),
      footer("one main product promise: faster triage before formal audit"),
    ].join(""),
  },
  {
    file: "04-architecture.html",
    label: "Architecture",
    name: "Architecture",
    content: [
      title("ARCHITECTURE", "工具做判定，AI 做解釋", "Slither finding 是事實來源；LLM 僅生成可追溯的修復說明。"),
      line("left:92pt;top:294pt;width:770pt;", "rule thick"),
      step(78, 242, "1", ".sol input", "single contract", "var(--blue)", 110),
      step(214, 242, "2", "Slither", "detector + AST", "var(--blue)", 110),
      step(350, 242, "3", "Adapter", "FindingSchema", "var(--blue)", 120),
      step(496, 242, "4", "RAG", "evidence chunks", "var(--green)", 110),
      step(632, 242, "5", "MLX-ready", "local output", "var(--blue)", 120),
      step(786, 242, "6", "Trace", "JSON / MD / DB", "var(--green)", 110),
      footer("template: process_flow · transition: fade/morph class"),
    ].join(""),
  },
  {
    file: "05-module-map.html",
    label: "Modules",
    name: "Module Map",
    content: [
      title("MODULE MAP", "模組邊界跟隨分析生命週期", "CLI-first package 讓工具能被終端、CI 與未來 UI 重用。"),
      panel(86, 210, 265, 215, div("code", "", p("src/smart_contract_audit/<br>├─ cli.py<br>├─ analyzer.py<br>├─ slither_runner.py<br>├─ finding_adapter.py<br>├─ rag/<br>├─ llm/<br>├─ validation/<br>└─ trace/"))),
      tableRow(420, 220, 390, "slither_runner", "solc 檢查、Slither 呼叫、JSON 解析"),
      tableRow(420, 278, 390, "finding_adapter", "detector 映射到 vulnerability_type"),
      tableRow(420, 336, 390, "rag", "chunks、BM25 fallback、eval fixture"),
      tableRow(420, 394, 390, "trace", "SQLite 查詢 finding 證據鏈"),
      footer("template: mixed content · max 2 columns"),
    ].join(""),
  },
  {
    file: "06-static-analysis.html",
    label: "SAST",
    name: "Static Analysis",
    content: [
      title("STATIC ANALYSIS", "正式 finding 來自 Slither detector", "未映射 detector 進 trace 供人工複查，避免模型新增不存在的漏洞。"),
      tableRow(92, 220, 420, "reentrancy-eth", "reentrancy / High"),
      tableRow(92, 278, 420, "unchecked-lowlevel", "unchecked_external_call / Medium"),
      tableRow(92, 336, 420, "controlled-delegatecall", "dangerous_delegatecall / High"),
      tableRow(92, 394, 420, "controlled-array-length", "array_length_manipulation / Medium"),
      panel(616, 232, 210, 170, div("code", "", p("finding_id<br>vulnerability_type<br>severity<br>location<br>evidence<br>finding_confidence<br>detector_name<br>partial"))),
      footer("Slither analyzer verified locally: 0.11.5"),
    ].join(""),
  },
  {
    file: "07-data-rag.html",
    label: "RAG",
    name: "Data + RAG",
    content: [
      title("DATA + RAG", "髒資料先變成可評測語料", "公開審計報告需先分離文字、程式碼與 metadata，再進入檢索。"),
      panel(90, 220, 220, 142, `${h(3, "Extraction")}${p("PDF / HTML / Markdown 分流，保留 Solidity code block。")}`, "panel mini"),
      panel(370, 220, 220, 142, `${h(3, "Retrieval")}${p("quality、balanced、fast、fallback 四種模式。")}`, "panel mini"),
      panel(650, 220, 220, 142, `${h(3, "Evaluation")}${p("eval/run_eval.py 計算正確文件 recall@k。")}`, "panel mini"),
      metric(405, 392, "1.0", "fixture recall@k", "var(--green)"),
      footer("template: three_column_layout + single metric emphasis"),
    ].join(""),
  },
  {
    file: "08-local-inference.html",
    label: "MLX",
    name: "Local Inference",
    content: [
      title("LOCAL INFERENCE", "先控資源，再控生成品質", "MLX-ready 介面預留 Apple Silicon 本地模型與 4-bit 權重量化部署。"),
      metric(92, 238, "4.0 GB", "8B 4-bit estimate", "var(--green)"),
      metric(330, 238, "1024", "tokens per finding"),
      metric(568, 238, "115s", "LLM stop threshold", "var(--red)"),
      panel(696, 232, 168, 165, `${h(3, "Degrade path")}${p("80s fast mode<br>100s fallback mode<br>115s deterministic output")}`, "panel mini"),
      footer("resource target: 16GB MacBook Pro workflow"),
    ].join(""),
  },
  {
    file: "09-traceability.html",
    label: "Trace",
    name: "Traceability",
    content: [
      title("TRACEABILITY", "每個報告欄位都能查回來源", "Trace 把 Slither raw、schema、RAG chunks、prompt 與 final report 串成證據鏈。"),
      panel(100, 235, 285, 160, div("code", "", p("finding_id<br>  → slither_raw<br>  → normalized_schema<br>  → rag_chunk_ids<br>  → packed_prompt<br>  → llm_raw_output<br>  → report_field"))),
      panel(482, 220, 310, 56, `${h(3, "analysis_trace")}${p("contract_id、dataset_version、final_status")}`, "panel mini"),
      panel(482, 304, 310, 56, `${h(3, "trace_findings")}${p("per-finding rag_mode、耗時、chunks_used")}`, "panel mini"),
      panel(482, 388, 310, 56, `${h(3, "trace_lookup")}${p("CLI 查詢單一 finding")}`, "panel mini"),
      footer("observability: SQLite trace database"),
    ].join(""),
  },
  {
    file: "10-case-study.html",
    label: "Case",
    name: "Case Study",
    content: [
      title("CASE STUDY", "VulnerableVault：reentrancy", "外部 call 發生在餘額歸零前，Slither 映射成 High severity finding。"),
      panel(90, 220, 380, 190, div("code", "", p("function withdraw() external {<br>  uint256 amount = balances[msg.sender];<br>  (bool success,) = msg.sender.call{value: amount}(\"\");<br>  require(success, \"transfer failed\");<br>  balances[msg.sender] = 0;<br>}"))),
      tableRow(545, 230, 300, "detector", "reentrancy-eth"),
      tableRow(545, 290, 300, "location", "VulnerableVault.sol:11-16"),
      tableRow(545, 350, 300, "fix", "checks-effects-interactions + nonReentrant"),
      footer("template: before/after evidence card"),
    ].join(""),
  },
  {
    file: "11-validation.html",
    label: "Validation",
    name: "Validation",
    content: [
      title("VALIDATION", "自動化測試覆蓋核心路徑", "單元測試、lint、RAG eval、judge eval 與 E2E 資源觀測都已納入驗收。"),
      metric(96, 238, "15", "pytest passed", "var(--green)"),
      metric(300, 238, "All", "ruff passed"),
      metric(504, 238, "2", "E2E passed", "var(--green)"),
      metric(708, 238, "54.23M", "max RSS bytes", "var(--blue)"),
      line("left:96pt;top:408pt;width:760pt;", "rule"),
      div("caption abs", "left:96pt;top:424pt;width:760pt;", p("commands: uv run pytest · uv run ruff check . · uv run python eval/run_eval.py · uv run python eval/run_judge.py")),
      footer("template: metrics_dashboard"),
    ].join(""),
  },
  {
    file: "12-roadmap.html",
    label: "Roadmap",
    name: "Roadmap",
    content: [
      title("ROADMAP", "下一版提高真實專案可用性", "優先補專案相容性與外部評測，再擴大生成能力。"),
      panel(86, 226, 220, 150, `${h(3, "v0.8 Completed")}${p("CLI、Slither、RAG fixture、MLX-ready、Trace、CI。")}`, "panel mini"),
      panel(370, 226, 220, 150, `${h(3, "v0.9 Priority")}${p("Foundry/Hardhat、多檔 import、Mythril、外部 judge API。")}`, "panel mini"),
      panel(654, 226, 220, 150, `${h(3, "v1.0 Gate")}${p("公開審計報告 corpus、Dense retrieval、報告審核 UI。")}`, "panel mini"),
      footer("template: timeline_slide"),
    ].join(""),
  },
];

await writeFile(path.join(sharedDir, "tokens.css"), css);
for (const slide of slides) {
  await writeFile(path.join(slidesDir, slide.file), shell(slide.name, slide.content));
}

const index = `<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>智能合約安全分析助理 · Elite Product Report</title>
<script>
window.DECK_WIDTH = 1280;
window.DECK_HEIGHT = 720;
window.DECK_MANIFEST = ${JSON.stringify(slides.map(({ file, label }) => ({ file: `slides/${file}`, label })), null, 2)};
</script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width:100%; height:100%; overflow:hidden; background:#201F1E; font-family:"Segoe UI", Arial, sans-serif; }
#stage { position:fixed; top:0; left:0; width:1280px; height:720px; transform-origin:top left; background:#F3F2F1; box-shadow:0 24px 80px rgba(0,0,0,.35); }
iframe { width:100%; height:100%; border:0; display:block; background:#F3F2F1; }
.counter { position:fixed; right:18px; bottom:18px; z-index:10; color:#fff; background:rgba(0,51,102,.9); border-radius:999px; padding:7px 12px; font-size:12px; }
.zone { position:fixed; top:0; bottom:0; width:18%; z-index:8; }
.left { left:0; } .right { right:0; }
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

await writeFile(path.join(root, "index.html"), index);
console.log(`generated ${slides.length} elite product report slides`);
