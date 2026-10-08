import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig(({ mode }) => ({
  envDir: "..",
  plugins: [react(), tailwindcss()],
  define:
    mode === "production" && !process.env.VITE_API_BASE_URL
      ? {
          "import.meta.env.VITE_API_BASE_URL": "undefined",
        }
      : {},
}));
