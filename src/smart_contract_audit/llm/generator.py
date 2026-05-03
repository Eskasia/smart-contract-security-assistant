from __future__ import annotations

import json

from smart_contract_audit.llm.mlx_runtime import MLXRuntimeConfig, generate_with_mlx
from smart_contract_audit.llm.prompt_template import pack_finding_prompt
from smart_contract_audit.models import Finding, RagChunk


def generate_finding_details(
    finding: Finding,
    chunks: list[RagChunk],
    config: MLXRuntimeConfig | None = None,
) -> dict[str, str]:
    runtime_config = config or MLXRuntimeConfig()
    prompt = pack_finding_prompt(finding, chunks)
    generated = generate_with_mlx(prompt, runtime_config)
    if generated:
        parsed = _parse_json_object(generated)
        if parsed:
            return {
                "explanation": str(parsed.get("explanation", "")),
                "attack_path": str(parsed.get("attack_path", "")),
                "fix_suggestion": str(parsed.get("fix_suggestion", "")),
                "remediation_code": str(
                    parsed.get("remediation_code") or parsed.get("fixed_code") or ""
                ),
            }

    return _deterministic_details(finding, chunks)


def _parse_json_object(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        parsed = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _deterministic_details(finding: Finding, chunks: list[RagChunk]) -> dict[str, str]:
    location = f"{finding.location.file} line {finding.location.line_start}"
    source_note = _source_note(chunks)
    return {
        "explanation": _explanation_for_type(finding, location, source_note),
        "attack_path": _attack_path_for_type(finding.vulnerability_type),
        "fix_suggestion": _fix_for_type(finding.vulnerability_type),
        "remediation_code": _remediation_code_for_type(finding.vulnerability_type),
    }


def _source_note(chunks: list[RagChunk]) -> str:
    if not chunks:
        return "No matching RAG chunk was available; this explanation uses detector semantics."
    sources = ", ".join(f"{chunk.source_id}:{chunk.section_title}" for chunk in chunks[:3])
    return f"RAG evidence used: {sources}."


def _explanation_for_type(finding: Finding, location: str, source_note: str) -> str:
    explanations = {
        "reentrancy": (
            f"`{finding.detector_name}` at {location} means the function transfers ETH "
            "before the caller balance is reduced. A receiver contract can re-enter the "
            "same function while its recorded balance is still positive, then withdraw "
            f"the same balance more than once. {source_note}"
        ),
        "access_control": (
            f"`{finding.detector_name}` at {location} means a privileged asset or admin "
            f"operation lacks an authorization boundary. {source_note}"
        ),
        "unchecked_external_call": (
            f"`{finding.detector_name}` at {location} means the contract ignores whether "
            f"an external call succeeded, so accounting can continue after failure. {source_note}"
        ),
        "dangerous_delegatecall": (
            f"`{finding.detector_name}` at {location} means code execution can be delegated "
            f"to an unsafe target under the caller contract storage context. {source_note}"
        ),
        "oracle": (
            f"`{finding.detector_name}` at {location} means oracle data is consumed without "
            f"the freshness or confidence checks needed before pricing assets. {source_note}"
        ),
        "price_manipulation": (
            f"`{finding.detector_name}` at {location} means value calculation can rely on "
            f"a manipulable price, timing, or arithmetic path. {source_note}"
        ),
        "privilege_escalation": (
            f"`{finding.detector_name}` at {location} means a caller can reach a privileged "
            f"state transition or asset flow beyond its intended authority. {source_note}"
        ),
        "upgrade_risk": (
            f"`{finding.detector_name}` at {location} means upgrade or initialization logic "
            f"can alter execution authority without a guarded review path. {source_note}"
        ),
    }
    return explanations.get(
        finding.vulnerability_type,
        (
            f"`{finding.detector_name}` at {location} maps to "
            f"`{finding.vulnerability_type}`. {source_note}"
        ),
    )


def _attack_path_for_type(vulnerability_type: str) -> str:
    paths = {
        "reentrancy": (
            "1. Attacker deposits or obtains a positive balance. "
            "2. Attacker calls the vulnerable withdraw function. "
            "3. Receiver fallback re-enters before balance is set to zero. "
            "4. Contract sends funds multiple times from one recorded balance."
        ),
        "access_control": (
            "1. Unauthorized caller invokes the privileged function. "
            "2. Contract executes the state change or transfer. "
            "3. Assets or admin state move outside the intended authority boundary."
        ),
        "upgrade_risk": (
            "1. Unauthorized caller reaches upgrade or initialization logic. "
            "2. Implementation or owner state changes. "
            "3. Future calls execute attacker-controlled behavior."
        ),
    }
    return paths.get(
        vulnerability_type,
        (
            "1. Attacker reaches the affected function. "
            "2. Vulnerable control flow is triggered. "
            "3. Contract state or asset flow changes according to the finding evidence."
        ),
    )


def _fix_for_type(vulnerability_type: str) -> str:
    fixes = {
        "reentrancy": (
            "Apply checks-effects-interactions and add a nonReentrant modifier "
            "around the affected function."
        ),
        "access_control": (
            "Protect the function with an explicit onlyOwner or role-based modifier "
            "and test unauthorized calls."
        ),
        "unchecked_external_call": (
            'Check the returned success boolean with require(success, "call failed") '
            "and handle revert data."
        ),
        "dangerous_delegatecall": (
            "Remove user-controlled delegatecall targets or restrict them through "
            "an allowlist."
        ),
        "array_length_manipulation": (
            "Avoid direct array length manipulation and guard index/length updates "
            "with require checks."
        ),
        "oracle": (
            "Validate oracle freshness, confidence bounds, and fallback behavior before "
            "using the price in asset accounting."
        ),
        "price_manipulation": (
            "Use manipulation-resistant pricing such as TWAP, slippage limits, and "
            "liquidity-aware checks before executing value transfers."
        ),
        "privilege_escalation": (
            "Restrict privileged flows with explicit roles, least-privilege checks, "
            "and tests for unauthorized callers."
        ),
        "upgrade_risk": (
            "Protect upgrade and initialization flows with owner or role checks, "
            "initializer guards, and storage layout tests."
        ),
    }
    return fixes.get(
        vulnerability_type,
        "Apply a minimal code-level guard matching the Slither detector evidence.",
    )


def _remediation_code_for_type(vulnerability_type: str) -> str:
    snippets = {
        "reentrancy": """import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract Vault is ReentrancyGuard {
    mapping(address => uint256) public balances;

    function withdraw() external nonReentrant {
        uint256 amount = balances[msg.sender];
        require(amount > 0, "no balance");

        balances[msg.sender] = 0;

        (bool success,) = payable(msg.sender).call{value: amount}("");
        require(success, "transfer failed");
    }
}""",
        "access_control": """modifier onlyOwner() {
    require(msg.sender == owner, "not owner");
    _;
}

function sweep(address payable to) external onlyOwner {
    require(to != address(0), "zero address");
    to.transfer(address(this).balance);
}""",
        "unchecked_external_call": """(bool success, bytes memory data) = target.call(payload);
require(success, "external call failed");""",
        "upgrade_risk": """function upgradeTo(address newImplementation) external onlyOwner {
    require(newImplementation.code.length > 0, "implementation has no code");
    _upgradeTo(newImplementation);
}""",
        "oracle": """function _validatedPrice() internal view returns (int256 price) {
    (, price,, uint256 updatedAt,) = priceFeed.latestRoundData();
    require(price > 0, "invalid price");
    require(block.timestamp - updatedAt <= maxOracleDelay, "stale price");
}""",
        "price_manipulation": """
uint256 amountOut = router.getAmountOut(amountIn, reserveIn, reserveOut);
require(amountOut >= minAmountOut, "slippage exceeded");""",
        "privilege_escalation": """
function setRole(address account, bytes32 role) external onlyOwner {
    require(account != address(0), "zero address");
    _grantRole(role, account);
}""",
    }
    return snippets.get(vulnerability_type, "")
