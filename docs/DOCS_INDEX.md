# Docs Index

Generated at: 2026-06-01

| Category | # | Status | Name | Description | Last Modified | Path |
|---|---|---|---|---|---|---|
| design | 001 | current | 專案架構書 | 描述 Solidity 安全初篩 MVP 的模組邊界、資料流、儲存與取捨。 | 2026-06-01 | `docs/design/001-project-architecture.md` |
| design | 005 | current | UI Design System | 定義 evidence-first security console 的產品氣質、視覺規範、design tokens、ToolSelector 與 UI migration notes。 | 2026-05-31 | `docs/design/005-ui-design-system.md` |
| design | 006 | current | Distribution Metrics Automation | 定義 source-backed adoption metrics updater、GitHub Actions PR workflow、official public sources 與 no-client-telemetry boundary。 | 2026-06-17 | `docs/design/006-telemetry-and-metrics-automation.md` |
| guides | 001 | current | 使用說明書 | 說明安裝、分析、API 加固、External tools、GitHub Actions、trace 查詢、MLX probe、Web UI 與輸出檔案。 | 2026-06-01 | `docs/guides/001-usage-manual.md` |
| templates | 001 | current | SCSA PR Triage GitHub Action | 提供外部 Solidity maintainer 可 copy-paste 的 manual GitHub Actions workflow，預設 `--native-build-policy disabled` 並要求 owned/maintained/authorized target。 | 2026-06-01 | `docs/templates/scsa-pr-triage.yml` |
| readme | 001 | current | Main README | 面向 GitHub 使用者的 SCSA 專屬產品入口，說明 evidence workbench 定位、安裝、Quick Start、Web Workbench、CLI、falsification pack、輸出契約、安全邊界與驗證。 | 2026-07-07 | `README.md` |
| adoption | 001 | current | Codex for OSS Evidence | 記錄 Codex for OSS application evidence、maintainer workflow、case studies、security boundary、benchmark/CI evidence 與 adoption metrics placeholder。 | 2026-06-01 | `docs/adoption/codex-for-oss-evidence.md` |
| adoption | 002 | current | Tester Onboarding | 說明外部 tester 的授權規則、fixture 測試、authorized repo 測試、回饋欄位與禁止提交的敏感資料。 | 2026-06-01 | `docs/adoption/tester-onboarding.md` |
| adoption | 003 | current | Public Triage Protocol | 說明 public triage case 的 authorization link、allowed/disallowed targets、sensitive material handling、sanitization 與 publication checklist。 | 2026-06-01 | `docs/adoption/public-triage-protocol.md` |
| adoption | 004 | current | Public Triage Cases | 記錄 authorized public triage case log；目前保持空白，不把本機 fixture case 誤算為外部 adoption。 | 2026-06-01 | `docs/adoption/public-triage-cases.md` |
| adoption | 005 | current | Adoption Metrics | 記錄 Codex for OSS application 的 stars、forks、external testers、public triage cases、feedback issues、testimonials、downloads、PyPI package publication 與 external OSS adoption 目標與目前來源。 | 2026-06-02 | `docs/adoption/metrics.md` |
| adoption | 006 | current | Tester Testimonials | 記錄 tester testimonial 的引用規則、80-word quote 限制、授權 evidence link 要求與空白 entry template；目前沒有已授權 testimonial。 | 2026-06-01 | `docs/adoption/testimonials.md` |
| adoption | 007 | current | Feedback Processing | 說明 tester feedback 如何經 intake、classification、SLA、PR、release notes 與 metrics update 轉成可驗證維護證據。 | 2026-06-01 | `docs/adoption/feedback-processing.md` |
| adoption | 008 | current | Outreach Kit | 提供 Solidity OSS maintainer、audit learner、Web3 社群、GitHub issue 與 tester follow-up 的安全 outreach 模板，要求 authorized-use boundary 與 public feedback issue。 | 2026-06-01 | `docs/adoption/outreach-kit.md` |
| adoption | 009 | current | External OSS Adoptions | 記錄 public、verifiable external OSS adoption；目前保持空白，不把 stars、forks、downloads、fixtures、local validation 或 one-off feedback 誤算為 external adoption。 | 2026-06-01 | `docs/adoption/external-adoptions.md` |
| adoption | 010 | current | Codex for OSS Application Package | 提供 Codex for OSS 申請用 repository、maintainer role、current evidence snapshot、500-character fields、public evidence links 與 do-not-submit items。 | 2026-06-02 | `docs/adoption/codex-for-oss-application.md` |
| adoption | 011 | current | Evidence Consistency Audit | 記錄 Codex for OSS 提交前的 stars/forks/downloads、README detector count、application adoption claims、API safety claims、confidential-info 與 certification wording 檢查。 | 2026-06-01 | `docs/adoption/evidence-consistency-audit.md` |
| adoption | 012 | current | Codex for OSS Adoption Evidence Plan | 定義 2-4 週 adoption evidence 補強節奏、weekly PR 規則、public tester/triage/adoption/testimonial counting rules 與 application narrative。 | 2026-06-17 | `docs/adoption/codex-for-oss-adoption-evidence-plan.md` |
| reference | 003 | current | Tool Attribution | 記錄 Slither、Aderyn、Echidna、Medusa、Mythril、Halmos、Foundry 與 Hardhat 的角色、license、bundled 狀態與 SCSA 消費邊界。 | 2026-06-01 | `docs/reference/tool-attribution.md` |
| reference | 004 | current | License Boundary | 說明 SCSA MIT license 與外部工具 license、bundling、native build、artifact 消費邊界。 | 2026-06-01 | `docs/reference/license-boundary.md` |
| reference | 005 | current | Related Work | 說明 SCSA 與外部 analyzer、fuzzer、symbolic tool、RAG/LLM assistance 的定位差異與 non-goals。 | 2026-06-01 | `docs/reference/related-work.md` |
| reference | 006 | current | Standards Mapping | 記錄 internal finding type 到 OWASP Smart Contract Top 10、SCWE、SCSVS 與 SWC 的 deterministic mapping policy。 | 2026-06-01 | `docs/reference/standards-mapping.md` |
| reference | 008 | current | Phase 3 Advanced Evidence | 記錄 sandbox-only exploit validation、fuzz seed suggestions、formal property drafts、DeFi profit signal 與 EVMbench adapter 邊界。 | 2026-06-01 | `docs/reference/phase3-advanced-evidence.md` |
| reference | 000 | current | Knowledge Graph | 描述 source import、Slither、external tools、RAG、report、trace、review 與 CI 之間的能力與證據關係。 | 2026-05-31 | `docs/knowledge-graph.md` |
| reference | 001 | current | 驗證程序日誌 | 記錄 2026-05-24 剩餘補強與 2026-05-17 release cleanup 驗證命令、結果、產物與剩餘限制。 | 2026-05-24 | `docs/reference/001-validation-procedure-log.md` |
| reference | 002 | current | Public Benchmark Leaderboard | 記錄 HF Slither50、paired variants、public project build preflight 的 gate、summary、confusion matrix、precision、recall、F1 與逐案結果。 | 2026-06-01 | `docs/reference/002-public-benchmark-leaderboard.md` |
| reference | 007 | current | Benchmark Reproducibility | 說明 HF Slither50 v2、paired variants、RAG groundedness 的 dataset、mapped detector scope、commands、metrics、gates、limitations 與 last verified run。 | 2026-06-01 | `docs/reference/benchmark-reproducibility.md` |
| review | 001 | current | Review Checklist | 記錄 API boundary、native build policy、0G proof、benchmark metrics、CI、project input、report 與 judge 審查門檻。 | 2026-06-01 | `docs/review_checklist.md` |
| archive | 001 | archived | v0.1.0 tester feedback guide | v0.1.0 feedback instructions retained for historical release context. | 2026-06-01 | `docs/archive/community/001-v0.1.0-tester-feedback.md` |
| archive | 002 | archived | v0.1.0 tester outreach kit | v0.1.0 outreach message templates and evidence rules retained for historical release context. | 2026-06-01 | `docs/archive/community/002-v0.1.0-outreach-kit.md` |
| archive | 003 | archived | v0.1.0 feedback tracker | v0.1.0 tester report and public usage signal tracker retained for historical release context. | 2026-06-01 | `docs/archive/community/003-v0.1.0-feedback-tracker.md` |
| archive | 004 | archived | Design drafts | Archived frontend architecture, 90% adoption optimization, and competitor optimization drafts. | 2026-06-01 | `docs/archive/design/` |
| archive | 005 | archived | 0G hackathon archive | Archived 0G hackathon submission, proof, demo, issue remediation, and HackQuest materials. | 2026-06-01 | `docs/archive/hackathon/` |
| archive | 006 | archived | v0.1.0 release readiness checklist | Historical v0.1.0 release checklist. | 2026-06-01 | `docs/archive/release/001-v0.1.0-checklist.md` |
| archive | 007 | archived | v0.2.0 release readiness checklist | Historical v0.2.0 release checklist. | 2026-06-01 | `docs/archive/release/002-v0.2.0-checklist.md` |
| archive | 008 | archived | v0.2.1 hardening checklist | v0.2.1 published hardening release record and validation checklist. | 2026-06-02 | `docs/archive/release/003-v0.2.1-hardening-checklist.md` |
