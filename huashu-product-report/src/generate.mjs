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
  --paper: #F8F7F1;
  --ink: #101417;
  --navy: #112A46;
  --muted: #68706D;
  --soft: #E9E5D8;
  --line: #CFC8B8;
  --green: #168A5A;
  --blue: #2368A2;
  --amber: #C98B16;
  --red: #B84640;
}
html, body {
  width: 960pt;
  height: 540pt;
  overflow: hidden;
  background: var(--paper);
  color: var(--ink);
  font-family: "PingFang TC", "PingFang SC", "Microsoft JhengHei", system-ui, -apple-system, sans-serif;
}
body { position: relative; letter-spacing: 0; }
h1, h2, h3, h4, p, li { line-height: 1.14; font-weight: 500; }
h1 { font-size: 42pt; font-weight: 800; color: var(--navy); }
h2 { font-size: 25pt; font-weight: 800; color: var(--navy); }
h3 { font-size: 14pt; font-weight: 800; color: var(--ink); }
p { font-size: 11.5pt; line-height: 1.38; color: var(--muted); }
.abs { position: absolute; }
.title { position: absolute; left: 50pt; top: 42pt; width: 700pt; }
.title p { margin-top: 9pt; width: 530pt; }
.label p {
  color: var(--green);
  font-size: 8.5pt;
  font-weight: 900;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  margin-bottom: 8pt;
}
.rule { position: absolute; height: 1pt; background: var(--line); }
.rule.navy { background: var(--navy); }
.rule.green { background: var(--green); height: 2pt; }
.panel {
  position: absolute;
  background: rgba(255,255,255,0.52);
  border: 1pt solid var(--line);
  border-radius: 4pt;
  padding: 10pt 12pt;
}
.panel.dark {
  background: var(--navy);
  border-color: var(--navy);
}
.panel.dark h3, .panel.dark h2 { color: #FFFFFF; }
.panel.dark p { color: #D8E1E8; }
.metric h2 { font-size: 34pt; }
.metric p { margin-top: 5pt; font-size: 9.5pt; }
.mono p, p.mono {
  font-family: Menlo, Monaco, Consolas, monospace;
  font-size: 8.8pt;
  line-height: 1.34;
}
.code p {
  font-family: Menlo, Monaco, Consolas, monospace;
  font-size: 9.2pt;
  line-height: 1.35;
  color: #0D2218;
}
.note p {
  font-size: 10pt;
  line-height: 1.42;
}
.chip {
  position: absolute;
  border: 1pt solid var(--line);
  border-radius: 99pt;
  background: #FFFFFF;
}
.chip p {
  text-align: center;
  font-size: 8.8pt;
  font-weight: 800;
  color: var(--navy);
}
.dot {
  position: absolute;
  width: 18pt;
  height: 18pt;
  border-radius: 99pt;
  background: var(--green);
}
.dot p {
  color: #FFFFFF;
  font-size: 8.5pt;
  font-weight: 900;
  text-align: center;
  line-height: 18pt;
}
.rowline { position: absolute; border-top: 1pt solid var(--line); }
.rowline h3 { position: absolute; left: 0; top: 8pt; font-size: 12pt; }
.rowline p { position: absolute; left: 160pt; top: 8pt; width: 230pt; font-size: 9.4pt; }
.foot { position: absolute; left: 50pt; right: 50pt; bottom: 23pt; border-top: 1pt solid var(--line); padding-top: 7pt; }
.foot p { font-size: 7.8pt; color: #78807B; font-family: Menlo, Monaco, Consolas, monospace; }
.grid-v { position: absolute; top: 34pt; bottom: 48pt; width: 1pt; background: rgba(207,200,184,0.55); }
.grid-h { position: absolute; left: 50pt; right: 50pt; height: 1pt; background: rgba(207,200,184,0.55); }
`;

function p(text, cls = "") {
  return `<p${cls ? ` class="${cls}"` : ""}>${text}</p>`;
}
function h(level, text) {
  return `<h${level}>${text}</h${level}>`;
}
function div(cls, style, content = "") {
  return `<div class="${cls}" style="${style}">${content}</div>`;
}
function label(text) {
  return div("label", "", p(text));
}
function title(kicker, headline, sub) {
  return div("title", "", `${label(kicker)}${h(1, headline)}${p(sub)}`);
}
function rule(style, cls = "rule") {
  return div(cls, style);
}
function panel(x, y, w, ht, content, extra = "") {
  return div("panel", `left:${x}pt;top:${y}pt;width:${w}pt;height:${ht}pt;${extra}`, content);
}
function darkPanel(x, y, w, ht, content) {
  return div("panel dark", `left:${x}pt;top:${y}pt;width:${w}pt;height:${ht}pt;`, content);
}
function metric(x, y, value, labelText, color = "var(--green)") {
  return div("metric abs", `left:${x}pt;top:${y}pt;width:150pt;`, `${h(2, `<span style="color:${color}">${value}</span>`)}${p(labelText)}`);
}
function dot(x, y, text, color = "var(--green)") {
  return div("dot", `left:${x}pt;top:${y}pt;background:${color};`, p(text));
}
function node(x, y, idx, titleText, body, color = "var(--green)", w = 210) {
  return div("abs", `left:${x}pt;top:${y}pt;width:${w}pt;height:48pt;`,
    dot(0, 0, idx, color) +
    div("abs", `left:27pt;top:-1pt;width:${w - 27}pt;`, `${h(3, titleText)}${p(body)}`),
  );
}
function chip(x, y, w, text) {
  return div("chip", `left:${x}pt;top:${y}pt;width:${w}pt;height:22pt;padding-top:5pt;`, p(text));
}
function row(x, y, w, key, value) {
  return div("rowline", `left:${x}pt;top:${y}pt;width:${w}pt;height:38pt;`, `${h(3, key)}${p(value)}`);
}
function grid() {
  return [
    div("grid-v", "left:290pt;"),
    div("grid-v", "left:530pt;"),
    div("grid-v", "left:770pt;"),
    div("grid-h", "top:178pt;"),
    div("grid-h", "top:316pt;"),
    div("grid-h", "top:454pt;"),
  ].join("");
}
function foot(text) {
  return div("foot", "", p(text));
}
function slideShell(name, content) {
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
    file: "01-cover.html",
    label: "封面",
    name: "產品報告",
    content: [
      grid(),
      rule("left:50pt;top:118pt;width:410pt;", "rule green"),
      title("PRODUCT REPORT", "智能合約安全分析助理", "產品狀態報告 · v0.8 · 本地漏洞初篩與可追溯 AI 修復建議"),
      darkPanel(590, 100, 270, 305, `${h(2, "交付狀態")}<p>可執行 CLI、Slither 串接、RAG fixture、MLX-ready 介面、SQLite trace、CI workflow 與端到端測試。</p>`),
      chip(595, 360, 64, "SAST"),
      chip(670, 360, 64, "RAG"),
      chip(745, 360, 64, "MLX"),
      chip(820, 360, 64, "Trace"),
      foot("report scope: product positioning · architecture · validation · risks · roadmap"),
    ].join(""),
  },
  {
    file: "02-executive-summary.html",
    label: "摘要",
    name: "執行摘要",
    content: [
      grid(),
      title("EXECUTIVE SUMMARY", "產品已達 MVP 驗收線", "MVP——最小可行產品，已能用真實測試合約跑完從靜態分析到報告輸出的流程。"),
      metric(70, 230, "10", "pytest cases passed"),
      metric(260, 230, "1.0", "RAG recall@k", "var(--blue)"),
      metric(450, 230, "5.0", "local judge score", "var(--amber)"),
      metric(640, 230, "51.6 MiB", "E2E memory peak", "var(--green)"),
      panel(70, 365, 760, 72, `${h(3, "管理結論")}<p>現階段適合作為審計前初篩與面試展示產品；下一階段應補多檔案專案支援、真實外部 judge API 與更大的公開審計報告資料集。</p>`),
      foot("validation source: uv run pytest · uv run ruff check . · eval/run_eval.py · eval/run_judge.py"),
    ].join(""),
  },
  {
    file: "03-product-scope.html",
    label: "範圍",
    name: "產品範圍",
    content: [
      grid(),
      title("PRODUCT SCOPE", "定位在正式審計前的工程化初篩", "SAST——用靜態分析工具檢查程式碼結構與常見漏洞；本產品把 SAST 結果轉成可閱讀、可追蹤的報告。"),
      panel(62, 220, 235, 150, `${h(3, "目標使用者")}<p>Solidity 開發者、Web3 小團隊、資安課程講師、履歷作品審查者。</p>`),
      panel(362, 220, 235, 150, `${h(3, "主要任務")}<p>單檔合約初篩、修復建議生成、報告輸出、finding 來源回放。</p>`),
      panel(662, 220, 235, 150, `${h(3, "產品邊界")}<p>目前支援單檔 500 行合約；大型 import graph 與完整審計流程放入下一版。</p>`),
      foot("product boundary prevents scope creep during v0.8 validation"),
    ].join(""),
  },
  {
    file: "04-architecture.html",
    label: "架構",
    name: "系統架構",
    content: [
      grid(),
      title("ARCHITECTURE", "確定性工具做判定，AI 做解釋", "RAG——先檢索技術文件與審計語料，再把相關片段交給模型生成答案。"),
      rule("left:90pt;top:292pt;width:770pt;", "rule navy"),
      node(70, 250, "1", ".sol input", "單檔 Solidity 合約", "var(--green)", 125),
      node(205, 250, "2", "Slither", "detector finding + AST", "var(--blue)", 125),
      node(340, 250, "3", "Adapter", "FindingSchema", "var(--amber)", 125),
      node(475, 250, "4", "RAG", "chunks + references", "var(--green)", 125),
      node(610, 250, "5", "MLX-ready", "local generation", "var(--blue)", 125),
      node(745, 250, "6", "Trace", "JSON / MD / SQLite", "var(--amber)", 125),
      foot("architecture principle: detector source remains authoritative through report generation"),
    ].join(""),
  },
  {
    file: "05-module-map.html",
    label: "模組",
    name: "模組地圖",
    content: [
      grid(),
      title("MODULE MAP", "程式碼邊界跟隨分析生命週期", "CLI-first 結構讓工具可在終端、CI 與未來 Web UI 之間重用。"),
      panel(60, 205, 260, 230, div("code", "position:absolute;left:16pt;top:16pt;width:220pt;height:190pt;", p("src/smart_contract_audit/<br>├─ cli.py<br>├─ analyzer.py<br>├─ slither_runner.py<br>├─ finding_adapter.py<br>├─ rag/<br>├─ llm/<br>├─ validation/<br>└─ trace/", "mono"))),
      row(385, 215, 430, "slither_runner", "準備 solc、呼叫 Slither、解析 JSON。"),
      row(385, 270, 430, "finding_adapter", "detector 映射成 vulnerability_type 與 severity。"),
      row(385, 325, 430, "rag", "萃取、chunk、JSONL、BM25 fallback。"),
      row(385, 380, 430, "trace", "analysis_trace 與 trace_findings 支援回放。"),
      foot("module map: analyzer orchestrates tools, adapters normalize output, reports stay traceable"),
    ].join(""),
  },
  {
    file: "06-static-analysis.html",
    label: "靜態分析",
    name: "靜態分析核心",
    content: [
      grid(),
      title("STATIC ANALYSIS CORE", "正式 finding 來自 Slither detector", "模型生成不新增漏洞類型；未映射 detector 進 trace 供人工複核。"),
      row(70, 215, 360, "reentrancy-eth", "reentrancy / High"),
      row(70, 270, 360, "unchecked-lowlevel", "unchecked_external_call / Medium"),
      row(70, 325, 360, "controlled-delegatecall", "dangerous_delegatecall / High"),
      row(70, 380, 360, "controlled-array-length", "array_length_manipulation / Medium"),
      panel(560, 214, 260, 185, div("code", "position:absolute;left:18pt;top:18pt;width:220pt;height:145pt;", p("finding_id<br>vulnerability_type<br>severity<br>location<br>evidence<br>finding_confidence<br>static_tool_source<br>detector_name<br>partial", "mono"))),
      foot("Slither version verified locally: 0.11.5"),
    ].join(""),
  },
  {
    file: "07-data-rag.html",
    label: "資料/RAG",
    name: "資料與檢索",
    content: [
      grid(),
      title("DATA + RETRIEVAL", "公開審計報告先轉成可評測語料", "非結構化資料萃取——把文件中的純文字、程式碼區塊與 metadata 分離，避免髒資料污染檢索。"),
      panel(62, 220, 235, 145, `${h(3, "資料清理")}<p>PDF / HTML / Markdown 分流，保留 Solidity code block，寫入 source_id、severity、sha256。</p>`),
      panel(360, 220, 235, 145, `${h(3, "檢索策略")}<p>quality / balanced / fast / fallback 四種模式，fixture 目前以 BM25 fallback 驗證。</p>`),
      panel(658, 220, 235, 145, `${h(3, "評測方式")}<p>eval/run_eval.py 讀取題庫，計算正確文件是否被檢索進 top-k。</p>`),
      metric(385, 390, "1.0", "fixture recall@k", "var(--green)"),
      foot("current corpus: data/dataset_v1.0/chunks/chunks.jsonl"),
    ].join(""),
  },
  {
    file: "08-local-inference.html",
    label: "本地推理",
    name: "本地推理策略",
    content: [
      grid(),
      title("LOCAL INFERENCE", "MLX-ready 設計先控資源再控品質", "MLX——Apple Silicon 上的機器學習框架；本產品預留本地模型、4-bit 權重量化與 timeout 降級介面。"),
      metric(70, 230, "4.0 GB", "8B 4-bit weight estimate"),
      metric(285, 230, "1024", "tokens per finding", "var(--blue)"),
      metric(500, 230, "115s", "LLM stop threshold", "var(--red)"),
      panel(690, 215, 190, 165, `${h(3, "降級規則")}${div("note", "", p("80s：後續 finding 進 fast mode。<br>100s：進 fallback mode。<br>115s：停止生成並保留 deterministic findings。"))}`),
      foot("resource design target: 16GB MacBook Pro local workflow"),
    ].join(""),
  },
  {
    file: "09-traceability.html",
    label: "可追溯",
    name: "可追溯性",
    content: [
      grid(),
      title("TRACEABILITY", "每個報告欄位都能接回來源", "Trace——把原始工具輸出、正規化 schema、RAG chunks、prompt、LLM output 與最終報告建立查詢鏈。"),
      panel(72, 230, 285, 165, div("code", "position:absolute;left:18pt;top:16pt;width:245pt;height:125pt;", p("finding_id<br>  → slither_raw<br>  → normalized_schema<br>  → rag_chunk_ids<br>  → packed_prompt<br>  → llm_raw_output<br>  → report_field", "mono"))),
      panel(480, 220, 310, 55, `${h(3, "analysis_trace")}<p>contract_id、model_version、dataset_version、final_status。</p>`),
      panel(480, 300, 310, 55, `${h(3, "trace_findings")}<p>per-finding rag_mode、耗時、chunks_used。</p>`),
      panel(480, 380, 310, 55, `${h(3, "trace_lookup")}<p>CLI 查詢單一 finding 的證據鏈。</p>`),
      foot("trace database: reports-*/analysis_trace.sqlite"),
    ].join(""),
  },
  {
    file: "10-case-study.html",
    label: "案例",
    name: "案例研究",
    content: [
      grid(),
      title("CASE STUDY", "VulnerableVault reentrancy 被正規化成 High finding", "實例顯示產品能從測試合約定位漏洞、附上位置、風險敘述與修復方向。"),
      panel(62, 205, 410, 220, div("code", "position:absolute;left:18pt;top:18pt;width:365pt;height:178pt;", p("function withdraw() external {<br>  uint256 amount = balances[msg.sender];<br>  (bool success,) = msg.sender.call{value: amount}(\"\");<br>  require(success, \"transfer failed\");<br>  balances[msg.sender] = 0;<br>}", "mono"))),
      row(535, 220, 330, "detector", "reentrancy-eth"),
      row(535, 282, 330, "location", "tests/contracts/VulnerableVault.sol:11-16"),
      row(535, 344, 330, "fix", "checks-effects-interactions + nonReentrant"),
      foot("case finding: external call precedes balance reset"),
    ].join(""),
  },
  {
    file: "11-validation.html",
    label: "驗收",
    name: "驗收儀表板",
    content: [
      grid(),
      title("VALIDATION DASHBOARD", "自動化測試覆蓋核心產品路徑", "驗收管線包含單元測試、靜態串接、RAG recall、AI judge 與端到端資源觀測。"),
      metric(68, 220, "10 passed", "pytest full regression"),
      metric(278, 220, "All passed", "ruff check", "var(--blue)"),
      metric(505, 220, "2 passed", "E2E tests", "var(--green)"),
      metric(715, 220, "54,083,584", "max RSS bytes", "var(--amber)"),
      panel(68, 370, 795, 52, div("code", "position:absolute;left:18pt;top:15pt;width:750pt;height:22pt;", p("uv run pytest · uv run ruff check . · uv run python eval/run_eval.py · uv run python eval/run_judge.py", "mono"))),
      foot("judge API key not set; local-rule-judge path produced average_judge_score = 5.0"),
    ].join(""),
  },
  {
    file: "12-risk-roadmap.html",
    label: "風險/路線",
    name: "風險與路線圖",
    content: [
      grid(),
      title("RISKS + ROADMAP", "下一版補專案支援與外部評測", "v0.8 已形成產品骨架；v0.9 應提升資料規模、專案相容性與評測可信度。"),
      panel(60, 215, 235, 160, `${h(3, "v0.8 已完成")}<p>CLI、Slither、FindingSchema、RAG fixture、MLX-ready runtime、trace、CI workflow。</p>`),
      panel(360, 215, 235, 160, `${h(3, "v0.9 優先")}<p>多檔 import resolution、Foundry/Hardhat 專案、Mythril 補充、外部 judge API。</p>`),
      panel(660, 215, 235, 160, `${h(3, "v1.0 門檻")}<p>真實公開審計報告 corpus、dense retrieval、使用者上傳流程、報告審核 UI。</p>`),
      foot("roadmap principle: expand project compatibility before adding more generation features"),
    ].join(""),
  },
];

await writeFile(path.join(sharedDir, "tokens.css"), css);
for (const spec of slides) {
  await writeFile(path.join(slidesDir, spec.file), slideShell(spec.name, spec.content));
}

const index = `<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="UTF-8">
<title>智能合約安全分析助理 · 產品報告</title>
<script>
window.DECK_WIDTH = 1280;
window.DECK_HEIGHT = 720;
window.DECK_MANIFEST = ${JSON.stringify(slides.map(({ file, label }) => ({ file: `slides/${file}`, label })), null, 2)};
</script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width:100%; height:100%; overflow:hidden; background:#111417; font-family:-apple-system, "PingFang TC", sans-serif; }
#stage { position:fixed; top:0; left:0; width:1280px; height:720px; transform-origin:top left; background:#F8F7F1; box-shadow:0 20px 70px rgba(0,0,0,.42); }
iframe { width:100%; height:100%; border:0; display:block; background:#F8F7F1; }
.counter { position:fixed; right:18px; bottom:18px; z-index:10; color:#F8F7F1; background:rgba(17,42,70,.82); border-radius:999px; padding:7px 12px; font-size:12px; }
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
console.log(`generated ${slides.length} product report slides`);
