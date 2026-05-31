# Third-Party Notices

This project uses and/or integrates with third-party open-source tools.
Unless explicitly stated, these tools are not bundled in this repository.
They must be installed separately by the operator and remain governed by their own licenses.

The SCSA MIT license covers this repository's orchestration, normalization,
reporting, trace, UI, and evaluation code. It does not relicense external
detectors, fuzzers, symbolic execution engines, build tools, or their outputs.

## Dependency License Inventory

Python and npm package dependencies are tracked separately from the external
security-tool table below. Their licenses are covered by generated SBOM and
license inventory artifacts such as `reports/sbom/python.cdx.json`,
`reports/sbom/frontend.cdx.json`, `reports/licenses/python-licenses.txt`, and
`reports/licenses/npm-tree.json`; this notice table is only the human-readable
summary for analyzer, fuzzer, symbolic-testing, and build-tool integrations.

## External Security Tools

### Slither

- Role in SCSA: primary deterministic static-analysis signal.
- Source URL: https://github.com/crytic/slither
- License: AGPL-3.0.
- Bundled in this repository: false.
- Invocation method: CLI / Python package, depending on installation mode.
- Output consumed by SCSA: detector findings, source ranges, severity, raw analyzer evidence.
- Notes: SCSA does not claim ownership of Slither detectors.

### Aderyn

- Role in SCSA: optional static-analysis signal and SARIF/JSON/Markdown artifact source.
- Source URL: https://github.com/Cyfrin/aderyn
- License: GPL-3.0.
- Bundled in this repository: false.
- Invocation method: external CLI.
- Output consumed by SCSA: static findings, SARIF artifact path, optional report summary.
- Notes: Aderyn SARIF remains an external artifact; SCSA stores the path and normalized signal.

### Echidna

- Role in SCSA: optional property-based fuzzing signal.
- Source URL: https://github.com/crytic/echidna
- License: AGPL-3.0.
- Bundled in this repository: false.
- Invocation method: external CLI.
- Output consumed by SCSA: invariant failures, counterexample signal, run metadata.
- Notes: SCSA treats Echidna failures as evidence requiring human review.

### Medusa

- Role in SCSA: optional coverage-guided fuzzing signal.
- Source URL: https://github.com/crytic/medusa
- License: AGPL-3.0.
- Bundled in this repository: false.
- Invocation method: external CLI.
- Output consumed by SCSA: fuzzer failures, campaign metadata, optional trace evidence.
- Notes: SCSA records Medusa output as external evidence, not as an SCSA-native fuzzer.

### Mythril

- Role in SCSA: optional symbolic-execution signal.
- Source URL: https://github.com/ConsenSysDiligence/mythril
- License: MIT.
- Bundled in this repository: false.
- Invocation method: external CLI.
- Output consumed by SCSA: symbolic issues, SWC references, trace context.
- Notes: Mythril issue paths are normalized into SCSA findings when present.

### Halmos

- Role in SCSA: optional Foundry-oriented symbolic-testing signal.
- Source URL: https://github.com/a16z/halmos
- License: AGPL-3.0.
- Bundled in this repository: false.
- Invocation method: external CLI in trusted Foundry mode.
- Output consumed by SCSA: proof failure, assertion failure, test target metadata.
- Notes: Halmos is disabled for untrusted imported sources.

## External Build Tools

### Foundry

- Role in SCSA: optional native build preflight and trusted Foundry project support.
- Source URL: https://github.com/foundry-rs/foundry
- License: Apache-2.0 OR MIT.
- Bundled in this repository: false.
- Invocation method: external CLI, primarily `forge build`.
- Output consumed by SCSA: build success/failure status and project build context before Slither.
- Notes: Native build scripts only run when `native_build_policy=trusted`.

### Hardhat

- Role in SCSA: optional native build preflight and trusted Hardhat project support.
- Source URL: https://github.com/NomicFoundation/hardhat
- License: MIT for the npm `hardhat` package; verify upstream package license before bundling or redistribution.
- Bundled in this repository: false.
- Invocation method: external CLI, local package binary, or `npx --no-install hardhat compile`.
- Output consumed by SCSA: build success/failure status and project build context before Slither.
- Notes: Native build scripts only run when `native_build_policy=trusted`.
