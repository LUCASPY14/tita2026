import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'

// Backend URL para el proxy de desarrollo — sobrescribir en .env.development.local
// En producción, Nginx hace el proxy en el mismo origen (no se usa esta variable).
const BACKEND_URL = process.env.VITE_BACKEND_URL ?? 'http://localhost:8000'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: 'autoUpdate',
      devOptions: { enabled: false },
      manifest: {
        name: 'Cantina Tita',
        short_name: 'Cantina',
        description: 'Sistema de gestión de cantina escolar',
        theme_color: '#1e40af',
        background_color: '#ffffff',
        display: 'standalone',
        orientation: 'portrait',
        start_url: '/modo-recreo',
        icons: [
          { src: '/logo_tita.png', sizes: '192x192', type: 'image/png' },
          { src: '/logo_tita.png', sizes: '512x512', type: 'image/png', purpose: 'any maskable' },
        ],
      },
      workbox: {
        navigateFallback: '/index.html',
        runtimeCaching: [
          {
            urlPattern: /\.(?:js|css|woff2?)$/i,
            handler: 'CacheFirst',
            options: { cacheName: 'static-assets', expiration: { maxAgeSeconds: 31536000 } },
          },
          {
            urlPattern: /\/api\/v1\/productos\//i,
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'api-catalogo', expiration: { maxEntries: 50, maxAgeSeconds: 3600 } },
          },
          {
            urlPattern: /\/api\/v1\/core\/medios-pago\//i,
            handler: 'StaleWhileRevalidate',
            options: { cacheName: 'api-medios-pago', expiration: { maxEntries: 10, maxAgeSeconds: 86400 } },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: BACKEND_URL,
        changeOrigin: true,
      },
      '/ws': {
        target: BACKEND_URL,
        ws: true,
        changeOrigin: true,
      }
    }
  }
})