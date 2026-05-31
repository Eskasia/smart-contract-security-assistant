import type { ReactNode } from "react";

export function Field({
  children,
  error,
  helper,
  label,
}: {
  children: ReactNode;
  error?: string;
  helper?: string;
  label: string;
}) {
  return (
    <label className="block">
      <span className="text-xs font-medium text-text-muted">{label}</span>
      <div className="mt-1">{children}</div>
      {helper && !error ? <p className="mt-1 text-xs text-text-muted">{helper}</p> : null}
      {error ? (
        <p className="mt-1 text-xs font-medium text-audit-red" role="alert">
          {error}
        </p>
      ) : null}
    </label>
  );
}

export const fieldControlClass =
  "w-full rounded-sm border border-border-subtle bg-surface px-3 py-2 text-sm text-text-strong placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-audit-teal disabled:bg-slate-50 disabled:text-text-muted";

