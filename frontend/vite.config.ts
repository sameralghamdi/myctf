import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Local development: run Flask (`python run.py`, port 8000) next to `npm run dev`.
// These prefixes are forwarded to Flask so cookies and API calls are same-origin,
// exactly like the Cloudflare Pages proxy does in production.
const flask = { target: "http://127.0.0.1:8000", changeOrigin: false };
const proxy = { "/api": flask, "/admin/api": flask, "/labs": flask };

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: { proxy },
  // `npm run preview` serves the production build locally with the same proxy.
  preview: { proxy },
  build: {
    outDir: "dist", // Cloudflare Pages "Build output directory"
    target: "es2020",
    sourcemap: false, // never publish source maps
    rollupOptions: {
      output: {
        // React and the router change rarely: a separate file stays cached across releases.
        manualChunks: { vendor: ["react", "react-dom", "react-router-dom"] },
      },
    },
  },
  esbuild:
    mode === "production"
      ? { drop: ["debugger"], pure: ["console.log", "console.debug", "console.info"] }
      : {},
}));
