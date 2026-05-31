# License Boundary

Updated: 2026-06-01

SCSA is released under the MIT license for code authored in this repository.
That license covers orchestration, adapters, normalization, report generation,
trace storage, local UI code, and evaluation scripts owned by this project.

The external analyzers, fuzzers, symbolic-testing tools, and build tools remain
under their upstream licenses. SCSA does not bundle those tools and does not
relicense their detector engines, fuzzer engines, symbolic execution engines,
or build systems.

## Boundary Rules

- External tools are invoked only when installed by the operator or present in the local project environment.
- AGPL/GPL tools are documented as external, non-bundled tools.
- Python and npm dependency license inventories are generated artifacts under `reports/sbom/` and `reports/licenses/`; they are not fully enumerated in `THIRD_PARTY_NOTICES.md`.
- Tool output is consumed as evidence or artifact paths; SCSA ownership claims apply only to normalization and review workflow code.
- Native Foundry and Hardhat builds can execute project scripts; keep untrusted imports on `native_build_policy=disabled`.
- Before bundling, redistributing, or vendoring any external tool, re-check its upstream license and security posture.

## Current External Tool Classes

| Class | Tools | Bundled | SCSA ownership boundary |
|---|---|---:|---|
| Primary analyzer | Slither | false | Detector output is external; normalization and report workflow are SCSA code. |
| Optional static analyzer | Aderyn | false | JSON/SARIF/Markdown outputs are external evidence artifacts. |
| Optional fuzzers | Echidna, Medusa | false | Failed property and campaign outputs are external evidence signals. |
| Optional symbolic tools | Mythril, Halmos | false | Symbolic issues and proof failures are external evidence signals. |
| Optional build tools | Foundry, Hardhat | false | Build success/failure is preflight context, not SCSA analysis logic. |

Authoritative machine-readable source: `tool_matrix.yml`.
Human-readable notices: `THIRD_PARTY_NOTICES.md`.
