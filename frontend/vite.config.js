
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Configure Vite, the development server for React.
export default defineConfig({
  plugins: [react()],

  server: {
    // Forward requests beginning with /api to FastAPI.
    // This avoids browser cross-origin restrictions during development.
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',

        // Change the request origin to match FastAPI.
        changeOrigin: true,

        // Remove /api before forwarding the request.
        // Example: /api/chat becomes /chat.
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
