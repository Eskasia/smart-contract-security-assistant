import { lazy, memo, Suspense } from "react";

import { useTranslation } from "../lib/i18n";

const SyntaxCodeBlock = lazy(() =>
  import("./SyntaxCodeBlock").then((module) => ({ default: module.SyntaxCodeBlock })),
);

export const CodeBlock = memo(function CodeBlock(props: { code: string; language?: string }) {
  const { t } = useTranslation();

  return (
    <Suspense
      fallback={
        <pre className="overflow-auto rounded-md border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-700">
          {props.code || t("codeUnavailable")}
        </pre>
      }
    >
      <SyntaxCodeBlock {...props} />
    </Suspense>
  );
});
