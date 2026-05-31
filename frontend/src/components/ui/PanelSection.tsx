import type { ReactNode } from "react";

export function PanelSection({
  children,
  title,
}: {
  children: ReactNode;
  title?: ReactNode;
}) {
  return (
    <section className="space-y-3 border-b border-border-subtle py-4">
      {title ? <h2 className="text-sm font-semibold text-text-strong">{title}</h2> : null}
      {children}
    </section>
  );
}

