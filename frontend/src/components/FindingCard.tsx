import { Clipboard, FileWarning, Save, ShieldCheck } from "lucide-react";
import { lazy, memo, Suspense, useCallback, useEffect, useState } from "react";

import { formatLocation, formatScore, formatTokens } from "../lib/format";
import { patchFindingReview } from "../lib/api";
import { useTranslation, type TranslationKey } from "../lib/i18n";
import { useAnalysisStore, useSettingsStore } from "../store/analysisStore";
import type { Finding, FindingReviewStatus } from "../types/report";
import { CodeBlock } from "./CodeBlock";
import { Metric } from "./Metric";
import { SeverityBadge } from "./StatusBadge";
import { Button } from "./ui/Button";

const LazyDiffViewerPanel = lazy(() =>
  import("./DiffViewerPanel").then((module) => ({ default: module.DiffViewerPanel })),
);

const findingReviewStatuses: FindingReviewStatus[] = [
  "unreviewed",
  "true_positive",
  "false_positive",
  "accepted_risk",
  "fixed",
];

const findingReviewLabelKeys: Record<FindingReviewStatus, TranslationKey> = {
  unreviewed: "unreviewed",
  true_positive: "truePositive",
  false_positive: "falsePositive",
  accepted_risk: "acceptedRisk",
  fixed: "fixed",
};

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

export const FindingCard = memo(function FindingCard({
  finding,
  selected,
  onSelect,
  streamText,
}: {
  finding: Finding;
  selected: boolean;
  onSelect: (findingId: string) => void;
  streamText?: string;
}) {
  const { t } = useTranslation();
  const diffMode = useSettingsStore((state) => state.settings.diffMode);
  const apiToken = useSettingsStore((state) => state.settings.apiToken);
  const updateSettings = useSettingsStore((state) => state.updateSettings);
  const contractId = useAnalysisStore((state) => state.report.contract_id);
  const connectionMode = useAnalysisStore((state) => state.connectionMode);
  const setReport = useAnalysisStore((state) => state.setReport);
  const updateFindingReview = useAnalysisStore((state) => state.updateFindingReview);
  const vulnerableCode = finding.vulnerable_code ?? "";
  const remediationCode = finding.remediation_code ?? "";
  const explanation = streamText || finding.explanation;
  const evidenceGraph = finding.evidence_graph ?? {};
  const standardRefs = finding.standard_refs ?? [];
  const ruleResults = evidenceGraph.rule_results ?? finding.native_rule_results ?? [];
  const claims = evidenceGraph.claims ?? [];
  const exploitValidation = finding.exploit_validation;
  const fuzzSeeds = finding.fuzz_seed_suggestions ?? [];
  const formalProperties = finding.formal_property_suggestions ?? [];
  const defiProfitSignal = finding.defi_profit_signal;
  const [reviewDraft, setReviewDraft] = useState<FindingReviewStatus>(
    finding.review_status ?? "unreviewed",
  );
  const [reviewNote, setReviewNote] = useState(finding.review_note ?? "");
  const [reviewMessage, setReviewMessage] = useState("");

  useEffect(() => {
    setReviewDraft(finding.review_status ?? "unreviewed");
    setReviewNote(finding.review_note ?? "");
    setReviewMessage("");
  }, [finding.finding_id, finding.review_status, finding.review_note]);

  const copyRemediation = useCallback(async () => {
    if (remediationCode) await navigator.clipboard.writeText(remediationCode);
  }, [remediationCode]);

  const saveFindingReview = useCallback(async () => {
    try {
      const response = await patchFindingReview(
        contractId,
        finding.finding_id,
        {
          review_status: reviewDraft,
          review_note: reviewNote,
        },
        apiToken,
      );
      setReport(response.report);
      setReviewMessage(t("saved"));
    } catch (error) {
      if (connectionMode === "demo") {
        updateFindingReview(finding.finding_id, reviewDraft, reviewNote);
        setReviewMessage(t("savedLocally"));
      } else {
        setReviewMessage(t("saveFailed", { message: errorMessage(error) }));
      }
    }
  }, [
    connectionMode,
    contractId,
    finding.finding_id,
    reviewDraft,
    reviewNote,
    apiToken,
    setReport,
    t,
    updateFindingReview,
  ]);

  return (
    <article
      role="article"
      aria-label={finding.finding_id}
      className={`rounded-md border bg-surface p-4 transition ${selected ? "border-audit-teal ring-2 ring-teal-100" : "border-border-subtle"}`}
    >
      <button
        type="button"
        onClick={() => onSelect(finding.finding_id)}
        aria-current={selected ? "true" : undefined}
        aria-pressed={selected}
        className="flex w-full items-start justify-between gap-3 text-left"
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <SeverityBadge severity={finding.severity} />
            <span className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 text-xs font-medium text-slate-700">
              {finding.detector_name}
            </span>
          </div>
          <h2 className="mt-2 text-base font-semibold text-slate-950">
            {finding.vulnerability_type}
          </h2>
          <p className="mt-1 break-words text-sm text-slate-600">
            {formatLocation(finding.location)}
          </p>
        </div>
        {finding.partial ? (
          <FileWarning className="mt-1 h-5 w-5 shrink-0 text-amber-600" aria-label={t("partialFinding")} />
        ) : (
          <ShieldCheck className="mt-1 h-5 w-5 shrink-0 text-emerald-700" aria-label={t("schemaValid")} />
        )}
      </button>

      <div className="mt-4 grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label={t("findingConfidence")} value={finding.finding_confidence.toFixed(2)} />
        <Metric label={t("explanationConfidence")} value={finding.explanation_confidence.toFixed(2)} />
        <Metric label={t("localJudge")} value={formatScore(finding.local_judge_score)} />
        <Metric label={t("externalJudge")} value={formatScore(finding.external_judge_score)} />
      </div>

      <section
        aria-labelledby={`${finding.finding_id}-evidence-graph`}
        className="mt-4 border-t border-slate-200 pt-3"
      >
        <div className="grid gap-3 lg:grid-cols-3">
          <div>
            <h3 id={`${finding.finding_id}-evidence-graph`} className="text-sm font-semibold text-slate-900">
              {t("evidenceGraph")}
            </h3>
            <p className="mt-1 break-words text-xs leading-5 text-slate-600">
              {evidenceGraph.root_finding_node_id ?? finding.finding_id}
            </p>
          </div>
          <Metric
            label={t("groundedness")}
            value={evidenceGraph.groundedness_status ?? "unavailable"}
          />
          <Metric
            label={t("unsupportedClaims")}
            value={evidenceGraph.unsupported_security_claims ?? 0}
          />
        </div>

        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          <EvidenceList
            title={t("toolProvenance")}
            items={evidenceGraph.tool_signal_nodes ?? [finding.static_tool_source]}
          />
          <EvidenceList
            title={t("sourceRange")}
            items={evidenceGraph.source_nodes ?? [formatLocation(finding.location)]}
          />
          <EvidenceList
            title={t("ragSupport")}
            items={evidenceGraph.rag_chunk_nodes ?? []}
          />
          <EvidenceList
            title={t("standards")}
            items={standardRefs.map((ref) => `${ref.standard} ${ref.id} ${ref.label}`)}
          />
        </div>

        {ruleResults.length > 0 ? (
          <div className="mt-3">
            <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("nativeRules")}</h3>
            <ul className="space-y-1 text-xs leading-5 text-slate-700">
              {ruleResults.map((rule) => (
                <li key={rule.rule_id} className="break-words">
                  <span className="font-medium">{rule.rule_id}</span>: {rule.status}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {claims.length > 0 ? (
          <div className="mt-3">
            <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("claimSupport")}</h3>
            <ul className="space-y-1 text-xs leading-5 text-slate-700">
              {claims.map((claim) => (
                <li key={claim.claim_id} className="break-words">
                  <span className="font-medium">{claim.groundedness_status}</span>:{" "}
                  {claim.claim_text ?? claim.text ?? claim.claim_id}
                </li>
              ))}
            </ul>
          </div>
        ) : null}
      </section>

      <section
        aria-labelledby={`${finding.finding_id}-advanced-evidence`}
        className="mt-4 border-t border-slate-200 pt-3"
      >
        <h3 id={`${finding.finding_id}-advanced-evidence`} className="text-sm font-semibold text-slate-900">
          {t("exploitValidation")}
        </h3>
        <div className="mt-3 grid gap-3 md:grid-cols-4">
          <Metric
            label={t("validationStatus")}
            value={exploitValidation?.status ?? "not_attempted"}
          />
          <Metric
            label={t("validationMode")}
            value={exploitValidation?.mode ?? "sandbox_only"}
          />
          <Metric
            label={t("humanReviewRequired")}
            value={String(exploitValidation?.human_review_required ?? true)}
          />
          <Metric
            label={t("defiProfitSignal")}
            value={defiProfitSignal?.profitability_status ?? "not_assessed"}
          />
        </div>
        <div className="mt-3 grid gap-3 lg:grid-cols-2">
          <EvidenceList
            title={t("transactionSequence")}
            items={exploitValidation?.transaction_sequence ?? []}
          />
          <EvidenceList
            title={t("safetyNotes")}
            items={exploitValidation?.safety_notes ?? []}
          />
          <EvidenceList
            title={t("fuzzSeeds")}
            items={fuzzSeeds.map((seed) => `${seed.seed_id} -> ${seed.target_function}`)}
          />
          <EvidenceList
            title={t("formalProperties")}
            items={formalProperties.map(
              (property) =>
                `${property.property_id}: ${property.status}/${property.verification_status}`,
            )}
          />
          <EvidenceList
            title={t("assetDelta")}
            items={(defiProfitSignal?.asset_flow ?? []).map(
              (flow) => `${flow.asset ?? "asset"} ${flow.from ?? "from"} -> ${flow.to ?? "to"} ${flow.delta ?? ""}`,
            )}
          />
          <EvidenceList
            title={t("claimSupport")}
            items={Array.from(
              new Set([
                ...(exploitValidation?.supported_by ?? []),
                ...fuzzSeeds.flatMap((seed) => seed.supported_by),
                ...formalProperties.flatMap((property) => property.supported_by),
              ]),
            )}
          />
        </div>
      </section>

      <div className="mt-4 grid gap-3 border-t border-slate-200 pt-3 md:grid-cols-[minmax(170px,220px)_minmax(0,1fr)_auto]">
        <label className="block">
          <span className="text-xs font-medium text-slate-600">
            {t("findingReviewStatus")}
          </span>
          <select
            value={reviewDraft}
            onChange={(event) =>
              setReviewDraft(event.currentTarget.value as FindingReviewStatus)
            }
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          >
            {findingReviewStatuses.map((status) => (
              <option key={status} value={status}>
                {t(findingReviewLabelKeys[status])}
              </option>
            ))}
          </select>
        </label>
        <label className="block min-w-0">
          <span className="text-xs font-medium text-slate-600">{t("reviewNote")}</span>
          <input
            value={reviewNote}
            maxLength={2000}
            onChange={(event) => setReviewNote(event.currentTarget.value)}
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-audit-teal"
          />
        </label>
        <Button
          type="button"
          onClick={saveFindingReview}
          className="self-end"
          aria-label={t("saveFindingReview")}
        >
          <Save className="h-4 w-4" aria-hidden="true" />
          <span>{t("save")}</span>
        </Button>
        <p className="min-h-5 text-xs text-slate-600 md:col-span-3" role="status">
          {reviewMessage}
        </p>
      </div>

      <div className="mt-4 space-y-4">
        <section aria-labelledby={`${finding.finding_id}-code`}>
          <h3 id={`${finding.finding_id}-code`} className="mb-2 text-sm font-semibold text-slate-900">
            {t("vulnerableCode")}
          </h3>
          <CodeBlock code={vulnerableCode} />
        </section>

        <section aria-labelledby={`${finding.finding_id}-explanation`}>
          <h3 id={`${finding.finding_id}-explanation`} className="mb-2 text-sm font-semibold text-slate-900">
            {t("aiExplanation")}
          </h3>
          <p className="text-sm leading-6 text-slate-700">{explanation || t("deterministicOnly")}</p>
        </section>

        <div className="grid gap-4 lg:grid-cols-2">
          <section>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("attackPath")}</h3>
            <p className="text-sm leading-6 text-slate-700">{finding.attack_path || t("notGenerated")}</p>
          </section>
          <section>
            <h3 className="mb-2 text-sm font-semibold text-slate-900">{t("fixSuggestion")}</h3>
            <p className="text-sm leading-6 text-slate-700">{finding.fix_suggestion || t("notGenerated")}</p>
          </section>
        </div>

        <section aria-labelledby={`${finding.finding_id}-diff`}>
          <div className="mb-2 flex items-center justify-between gap-2">
            <h3 id={`${finding.finding_id}-diff`} className="text-sm font-semibold text-slate-900">
              {t("remediationDiff")}
            </h3>
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-xs text-slate-600">
                <input
                  type="checkbox"
                  checked={diffMode === "split"}
                  onChange={(event) =>
                    updateSettings({ diffMode: event.currentTarget.checked ? "split" : "inline" })
                  }
                  className="h-4 w-4 rounded border-slate-300 text-audit-teal focus:ring-audit-teal"
                />
                {t("split")}
              </label>
              <Button
                type="button"
                onClick={copyRemediation}
                size="icon"
                aria-label={t("copyRemediationCode")}
              >
                <Clipboard className="h-4 w-4" aria-hidden="true" />
              </Button>
            </div>
          </div>
          <Suspense
            fallback={
              <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600">
                {t("loadingDiff")}
              </div>
            }
          >
            <LazyDiffViewerPanel
              oldValue={vulnerableCode}
              newValue={remediationCode}
              splitView={diffMode === "split"}
            />
          </Suspense>
        </section>

        <dl className="grid grid-cols-3 gap-3 border-t border-slate-200 pt-3">
          <Metric label={t("promptTokens")} value={formatTokens(finding.prompt_tokens)} />
          <Metric label={t("completionTokens")} value={formatTokens(finding.completion_tokens)} />
          <Metric label={t("totalTokens")} value={formatTokens(finding.total_tokens)} />
        </dl>
      </div>
    </article>
  );
});

function EvidenceList({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h3 className="mb-1 text-xs font-semibold uppercase text-slate-500">{title}</h3>
      {items.length > 0 ? (
        <ul className="space-y-1 text-xs leading-5 text-slate-700">
          {items.map((item, index) => (
            <li key={`${item}-${index}`} className="break-words">
              {item}
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-xs text-slate-500">[]</p>
      )}
    </section>
  );
}
