import type { ReactNode } from "react";

export function MetricGroup({
  children,
  columns = "grid-cols-2",
  className = "",
}: {
  children: ReactNode;
  className?: string;
  columns?: string;
}) {
  return <dl className={`grid gap-3 ${columns} ${className}`}>{children}</dl>;
}

