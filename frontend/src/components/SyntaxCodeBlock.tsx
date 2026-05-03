import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import solidity from "react-syntax-highlighter/dist/esm/languages/prism/solidity";
import { oneLight } from "react-syntax-highlighter/dist/esm/styles/prism";

import { useTranslation } from "../lib/i18n";

SyntaxHighlighter.registerLanguage("solidity", solidity);

export function SyntaxCodeBlock({
  code,
  language = "solidity",
}: {
  code: string;
  language?: string;
}) {
  const { t } = useTranslation();

  return (
    <div className="overflow-hidden rounded-md border border-slate-200 bg-slate-50">
      <SyntaxHighlighter
        language={language}
        style={oneLight}
        customStyle={{
          margin: 0,
          padding: "12px",
          background: "transparent",
          fontSize: "12px",
          lineHeight: "18px",
        }}
        wrapLongLines
      >
        {code || t("codeUnavailable")}
      </SyntaxHighlighter>
    </div>
  );
}
