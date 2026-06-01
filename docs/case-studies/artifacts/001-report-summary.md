# Case Study 001 Report Summary

Status: sanitized excerpt
Generated from: `reports-case-study-001/3fca00c06c2f.md`
Generated at: 2026-06-01

## Summary

| Field | Value |
|---|---|
| Contract ID | `3fca00c06c2f` |
| Overall status | `finding` |
| Review status | `pending_human_review` |
| Human review required | `true` |
| Business logic review required | `false` |
| Security score | `73.00/100` |
| Report version | `report_v3.0` |
| Dataset version | `dataset_v1.0` |
| Model version | `mlx-8b-4bit` |
| Slither version | `0.11.5` |
| solc version | `0.8.35` |

## Finding

| Field | Value |
|---|---|
| Finding ID | `f_001` |
| Vulnerability | `reentrancy` |
| Severity | `3` |
| Detector | `reentrancy-eth` |
| Location | `tests/contracts/VulnerableVault.sol:11-16` |
| Function | `withdraw` |
| Finding review status | `unreviewed` |
| Finding confidence | `0.90` |
| Explanation confidence | `0.90` |

## Evidence Excerpt

The analyzer identified an external ETH transfer before the caller balance is
set to zero:

```solidity
11:     function withdraw() external {
12:         uint256 amount = balances[msg.sender];
13:         (bool success, ) = msg.sender.call{value: amount}("");
14:         require(success, "transfer failed");
15:         balances[msg.sender] = 0;
16:     }
```

## Standards

- `OWASP Smart Contract Top 10 SC08:2026`
- `SCWE-046`
- `SCSVS-CODE`
- `SWC-107`

## Reviewer Boundary

This is automated triage evidence for an intentionally vulnerable fixture.
Human review remains required before treating any analogous production finding
as final.
