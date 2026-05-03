import type { AnalysisStatus, ReviewStatus } from "../types/report";

export function isTerminalStatus(status: AnalysisStatus): boolean {
  return status === "finding" || status === "no_finding" || status === "partial_analysis" || status === "error";
}

export function statusText(status: AnalysisStatus): string {
  const labels: Record<AnalysisStatus, string> = {
    queued: "Queued",
    running: "Running",
    finding: "Finding",
    no_finding: "No finding",
    partial_analysis: "Partial",
    error: "Error",
  };
  return labels[status];
}

export function reviewStatusText(status: ReviewStatus): string {
  const labels: Record<ReviewStatus, string> = {
    pending_human_review: "Pending",
    approved: "Approved",
    rejected: "Rejected",
    blocked: "Blocked",
  };
  return labels[status];
}
