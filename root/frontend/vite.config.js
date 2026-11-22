import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In dev, /api and /media are forwarded to the Django server (no CORS setup needed).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/media": "http://127.0.0.1:8000",
    },
  },
});
