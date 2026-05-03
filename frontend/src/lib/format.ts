import type { Finding, Location } from "../types/report";

export function formatLocation(location: Location): string {
  const range =
    location.line_start === location.line_end
      ? `${location.line_start}`
      : `${location.line_start}-${location.line_end}`;
  return `${location.file}:${range}`;
}

export function formatScore(score: number | undefined): string {
  return `${(score ?? 0).toFixed(2)}/5`;
}

export function formatTokens(value: number | undefined): string {
  return new Intl.NumberFormat("en-US").format(value ?? 0);
}

export function severityLabel(severity: number): string {
  if (severity >= 4) return "Critical";
  if (severity === 3) return "High";
  if (severity === 2) return "Medium";
  if (severity === 1) return "Low";
  return "Info";
}

export function findingTitle(finding: Finding): string {
  return `${finding.finding_id} · ${finding.vulnerability_type}`;
}
