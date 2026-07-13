import type { AnalysisReport, TraceFinding } from "../types/report";

export const demoReport: AnalysisReport = {
  report_version: "1.0",
  overall_status: "finding",
  contract_id: "10679f2de6b7",
  review_status: "pending_human_review",
  requires_human_review: true,
  business_logic_review_required: false,
  review_reason: "Slither-based MVP findings still require human security review.",
  security_score: 61.84,
  score_formula_version: "security_score_v2",
  score_factors: {
    base_score: 100,
    total_finding_penalty: 38.16,
    severity_counts: { "1": 0, "2": 1, "3": 1 },
  },
  evidence_graph_summary: {
    finding_count: 2,
    claim_count: 2,
    native_rule_result_count: 10,
    unsupported_security_claims: 0,
  },
  external_tool_results: [
    {
      tool_name: "mythril",
      command: ["myth", "analyze", "tests/contracts/VulnerableVault.sol", "-o", "json"],
      status: "skipped",
      findings_count: 0,
      summary: "mythril not installed; skipped optional external analysis.",
    },
    {
      tool_name: "echidna",
      command: ["echidna", "tests/contracts/VulnerableVault.sol", "--format", "json"],
      status: "skipped",
      findings_count: 0,
      summary: "echidna not installed; skipped optional external analysis.",
    },
  ],
  findings: [
    {
      finding_id: "f_001",
      vulnerability_type: "reentrancy",
      severity: 3,
      location: {
        file: "tests/contracts/VulnerableVault.sol",
        function: "withdraw",
        line_start: 11,
        line_end: 16,
      },
      evidence:
        "External call msg.sender.call{value: amount}() happens before balances[msg.sender] is reset.",
      reference: ["SWC-107"],
      finding_confidence: 0.85,
      explanation_confidence: 0.72,
      explanation:
        "withdraw() sends ETH before clearing the caller balance. A receiving contract can re-enter withdraw() while the recorded balance is still positive.",
      attack_path:
        "1. Attacker deposits ETH. 2. Attacker calls withdraw(). 3. Fallback re-enters before balance reset. 4. Repeated withdrawals drain available ETH.",
      fix_suggestion:
        "Move the balance update before the external call and guard withdraw() with a nonReentrant lock.",
      remediation_code:
        "function withdraw() external nonReentrant {\n  uint256 amount = balances[msg.sender];\n  require(amount > 0, \"No balance\");\n  balances[msg.sender] = 0;\n  (bool success, ) = msg.sender.call{value: amount}(\"\");\n  require(success, \"Transfer failed\");\n}",
      vulnerable_code:
        "11: function withdraw() external {\n12:   uint256 amount = balances[msg.sender];\n13:   (bool success, ) = msg.sender.call{value: amount}(\"\");\n14:   require(success, \"Transfer failed\");\n15:   balances[msg.sender] = 0;\n16: }",
      static_tool_source: "slither",
      detector_name: "reentrancy-eth",
      partial: false,
      local_judge_score: 5,
      external_judge_score: 5,
      prompt_tokens: 680,
      completion_tokens: 300,
      total_tokens: 980,
      review_status: "unreviewed",
      review_note: "",
      standard_refs: [
        {
          standard: "OWASP Smart Contract Top 10",
          id: "SC08:2026",
          label: "Reentrancy",
          confidence: "high",
        },
        {
          standard: "SWC",
          id: "SWC-107",
          label: "Reentrancy",
          confidence: "high",
        },
      ],
      evidence_graph: {
        nodes_path: "analysis_trace.sqlite:evidence_nodes",
        edges_path: "analysis_trace.sqlite:evidence_edges",
        claims_path: "analysis_trace.sqlite:evidence_claims",
        root_finding_node_id: "finding:f_001",
        source_nodes: ["source:tests/contracts/VulnerableVault.sol:11-16"],
        tool_signal_nodes: ["tool_signal:slither:reentrancy-eth:f_001"],
        rag_chunk_nodes: ["rag_chunk:web50_022#12"],
        claim_nodes: ["claim:f_001:001"],
        standard_nodes: ["standard_ref:OWASP:SC08:2026", "standard_ref:SWC:SWC-107"],
        rule_nodes: ["rule_result:scsa.reentrancy.evidence_confirmer.v1:f_001"],
        advanced_nodes: [
          "exploit_validation:f_001:001",
          "seed:f_001:001",
          "property:f_001:001",
          "defi_profit_signal:f_001:001",
        ],
        unsupported_security_claims: 0,
        groundedness_status: "supported",
        rule_results: [
          {
            rule_id: "scsa.reentrancy.evidence_confirmer.v1",
            status: "confirmed_by_evidence",
            confidence_delta: 0.15,
          },
          {
            rule_id: "scsa.multi_tool_consensus_scorer.v1",
            status: "single_tool_signal",
            confidence_delta: 0,
          },
        ],
        claims: [
          {
            claim_id: "claim:f_001:001",
            text: "withdraw sends ETH before clearing the caller balance.",
            groundedness_status: "supported",
            support_node_ids: ["source:tests/contracts/VulnerableVault.sol:11-16"],
          },
        ],
      },
      exploit_validation: {
        validation_id: "exploit_validation:f_001:001",
        status: "not_attempted",
        mode: "sandbox_only",
        poc_artifact_path: null,
        test_framework: null,
        triggered: null,
        profit_delta: null,
        asset_delta: [],
        transaction_sequence: [],
        execution_log_path: null,
        human_review_required: true,
        safety_notes: [
          "PoC validation is disabled by default.",
          "Only local fixtures or authorized targets are allowed.",
        ],
        supported_by: [
          "finding:f_001",
          "source:tests/contracts/VulnerableVault.sol:11-16",
        ],
      },
      fuzz_seed_suggestions: [
        {
          finding_id: "f_001",
          seed_id: "seed:f_001:001",
          target_function: "withdraw",
          preconditions: [
            "attacker has a positive recorded balance",
            "vault has enough local fixture ETH",
          ],
          sequence: [
            { call: "deposit", sender: "attacker", value: "1 ETH" },
            { call: "withdraw", sender: "attacker", value: "0" },
          ],
          expected_signal: "external_call_before_state_update",
          status: "suggestion",
          supported_by: [
            "finding:f_001",
            "source:tests/contracts/VulnerableVault.sol:11-16",
          ],
        },
      ],
      formal_property_suggestions: [
        {
          property_id: "property:f_001:001",
          finding_id: "f_001",
          format: "foundry_invariant",
          status: "draft",
          property_text:
            "function invariant_totalAssetsCoverBalances() public { /* reviewer adapts draft */ }",
          compile_status: "not_checked",
          verification_status: "not_proven",
          supported_by: [
            "finding:f_001",
            "source:tests/contracts/VulnerableVault.sol:11-16",
          ],
          review_notes: "Reviewer must adapt this draft before relying on it.",
        },
      ],
      defi_profit_signal: {
        status: "not_observed",
        asset_flow: [],
        oracle_dependency: null,
        flash_loan_dependency: false,
        profitability_status: "not_assessed",
        supported_by: [],
      },
      falsification_pack: {
        status: "needs_human_review",
        reviewer_goal:
          "Confirm the detector evidence or document counterevidence before changing review status.",
        counterevidence_checks: [
          {
            check_id: "reentrancy_state_update_before_call",
            question:
              "Is every affected balance or accounting state updated before the external call?",
            would_refute_if:
              "All affected state is updated before the external call on every reachable path.",
            evidence_to_collect:
              "Trace the function order around the external call and state writes.",
            status: "not_checked",
          },
          {
            check_id: "reentrancy_guard_effective",
            question:
              "Is an effective nonReentrant guard or equivalent mutex active on the call path?",
            would_refute_if:
              "A reachable guard prevents nested entry into the affected function.",
            evidence_to_collect:
              "Inspect modifiers, inherited guards, and internal function call paths.",
            status: "not_checked",
          },
        ],
        confirmation_requirements: [
          "Show a reachable external call before the relevant state update.",
          "Show that attacker-controlled code can re-enter the affected path.",
        ],
        missing_evidence: ["No positive or negative reentrancy guard evidence is recorded."],
        human_review_required: true,
        supported_by: [
          "detector:reentrancy-eth",
          "static_tool:slither",
          "location:tests/contracts/VulnerableVault.sol:11",
        ],
        limitations: [
          "Generated from detector evidence and local report context.",
          "This pack is not proof that the finding is exploitable or impossible.",
        ],
      },
    },
    {
      finding_id: "f_002",
      vulnerability_type: "access_control",
      severity: 2,
      location: {
        file: "tests/contracts/detectors/PrivilegeOwnerDrain.sol",
        function: "drain",
        line_start: 18,
        line_end: 22,
      },
      evidence: "Privileged asset transfer depends on owner-only control and requires human review.",
      reference: ["CWE-284"],
      finding_confidence: 0.68,
      explanation_confidence: 0.64,
      explanation:
        "The drain path moves contract value through a privileged function. Static analysis can identify the privileged flow, while business authorization intent requires reviewer confirmation.",
      attack_path:
        "1. Owner key or owner assignment is compromised. 2. drain() is called. 3. Contract-held funds move to the attacker-controlled address.",
      fix_suggestion:
        "Constrain privileged transfer scope, add multisig ownership, and emit reviewable operational events.",
      remediation_code:
        "function drain(address payable receiver, uint256 amount) external onlyOwner {\n  require(receiver != address(0), \"receiver\");\n  require(amount <= address(this).balance, \"amount\");\n  receiver.transfer(amount);\n  emit Drain(receiver, amount);\n}",
      vulnerable_code:
        "18: function drain(address payable receiver) external onlyOwner {\n19:   receiver.transfer(address(this).balance);\n20: }",
      static_tool_source: "slither",
      detector_name: "owner-drain",
      partial: false,
      local_judge_score: 4.5,
      external_judge_score: 4.5,
      prompt_tokens: 420,
      completion_tokens: 190,
      total_tokens: 610,
      review_status: "accepted_risk",
      review_note: "Privileged transfer requires business owner confirmation.",
      standard_refs: [
        {
          standard: "OWASP Smart Contract Top 10",
          id: "SC01:2026",
          label: "Access Control",
          confidence: "medium",
        },
      ],
      evidence_graph: {
        nodes_path: "analysis_trace.sqlite:evidence_nodes",
        edges_path: "analysis_trace.sqlite:evidence_edges",
        claims_path: "analysis_trace.sqlite:evidence_claims",
        root_finding_node_id: "finding:f_002",
        source_nodes: ["source:tests/contracts/detectors/PrivilegeOwnerDrain.sol:18-22"],
        tool_signal_nodes: ["tool_signal:slither:owner-drain:f_002"],
        rag_chunk_nodes: ["rag_chunk:web50_036#04"],
        claim_nodes: ["claim:f_002:001"],
        standard_nodes: ["standard_ref:OWASP:SC01:2026"],
        rule_nodes: ["rule_result:scsa.auth_sensitive_state_write.v1:f_002"],
        advanced_nodes: [
          "exploit_validation:f_002:001",
          "seed:f_002:001",
          "property:f_002:001",
          "defi_profit_signal:f_002:001",
        ],
        unsupported_security_claims: 0,
        groundedness_status: "supported",
        rule_results: [
          {
            rule_id: "scsa.auth_sensitive_state_write.v1",
            status: "needs_review",
            confidence_delta: 0.03,
          },
          {
            rule_id: "scsa.multi_tool_consensus_scorer.v1",
            status: "single_tool_signal",
            confidence_delta: 0,
          },
        ],
        claims: [
          {
            claim_id: "claim:f_002:001",
            text: "The drain path moves contract value through a privileged function.",
            groundedness_status: "supported",
            support_node_ids: ["source:tests/contracts/detectors/PrivilegeOwnerDrain.sol:18-22"],
          },
        ],
      },
      exploit_validation: {
        validation_id: "exploit_validation:f_002:001",
        status: "not_attempted",
        mode: "sandbox_only",
        poc_artifact_path: null,
        test_framework: null,
        triggered: null,
        profit_delta: null,
        asset_delta: [],
        transaction_sequence: [],
        execution_log_path: null,
        human_review_required: true,
        safety_notes: [
          "PoC validation is disabled by default.",
          "Only local fixtures or authorized targets are allowed.",
        ],
        supported_by: [
          "finding:f_002",
          "source:tests/contracts/detectors/PrivilegeOwnerDrain.sol:18-22",
        ],
      },
      fuzz_seed_suggestions: [
        {
          finding_id: "f_002",
          seed_id: "seed:f_002:001",
          target_function: "drain",
          preconditions: [
            "exercise privileged path with authorized and unauthorized senders",
          ],
          sequence: [
            { call: "drain", sender: "owner", value: "0" },
            { call: "drain", sender: "attacker", value: "0" },
          ],
          expected_signal: "privileged_state_or_asset_flow_diff",
          status: "suggestion",
          supported_by: [
            "finding:f_002",
            "source:tests/contracts/detectors/PrivilegeOwnerDrain.sol:18-22",
          ],
        },
      ],
      formal_property_suggestions: [
        {
          property_id: "property:f_002:001",
          finding_id: "f_002",
          format: "foundry_invariant",
          status: "draft",
          property_text:
            "function invariant_privilegedCallsRequireAuthorizedActor() public { /* reviewer adapts draft */ }",
          compile_status: "not_checked",
          verification_status: "not_proven",
          supported_by: [
            "finding:f_002",
            "source:tests/contracts/detectors/PrivilegeOwnerDrain.sol:18-22",
          ],
          review_notes: "Reviewer must adapt this draft before relying on it.",
        },
      ],
      defi_profit_signal: {
        status: "not_observed",
        asset_flow: [],
        oracle_dependency: null,
        flash_loan_dependency: false,
        profitability_status: "not_assessed",
        supported_by: [],
      },
      falsification_pack: {
        status: "needs_human_review",
        reviewer_goal:
          "Confirm the detector evidence or document counterevidence before changing review status.",
        counterevidence_checks: [
          {
            check_id: "access_control_authorization_boundary",
            question:
              "Is the affected operation protected by owner, role, or capability checks?",
            would_refute_if:
              "All reachable callers must pass an intended authorization boundary.",
            evidence_to_collect:
              "Review modifiers, internal guards, and inherited access-control logic.",
            status: "not_checked",
          },
          {
            check_id: "access_control_public_intent",
            question: "Is the operation intentionally public and safe for any caller?",
            would_refute_if:
              "The operation is designed to be permissionless and cannot move privileged state.",
            evidence_to_collect:
              "Compare code behavior with the protocol's documented permission model.",
            status: "not_checked",
          },
        ],
        confirmation_requirements: [
          "Show the intended authorization boundary for the affected operation.",
          "Show an unauthorized caller can reach the operation.",
        ],
        missing_evidence: ["No obvious missing evidence was detected by deterministic checks."],
        human_review_required: true,
        supported_by: [
          "detector:owner-drain",
          "static_tool:slither",
          "location:tests/contracts/detectors/PrivilegeOwnerDrain.sol:18",
        ],
        limitations: [
          "Generated from detector evidence and local report context.",
          "This pack is not proof that the finding is exploitable or impossible.",
        ],
      },
    },
  ],
  analysis_metadata: {
    dataset_version: "dataset_v1.0",
    model_version: "mlx-8b-4bit",
    solc_version: "0.8.34",
    slither_version: "0.11.5",
    partial_analysis: false,
    analysis_trace_id: "trace_6cb6648b074e",
    context_tokens_used: 41,
    prompt_tokens: 1100,
    completion_tokens: 490,
    total_tokens: 1590,
    local_average_judge_score: 4.75,
    external_average_judge_score: 4.75,
    rag_mode: "fallback",
    total_duration_ms: 1222,
    input_kind: "single_file",
    project_type: "single_file",
    entry_path: "tests/contracts/VulnerableVault.sol",
    project_root: "",
    source_files_count: 1,
    errors: ["Using system solc 0.8.34 for pragma-compatible 0.8.19."],
  },
};

export const demoTrace: TraceFinding[] = demoReport.findings.map((finding, index) => ({
  trace_id: demoReport.analysis_metadata.analysis_trace_id,
  finding_id: finding.finding_id,
  detector_name: finding.detector_name,
  rag_mode: demoReport.analysis_metadata.rag_mode,
  retrieval_duration_ms: 18 + index * 4,
  llm_duration_ms: 120 + index * 25,
  chunks_used: 3,
  slither_raw: JSON.stringify({ check: finding.detector_name, impact: finding.severity }, null, 2),
  normalized_finding: JSON.stringify(finding, null, 2),
  rag_chunk_ids: JSON.stringify(["web50_022#12", "web50_036#04", "dataset_v1.0#08"]),
  packed_prompt: `Finding ${finding.finding_id}: ${finding.evidence}`,
  llm_raw_output: JSON.stringify(
    {
      explanation: finding.explanation,
      attack_path: finding.attack_path,
      fix_suggestion: finding.fix_suggestion,
    },
    null,
    2,
  ),
  schema_valid: true,
  retry_count: 0,
  partial: finding.partial,
  review_status: finding.review_status,
  review_note: finding.review_note,
}));
