import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Use an assigned PORT when one is given (e.g. when 5173 is taken);
// otherwise Vite's default 5173.
const assignedPort = Number(process.env.PORT);

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: assignedPort
    ? { port: assignedPort, strictPort: true }
    : undefined,
});