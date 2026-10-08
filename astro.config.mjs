import { defineConfig } from "astro/config";

// Se publica en GitHub Pages bajo /ePOEL (ADR 0003: sitio 100% estático)
export default defineConfig({
  site: "https://bajaloreto.github.io",
  base: "/ePOEL",
  trailingSlash: "always",
  build: { format: "directory" },
  vite: { optimizeDeps: { exclude: ["maplibre-gl"] } },
});
