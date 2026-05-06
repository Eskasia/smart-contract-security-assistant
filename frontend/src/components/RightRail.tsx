import { formatScore, formatTokens } from "../lib/format";
import { useTranslation } from "../lib/i18n";
import { useAnalysisStore } from "../store/analysisStore";
import { Metric } from "./Metric";
import { ReviewerPanel } from "./ReviewerPanel";
import { TracePanel } from "./TracePanel";

function shortenHash(value: string) {
  if (value.length <= 18) return value;
  return `${value.slice(0, 6)}...${value.slice(-6)}`;
}

export function RightRail() {
  const { t } = useTranslation();
  const report = useAnalysisStore((state) => state.report);
  const metadata = report.analysis_metadata;
  const zeroGProof = metadata.zero_g_proof;
  const zeroGLinks = zeroGProof?.explorer_links;

  return (
    <aside className="flex w-full shrink-0 flex-col overflow-auto border-t border-slate-200 bg-surface-50 px-4 py-4 lg:h-full lg:w-[360px] lg:border-l lg:border-t-0">
      <ReviewerPanel />

      <section className="space-y-3 border-b border-slate-200 py-4">
        <h2 className="text-sm font-semibold text-slate-950">{t("metrics")}</h2>
        <dl className="grid grid-cols-2 gap-3">
          <Metric label={t("scoreFormula")} value={report.score_formula_version ?? "security_score_v2"} />
          <Metric label={t("promptTokens")} value={formatTokens(metadata.prompt_tokens)} />
          <Metric label={t("completionTokens")} value={formatTokens(metadata.completion_tokens)} />
          <Metric label={t("totalTokens")} value={formatTokens(metadata.total_tokens)} />
          <Metric label={t("localJudge")} value={formatScore(metadata.local_average_judge_score)} />
          <Metric label={t("externalJudge")} value={formatScore(metadata.external_average_judge_score)} />
        </dl>
        {metadata.errors.length > 0 && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs leading-5 text-amber-900">
            {metadata.errors.join(" ")}
          </div>
        )}
      </section>

      {zeroGProof && (
        <section className="space-y-3 border-b border-slate-200 py-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-sm font-semibold text-slate-950">0G Proof</h2>
            {zeroGLinks?.registry && (
              <a
                className="shrink-0 text-xs font-semibold text-audit-blue hover:text-slate-950"
                href={zeroGLinks.registry}
                rel="noreferrer"
                target="_blank"
              >
                Registry
              </a>
            )}
          </div>
          <dl className="space-y-2 text-xs">
            <div className="min-w-0 rounded-md border border-slate-200 bg-white p-3">
              <dt className="font-semibold uppercase text-slate-500">Storage root</dt>
              <dd className="mt-1 break-all font-mono text-slate-900">
                {shortenHash(zeroGProof.storage_root_hash)}
              </dd>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="min-w-0 rounded-md border border-slate-200 bg-white p-3">
                <dt className="font-semibold uppercase text-slate-500">Registry</dt>
                <dd className="mt-1 truncate font-mono text-slate-900">
                  {shortenHash(zeroGProof.registry_address)}
                </dd>
              </div>
              <div className="min-w-0 rounded-md border border-slate-200 bg-white p-3">
                <dt className="font-semibold uppercase text-slate-500">Storage tx</dt>
                <dd className="mt-1 truncate font-mono text-slate-900">
                  {shortenHash(zeroGProof.storage_tx_hash)}
                </dd>
              </div>
            </div>
            <div className="min-w-0 rounded-md border border-slate-200 bg-white p-3">
              <dt className="font-semibold uppercase text-slate-500">Register tx</dt>
              <dd className="mt-1 break-all font-mono text-slate-900">
                {shortenHash(zeroGProof.registry_tx_hash)}
              </dd>
            </div>
          </dl>
          <div className="flex flex-wrap gap-2 text-xs font-semibold">
            {zeroGLinks?.storage_tx && (
              <a
                className="rounded border border-slate-200 bg-white px-2 py-1 text-slate-700 hover:border-audit-blue hover:text-audit-blue"
                href={zeroGLinks.storage_tx}
                rel="noreferrer"
                target="_blank"
              >
                Storage tx
              </a>
            )}
            {zeroGLinks?.registration_tx && (
              <a
                className="rounded border border-slate-200 bg-white px-2 py-1 text-slate-700 hover:border-audit-blue hover:text-audit-blue"
                href={zeroGLinks.registration_tx}
                rel="noreferrer"
                target="_blank"
              >
                Registration tx
              </a>
            )}
          </div>
        </section>
      )}

      <section className="space-y-3 border-b border-slate-200 py-4">
        <h2 className="text-sm font-semibold text-slate-950">{t("externalTools")}</h2>
        {report.external_tool_results && report.external_tool_results.length > 0 ? (
          <div className="space-y-2">
            {report.external_tool_results.map((result) => (
              <div key={result.tool_name} className="rounded-md border border-slate-200 bg-white p-3">
                <div className="flex items-center justify-between gap-2 text-xs">
                  <span className="font-semibold uppercase text-slate-700">
                    {result.tool_name}
                  </span>
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-mono text-slate-700">
                    {result.status}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-600">{result.summary}</p>
                <p className="mt-1 font-mono text-xs text-slate-500">
                  findings {result.findings_count}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-slate-500">{t("noExternalTools")}</p>
        )}
      </section>

      <div className="py-4">
        <TracePanel />
      </div>
    </aside>
  );
}
