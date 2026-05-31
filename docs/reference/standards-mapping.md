# Standards Mapping

Updated: 2026-06-01

SCSA maps normalized finding types to public smart-contract security standards
so JSON and Markdown reports can show reviewer-facing context beyond legacy
SWC IDs.

Machine-readable mapping lives in `standards_mapping.yml`.

## Mapping Policy

- Mapping is deterministic and based on `vulnerability_type`.
- Finding-specific `reference` values remain in the report for backward compatibility.
- If no mapping exists, SCSA emits `standard_refs: []`.
- SCSA does not invent a standard reference from LLM text.
- Every high-severity normalized finding type must map to at least one OWASP or SWC reference.
- Mapping rows intentionally avoid detector-specific SWC overclaiming; narrow SWC references stay in the finding's analyzer-provided `reference` field unless the normalized type is specific enough.

## Current Coverage

| Internal type | Primary refs |
|---|---|
| `reentrancy` | SC08:2026, SCWE-046, SCSVS-CODE, SWC-107 |
| `unchecked_external_call` | SC06:2026, SCWE-048, SCSVS-CODE, SWC-104 |
| `access_control` | SC01:2026, SCWE-016, SCSVS-AUTH |
| `privilege_escalation` | SC01:2026, SCWE-017, SCSVS-AUTH |
| `upgrade_risk` | SC10:2026, SCWE-005, SCSVS-ARCH |
| `dangerous_delegatecall` | SC10:2026, SCWE-035, SCSVS-COMM, SWC-112 |
| `array_length_manipulation` | SC02:2026, SCSVS-GOV |
| `price_manipulation` | SC03:2026, SCSVS-ORACLE, SCSVS-GOV |
| `oracle` | SC03:2026, SCSVS-ORACLE |
| `invariant_violation` | SC02:2026, SCSVS-GOV |
| `formal_property_violation` | SC02:2026, SCSVS-GOV |

## Sources

- OWASP Smart Contract Security checklist and 2026 Top 10: https://scs.owasp.org/checklists/interactive/
- OWASP SCSVS project: https://owasp.org/www-project-smart-contract-security-verification-standard/
