export function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0">
      <dt className="text-xs text-text-muted">{label}</dt>
      <dd className="mt-1 truncate text-sm font-semibold text-text-strong">{value}</dd>
    </div>
  );
}
