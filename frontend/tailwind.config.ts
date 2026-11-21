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
        // Entrance: content rises 8px into place. Used through the `reveal` helper.
        "fade-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": { from: { opacity: "0" }, to: { opacity: "1" } },
        "scale-in": {
          from: { opacity: "0", transform: "scale(0.96)" },
          to: { opacity: "1", transform: "scale(1)" },
        },
        // Podium columns grow from the floor.
        rise: { from: { transform: "scaleY(0.2)", opacity: "0" }, to: { transform: "scaleY(1)", opacity: "1" } },
        shimmer: { "100%": { transform: "translateX(100%)" } },
        // Expanding halo behind the "live" dot.
        ping: { "75%, 100%": { transform: "scale(2.4)", opacity: "0" } },
        // A row whose score just changed glows once.
        flash: { "0%": { backgroundColor: "rgb(239 68 68 / 0.25)" }, "100%": { backgroundColor: "transparent" } },
        float: { "0%, 100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-6px)" } },
        "toast-in": {
          from: { opacity: "0", transform: "translateY(16px) scale(0.98)" },
          to: { opacity: "1", transform: "translateY(0) scale(1)" },
        },
      },
      animation: {
        blink: "blink 1s step-end infinite",
        "fade-up": "fade-up 500ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
        "fade-in": "fade-in 300ms ease-out both",
        "scale-in": "scale-in 200ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
        rise: "rise 700ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
        shimmer: "shimmer 1.6s infinite",
        ping: "ping 1.6s cubic-bezier(0, 0, 0.2, 1) infinite",
        flash: "flash 1.6s ease-out",
        float: "float 4s ease-in-out infinite",
        "toast-in": "toast-in 260ms cubic-bezier(0.2, 0.8, 0.2, 1) both",
      },
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
