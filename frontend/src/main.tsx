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

// Service Worker — offline POS support for ModoRecreo
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  navigator.serviceWorker.register('/sw.js', { scope: '/' }).catch(() => {
    // SW registration is best-effort; app works normally without it
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
