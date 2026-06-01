# Evidence Consistency Audit

Status: current pre-application audit
Updated: 2026-06-01

This audit checks public SCSA claims before Codex for OSS submission. It covers
`README.md`, `CHANGELOG.md`, and `docs/adoption/*`.

## Checklist

| Check | Status | Evidence |
|---|---|---|
| Stars/forks/downloads match current public data | Pass | GitHub repo API returned `stargazers_count=0` and `forks_count=0` on 2026-06-01; PyPI JSON returned 404 |
| README detector count matches `config.py` | Pass | `DETECTOR_MAPPING` contains 27 Slither detectors; README mapped detector subset now states 27 |
| Application text does not overclaim adoption | Pass | Application package repeats 0 testers, 0 public triage cases, 0 testimonials, 0 downloads, and 0 external OSS adoptions |
| API safety claims match code | Pass | `ApiConfig` defaults to `api_token=None`, `allow_tokenless_local_demo=False`, `allow_any_input_root=False`, and `native_build_policy="disabled"`; request validation rejects non-JSON write bodies and unsafe CORS/token combinations |
| No confidential info | Pass | Public adoption docs use public repo links and placeholders only |
| No private repo names without permission | Pass | Adoption docs do not log private repo names or private customer identifiers |
| No full-audit or certification claim | Pass | Matching phrases are boundary denials such as "not a full audit" and "not audit certification"; no text claims SCSA provides full audit or certification |

## Metrics snapshot

| Metric | Current | Source |
|---|---:|---|
| GitHub stars | 0 | GitHub repo API, 2026-06-01 |
| GitHub forks | 0 | GitHub repo API, 2026-06-01 |
| Monthly downloads | 0 | PyPI JSON returned 404, 2026-06-01 |
| External testers | 0 | `docs/adoption/metrics.md` |
| Public triage cases | 0 | `docs/adoption/public-triage-cases.md` |
| Testimonials | 0 | `docs/adoption/testimonials.md` |
| External OSS adoptions | 0 | `docs/adoption/external-adoptions.md` |

## Detector scope

`src/smart_contract_audit/config.py::DETECTOR_MAPPING` contains 27 mapped
Slither detectors. README lists the same mapped detector groups and does not
claim complete Slither or complete Solidity vulnerability coverage.

## Claim boundaries

Keep these boundaries for application text and public docs:

- SCSA is automated triage evidence for human review.
- SCSA does not certify contracts as safe to deploy.
- SCSA does not replace a qualified manual audit.
- External adoption remains unclaimed until public evidence is logged.
- Downloads remain 0 until a package-hosted download counter exists.

## Follow-up for G4.2

No claim mismatch required a behavioral fix. The only documentation adjustment
made in this goal was adding the explicit README detector count so it can be
checked against `DETECTOR_MAPPING`.
