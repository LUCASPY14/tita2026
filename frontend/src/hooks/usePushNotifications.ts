import { useEffect, useRef } from 'react'
import api from '../services/api'
import { useAuthStore } from '../store/authStore'

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = '='.repeat((4 - (base64String.length % 4)) % 4)
  const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = window.atob(base64)
  return Uint8Array.from([...raw].map(c => c.charCodeAt(0)))
}

export function usePushNotifications() {
  const { isAuthenticated } = useAuthStore()
  const subscribed = useRef(false)

  useEffect(() => {
    if (!isAuthenticated || subscribed.current) return
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
        subscribed.current = true
      } catch {
        // Push notifications are optional — fail silently
      }
    }

    trySubscribe()
    return () => { cancelled = true }
  }, [isAuthenticated])
}
