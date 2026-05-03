import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          50: "#f8faf9",
          100: "#edf2ef",
          200: "#d9e3dd",
          800: "#24302a",
          900: "#151c18",
        },
        audit: {
          teal: "#0f766e",
          blue: "#2563eb",
          red: "#b91c1c",
          amber: "#b45309",
          green: "#15803d",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "SFMono-Regular",
          "Consolas",
          "Liberation Mono",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
} satisfies Config;
