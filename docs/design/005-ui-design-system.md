# UI Design System

更新日期：2026-05-31。

## 產品定位

SCSA 前端是本地優先的智能合約安全審計工作台。產品氣質是 evidence-first security console：高資訊密度、低裝飾、可回溯，服務對象是智能合約安全工程師、Protocol 開發者、審計 reviewer 與 CI/benchmark 維護者。

核心場景：匯入 source、選擇 Slither 與 optional external tools、追蹤 analysis job、triage findings、比對 remediation diff、查 trace evidence、完成人工 review、輸出 JSON/Markdown/SARIF artifact。

## 視覺規範

| 類別 | 規範 | 適用場景 | 不要怎麼用 |
|---|---|---|---|
| 原則 | Evidence first：漏洞、trace、tool output 優先於裝飾 | Finding card、TracePanel、External tools | 不用 hero、插畫或行銷式卡片 |
| 原則 | Quiet cockpit：高密度但用線條、間距與小標題分組 | 三欄工作台、review 面板 | 不把每個小資訊都包成厚重卡片 |
| 原則 | Progressive disclosure：進階工具逐步展開 | Aderyn、Echidna、Medusa、Halmos | 不一次顯示所有低頻參數 |
| 色彩 | Neutral first：canvas `#f1f5f9`、panel `#f8faf9`、surface `#ffffff` | 背景、左右 rail、finding list | 不用紫藍漸層、霓虹 glow、純黑 |
| 色彩 | Accent 只用 teal `#0f766e` | focus、selected finding、primary affordance | 不用 teal 表示 success |
| 色彩 | 狀態色固定：red/high risk、amber/partial、green/pass、blue/running | badge、alert、tool status | 不只靠顏色傳達狀態 |
| 字體 | Sans 用 Geist fallback，Mono 用 JetBrains Mono fallback | UI、表單、報告、數字 | 不新增 serif 或裝飾字體 |
| 字體 | 12 label、14 body、16 section title、20 page title | 全站文字階層 | 不用 landing hero 級大字 |
| 間距 | 4px base，常用 8/12/16/20/24 | form、card、section | 不用任意像素間距 |
| Layout | Desktop：left 320、right 360、center fluid；mobile 單欄 | Workbench | 不在手機保留水平 scroll |
| 圓角 | chip/button/input 6px，tool/finding card 8px | 互動元件 | 不用大 pill 當主要語言 |
| 邊框 | 1px border 為主，陰影只給浮層 | panels、cards、dropdown | 不給每張卡片加 shadow |
| 元件 | Button 分 primary/secondary/icon/destructive | submit、export、review save | 不複製 inline button class |
| 元件 | Field 統一 label/helper/error | settings、API token、tool options | 不只用 placeholder 當 label |
| 元件 | ToolSelector 顯示工具能力與 trust requirement | external tools | 不把工具塞成單一 select |
| 狀態 | Loading 用 skeleton 或 inline pending row | route loading、diff lazy load | 不只用 spinner 或裸文字 |
| 狀態 | Error 靠近失敗操作，保留 HTTP/message | import、submit、review save | 不只在頁頂顯示籠統錯誤 |
| Icons | 只用 Lucide，16px controls、20px semantic status | buttons、tool rows、status cards | 不使用 emoji 或混用 icon set |
| 文案 | 精確、可操作、低情緒 | alerts、helper、empty state | 不用行銷語 |
| 紅線 | LLM 只做解釋，不做漏洞事實來源 | AI explanation、fix suggestion | 不暗示 AI 已完成正式審計 |
| 紅線 | 未信任來源不可啟用 Halmos trusted flow | imported source、disabled policy | 不提供繞過 native build policy 的 UI |

## Tokens

```css
:root {
  --color-canvas: #f1f5f9;
  --color-panel: #f8faf9;
  --color-surface: #ffffff;
  --color-surface-muted: #f8fafc;
  --color-border: #d9e3dd;
  --color-border-subtle: #e2e8f0;
  --color-text-strong: #0f172a;
  --color-text: #334155;
  --color-text-muted: #64748b;
  --color-text-inverse: #ffffff;
  --color-accent: #0f766e;
  --color-accent-hover: #115e59;
  --color-running: #2563eb;
  --color-danger: #b91c1c;
  --color-warning: #b45309;
  --color-success: #15803d;
  --font-sans: Geist, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --font-mono: "JetBrains Mono", SFMono-Regular, Consolas, "Liberation Mono", monospace;
  --radius-xs: 4px;
  --radius-sm: 6px;
  --radius-md: 8px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 20px;
  --space-6: 24px;
  --shadow-floating: 0 16px 40px -24px rgba(15, 23, 42, 0.35);
  --ring-focus: 0 0 0 2px rgba(15, 118, 110, 0.35);
}
```

## UI Migration Notes

- `Button`、`Field`、`PanelSection`、`MetricGroup` 與 `ToolSelector` 是後續 UI 擴充的預設入口。
- `echidnaEnabled` legacy setting 會 migration 成 `externalTools=["echidna"]`；新 UI 使用 `externalTools` 多選。
- `Halmos` 只在 `nativeBuildPolicy="trusted"` 時可選；`disabled` 模式下 UI disabled，HTTP API 也會拒絕。
- 右欄 external tool cards 會顯示 `artifact_paths`，Aderyn SARIF 不塞進主 report JSON，只以 artifact path 呈現。

