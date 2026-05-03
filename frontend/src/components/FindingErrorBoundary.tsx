import { Component, type ReactNode } from "react";

export class FindingErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error) {
    console.error("[FindingErrorBoundary]", error);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          此 finding 資料格式異常，請查看 trace 原文。
        </div>
      );
    }

    return this.props.children;
  }
}
