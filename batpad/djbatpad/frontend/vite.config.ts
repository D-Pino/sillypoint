import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/static/',
  build: {
    manifest: true,
    outDir: 'dist',
    assetsDir: 'assets',
    rollupOptions: { input: 'src/main.tsx' },
  },
  server: { port: 5173, strictPort: true, host: "localhost" },
})
