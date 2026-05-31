import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "destructive" | "ghost";
type ButtonSize = "sm" | "md" | "icon";

const variantClasses: Record<ButtonVariant, string> = {
  primary: "border-transparent bg-slate-900 text-white hover:bg-slate-800 disabled:bg-slate-400",
  secondary:
    "border-border-subtle bg-surface text-slate-900 hover:bg-surface-muted disabled:bg-slate-100 disabled:text-text-muted",
  destructive:
    "border-red-200 bg-red-50 text-audit-red hover:bg-red-100 disabled:bg-slate-100 disabled:text-text-muted",
  ghost:
    "border-transparent bg-transparent text-slate-700 hover:bg-slate-100 disabled:text-text-muted",
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: "h-8 gap-1.5 px-2.5 text-xs",
  md: "h-10 gap-2 px-3 text-sm",
  icon: "h-8 w-8 justify-center p-0",
};

export function Button({
  children,
  className = "",
  size = "md",
  variant = "secondary",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  size?: ButtonSize;
  variant?: ButtonVariant;
}) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center rounded-sm border font-semibold transition active:translate-y-px disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-audit-teal ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {children}
    </button>
  );
}

