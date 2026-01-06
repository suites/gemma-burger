import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react({})],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/chat": {
        target: "http://localhost:3333",
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
