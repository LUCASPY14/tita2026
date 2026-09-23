import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import './i18n'
import App from './App.tsx'

const SENTRY_DSN = import.meta.env.VITE_SENTRY_DSN as string | undefined
if (SENTRY_DSN) {
  Sentry.init({
    dsn: SENTRY_DSN,
    environment: import.meta.env.MODE,
    release: import.meta.env.VITE_GIT_COMMIT_SHA as string | undefined,
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: 0.1,
    replaysOnErrorSampleRate: 0,
    beforeSend(event) {
      const err = event.exception?.values?.[0]
      // Petición cancelada por AbortController (navegación rápida, etc.)
      if (err?.type === 'AbortError') return null
      // 401 de token caducado — flujo esperado, no es un bug
      if (err?.value?.includes('status code 401')) return null
      return event
    },
  })
}

// Service Worker — offline support (ModoRecreo POS + Portal de Padres)
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  // El navegador chequea actualizaciones del SW por su cuenta, pero con
  // timing variable (a veces recién a las 24h) — se fuerza el chequeo acá.
  navigator.serviceWorker.register('/sw.js', { scope: '/' })
    .then(reg => reg.update().catch(() => {}))
    .catch(() => {})

  // Cuando el SW nuevo (con skipWaiting + clients.claim) toma el control,
  // recargar una vez para que esta pestaña ya sirva desde el SW nuevo — sin
  // esto, alguien puede recargar varias veces y seguir viendo datos viejos
  // (caché del portal, catálogo, etc.) hasta la próxima navegación completa.
  let refrescando = false
  navigator.serviceWorker.addEventListener('controllerchange', () => {
    if (refrescando) return
    refrescando = true
    window.location.reload()
  })
}

// Capturar el prompt de instalación PWA antes de que el browser lo descarte
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault()
  ;(window as unknown as Record<string, unknown>).__pwaPrompt = e
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
