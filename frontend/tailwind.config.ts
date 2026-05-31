import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "var(--color-canvas)",
        panel: "var(--color-panel)",
        border: {
          DEFAULT: "var(--color-border)",
          subtle: "var(--color-border-subtle)",
        },
        text: {
          strong: "var(--color-text-strong)",
          DEFAULT: "var(--color-text)",
          muted: "var(--color-text-muted)",
          inverse: "var(--color-text-inverse)",
        },
        surface: {
          DEFAULT: "var(--color-surface)",
          muted: "var(--color-surface-muted)",
          50: "#f8faf9",
          100: "#edf2ef",
          200: "#d9e3dd",
          800: "#24302a",
          900: "#151c18",
        },
        audit: {
          teal: "var(--color-accent)",
          blue: "var(--color-running)",
          red: "var(--color-danger)",
          amber: "var(--color-warning)",
          green: "var(--color-success)",
        },
      },
      borderRadius: {
        xs: "var(--radius-xs)",
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
      },
      boxShadow: {
        floating: "var(--shadow-floating)",
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
        mono: ["var(--font-mono)"],
      },
    },
  },
  plugins: [],
} satisfies Config;
