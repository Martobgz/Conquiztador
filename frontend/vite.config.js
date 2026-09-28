import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      // The API is served through the dev server so the browser treats it as
      // same-origin. That keeps the session and csrftoken cookies working
      // without CORS, and keeps Django's Origin/Host CSRF check happy
      // (changeOrigin stays false so the Host header is not rewritten).
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
      },
    },
  },
})
