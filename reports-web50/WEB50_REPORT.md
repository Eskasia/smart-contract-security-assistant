# Web50 Audit Corpus Result

- Generated at: `2026-04-30`
- Source repository: https://github.com/Quillhash/QuillAudit_smart_contract_audit_Reports
- Source PDFs: `50`
- Downloaded bytes: `142590106`
- RAG chunks: `798`
- Eligible chunks: `151`

## Corpus Summary

| Type | Count |
|---|---:|
| `access_control` | 29 |
| `array_length_manipulation` | 4 |
| `dangerous_delegatecall` | 23 |
| `reentrancy` | 33 |
| `unchecked_external_call` | 62 |
| `unknown` | 647 |

| Severity | Count |
|---|---:|
| `1` | 440 |
| `2` | 53 |
| `3` | 305 |

## Analysis Result

- Command: `uv run scsa analyze tests/contracts/VulnerableVault.sol --out-dir reports-web50 --dataset-chunks data/web50/chunks.jsonl --rag-mode balanced`
- Status: `finding`
- Contract ID: `10679f2de6b7`
- Trace ID: `trace_09392a23d40e`
- Findings: `1`
- Duration: `1310 ms`

### Finding f_001

- Type: `reentrancy`
- Severity: `3`
- Detector: `reentrancy-eth`
- Location: `tests/contracts/VulnerableVault.sol:11-16`
- Finding confidence: `1.0`
- Explanation confidence: `0.8999999999999999`
- Explanation: Slither reported `reentrancy-eth` at tests/contracts/VulnerableVault.sol line 11, mapped to `reentrancy` with severity 3. Related chunks: web50_046, web50_046, web50_046.

## Trace Summary

| Finding | Detector | RAG mode | Chunks used | Retrieval ms | Partial |
|---|---|---|---:|---:|---|
| `f_001` | `reentrancy-eth` | `balanced` | 3 | 69 | `False` |

## RAG Sources Used By Analysis

| Chunk | Source PDF | Type | Severity |
|---|---|---|---:|
| `web50_046_0016` | `Amplify Smart Contract Audit Report(vesting) - QuillAudits.pdf` | `reentrancy` | 1 |
| `web50_046_0022` | `Amplify Smart Contract Audit Report(vesting) - QuillAudits.pdf` | `reentrancy` | 1 |
| `web50_046_0034` | `Amplify Smart Contract Audit Report(vesting) - QuillAudits.pdf` | `reentrancy` | 1 |

## 50 Source PDFs

| ID | PDF | Bytes |
|---|---|---:|
| `web50_001` | `2D3T Smart Contract Audit Report - Quill Audits.pdf` | 6568169 |
| `web50_002` | `5tars Smart Contract Audit Report - QuillAudits.pdf` | 2086183 |
| `web50_003` | `99Starz Smart Contract Audit Report - QuillAudits.pdf` | 5088059 |
| `web50_004` | `ACYC Token Smart Contracts Audit Report - QuillAudits.pdf` | 5119635 |
| `web50_005` | `AHT Smart Contract Audit report - QuillAudits.pdf` | 1684869 |
| `web50_006` | `AIDUS Smart Contract Audit Report - QuillAudits.pdf` | 2172131 |
| `web50_007` | `AL Mabrook Financials Inc Smart Contracts Audit Report - QuillAudits.pdf` | 4423012 |
| `web50_008` | `AQEX Token Smart Contract Audit Report - QuillAudits.pdf` | 1791744 |
| `web50_009` | `ASVA Smart Contract Audit Report - QuillAudits.pdf` | 2889807 |
| `web50_010` | `ASVA Token Contract Audit Report - QuillAudits.pdf` | 2706218 |
| `web50_011` | `ATM Smart Contract Audit Report- QuillAudits.pdf` | 1572027 |
| `web50_012` | `AVNBridge Smart Contract Audit report - QuillAudits.pdf` | 1567837 |
| `web50_013` | `AVX Smart Contract Audit Report - QuillAudits.pdf` | 2462990 |
| `web50_014` | `AcknoLedger Smart Contract Audit Report - QuillAudits.pdf` | 1845175 |
| `web50_015` | `Acknoledger Smart Contract Audit Report_2 - QuillAudits.pdf` | 2228086 |
| `web50_016` | `Aconomy (StakingYield) Contract Audit Report - QuillAudits.pdf` | 1977361 |
| `web50_017` | `Aconomy Smart Contract Audit Report - QuillAudits.pdf` | 2758624 |
| `web50_018` | `Acria Token Contract Audit Report - QuillAudits.pdf` | 1669266 |
| `web50_019` | `Advon Smart Contract Audit Report - QuillAudits.pdf` | 3118058 |
| `web50_020` | `Agiratech Hyperledger Fabric Audit Report - QuillAudits.pdf` | 2313835 |
| `web50_021` | `AgriUT Smart Contract Audit Report - QuillAudits.pdf` | 1469682 |
| `web50_022` | `Ai Fun Token Contract Audit Report - QuillAudits.pdf` | 1862111 |
| `web50_023` | `AiPepe Smart Contract Audit Report-QuillAudits.pdf` | 3054214 |
| `web50_024` | `AiVoiceAgent Token Contract Audit Report - QuillAudits.pdf` | 6121501 |
| `web50_025` | `AirLyft Smart Contract Audit Report - QuillAudits.pdf` | 1893063 |
| `web50_026` | `Akt.io Smart Contract Audit Report - QuillAudits.pdf` | 1674500 |
| `web50_027` | `Alfcoin Smart Contract Audit Report - QuillAudits.pdf` | 2514053 |
| `web50_028` | `Algovest Audit Report.pdf` | 5936362 |
| `web50_029` | `Alium Finance (MulticallUserExecutable)Contract Audit Report - QuillAudits.pdf` | 1618320 |
| `web50_030` | `Alium Finance Smart Contract Audit Report - QuillAudits.pdf` | 2549554 |
| `web50_031` | `AliumSwap Smart Contract Audit Report - QuillAudits.pdf` | 2396372 |
| `web50_032` | `Alkimi Move Smart Contract Audit report - QuillAudits.pdf` | 1253589 |
| `web50_033` | `Alkimi Pentest Audit Report.pdf` | 2019124 |
| `web50_034` | `Alkimi Solidity Smart Contract Audit report - QuillAudits.pdf` | 1993628 |
| `web50_035` | `Alkimi Token Gen Smart Contract Audit Report - QuillAudits.pdf` | 864336 |
| `web50_036` | `Alkimi Token Smart Contract Audit Report - QuillAudits.pdf` | 1341259 |
| `web50_037` | `Allo Pentest Audit report - QuillAudits .pdf` | 3641366 |
| `web50_038` | `Allo Smart Contract Audit Report - QuillAudits.pdf` | 6379683 |
| `web50_039` | `Almanak Smart Contract Audit report - QuillAudits.pdf` | 2524518 |
| `web50_040` | `Altranium Contract Audit Report - QuillAudits.pdf` | 1796444 |
| `web50_041` | `Alvara Gauge Weight Rewards Smart Contract Audit Report - QuillAudits.pdf` | 1634797 |
| `web50_042` | `Alvara Smart Contracts Audit Report - QuillAudits.pdf` | 6855138 |
| `web50_043` | `Alvara Staking Smart Contract Audit Report - QuillAudits.pdf` | 6309039 |
| `web50_044` | `AlvaraAvax Smart Contract Audit Report - QuillAudits .pdf` | 1799408 |
| `web50_045` | `Amplify Smart Contract Audit Report - QuillAudits.pdf` | 2711975 |
| `web50_046` | `Amplify Smart Contract Audit Report(vesting) - QuillAudits.pdf` | 1448907 |
| `web50_047` | `Amplify Token Smart Contract Audit Report - QuillAudits.pdf` | 2477160 |
| `web50_048` | `Amplify voting Smart Contract Audit Report - QuillAudits.pdf` | 1824811 |
| `web50_049` | `Amplify_Child_Token_Smart_Contract_Audit_Report_QuillAudits.pdf` | 4720670 |
| `web50_050` | `AngelsCreed Token Contract Audit Report - QuillAudits.pdf` | 3861436 |

## Artifacts

- `data/web50/source_manifest.json`
- `data/web50/chunks.jsonl`
- `reports-web50/10679f2de6b7.json`
- `reports-web50/10679f2de6b7.md`
- `reports-web50/analysis_trace.sqlite`
- `reports-web50/web50_result.json`
