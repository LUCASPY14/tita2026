import { useEffect, useRef } from 'react'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'

function urlBase64ToUint8Array(base64String: string): Uint8Array<ArrayBuffer> {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = window.atob(base64)
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)))
}

export function usePushNotifications() {
  const { isAuthenticated, user } = useAuthStore()
  // Track which user ID already registered push in this session.
  // Resets when a different user logs in on the same device.
  const subscribedUserId = useRef<number | null>(null)

  useEffect(() => {
    if (!isAuthenticated || !user) {
      subscribedUserId.current = null
      return
    }
    if (import.meta.env.DEV) return   // sin service worker ni VAPID en desarrollo
    if (subscribedUserId.current === user.id) return
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) return
    if (Notification.permission === 'denied') return

    let cancelled = false

    const trySubscribe = async () => {
      try {
        const { data } = await api.get<{ publicKey: string }>('/notificaciones/vapid-public-key/')
        if (cancelled) return

        const permission = await Notification.requestPermission()
        if (permission !== 'granted' || cancelled) return

        const reg = await navigator.serviceWorker.ready
        const existing = await reg.pushManager.getSubscription()

        const sub = existing ?? await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(data.publicKey),
        })

        if (cancelled) return
        await api.post('/notificaciones/push-subscription/', sub.toJSON())
        subscribedUserId.current = user.id
      } catch {
        // Push notifications are optional — fail silently
      }
    }

    trySubscribe()
    return () => { cancelled = true }
    // Solo re-suscribir cuando cambia el usuario logueado, no ante cualquier
    // cambio de referencia del objeto `user` (p.ej. al refrescar su perfil).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, user?.id])
}
