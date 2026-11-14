import type { Config } from "tailwindcss";
import colors from "tailwindcss/colors";

/**
 * MyCTF design tokens — the single source of truth.
 *
 * - Spacing: Tailwind's default scale, used in 8px steps only (2, 4, 6, 8, 10, 12, 16…).
 * - Brand:   ONE primary color. Re-skin the whole app by changing the `brand` alias.
 * - Neutrals: Tailwind `gray` for every surface, border and text color.
 * - Theme:   dark-only, so components use dark values directly (no `dark:` variants).
 */
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: colors.red,
      },
      // Layout tokens (named, not ad-hoc): full height under the 64px top bar,
      // and the draggable brief column on the challenge play screen.
      height: { app: "calc(100vh - 4rem)" },
      width: { play: "var(--play-left)" },
      // Terminal cursor: a solid block that switches off for half of each second.
      keyframes: {
        blink: {
          "0%, 49%": { backgroundColor: colors.gray[200], color: colors.black },
          "50%, 100%": { backgroundColor: "transparent", color: "inherit" },
        },
      },
      animation: { blink: "blink 1s step-end infinite" },
      fontFamily: {
        mono: [
          "ui-monospace",
          "SFMono-Regular",
          "JetBrains Mono",
          "Menlo",
          "Consolas",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
