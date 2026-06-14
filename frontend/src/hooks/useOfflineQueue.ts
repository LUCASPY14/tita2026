import { useCallback, useEffect, useState } from 'react'

const IDB_DB    = 'cantina-offline'
const IDB_STORE = 'pending-ventas'

export interface PendingVenta {
  id:        number
  url:       string
  method:    string
  body:      string
  headers:   Record<string, string>
  timestamp: string
}

function openIDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_DB, 1)
    req.onupgradeneeded = (e) => {
      (e.target as IDBOpenDBRequest).result.createObjectStore(IDB_STORE, { keyPath: 'id' })
    }
    req.onsuccess = (e) => resolve((e.target as IDBOpenDBRequest).result)
    req.onerror   = (e) => reject((e.target as IDBOpenDBRequest).error)
  })
}

async function getPending(): Promise<PendingVenta[]> {
  const db = await openIDB()
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(IDB_STORE, 'readonly')
    const req = tx.objectStore(IDB_STORE).getAll()
    req.onsuccess = () => resolve(req.result as PendingVenta[])
    req.onerror   = () => reject(req.error)
  })
}

async function deletePending(id: number): Promise<void> {
  const db = await openIDB()
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(IDB_STORE, 'readwrite')
    const req = tx.objectStore(IDB_STORE).delete(id)
    req.onsuccess = () => resolve()
    req.onerror   = () => reject(req.error)
  })
}

/**
 * Hook para gestionar la cola offline de ventas.
 *
 * - `pendingCount`: número de ventas pendientes de sincronizar
 * - `isOnline`: estado de conectividad actual
 * - `syncNow()`: fuerza un intento de sincronización manual
 */
export function useOfflineQueue() {
  const [isOnline,     setIsOnline]     = useState(navigator.onLine)
  const [pendingCount, setPendingCount] = useState(0)
  const [syncing,      setSyncing]      = useState(false)

  const refreshCount = useCallback(async () => {
    const items = await getPending().catch(() => [])
    setPendingCount(items.length)
  }, [])

  const syncNow = useCallback(async () => {
    if (syncing || !navigator.onLine) return
    setSyncing(true)
    const items = await getPending().catch(() => [])
    let synced = 0
    for (const item of items) {
      try {
        const res = await fetch(item.url, {
          method:  item.method,
          body:    item.body,
          headers: item.headers,
        })
        if (res.ok || res.status === 400) {
          await deletePending(item.id)
          synced++
        }
      } catch {
        break // sigue offline
      }
    }
    await refreshCount()
    setSyncing(false)
    return synced
  }, [syncing, refreshCount])

  useEffect(() => {
    refreshCount()

    const handleOnline  = () => { setIsOnline(true);  syncNow() }
    const handleOffline = () => { setIsOnline(false); refreshCount() }

    window.addEventListener('online',  handleOnline)
    window.addEventListener('offline', handleOffline)

    // Polling ligero cada 30 s para reflejar items añadidos por el SW
    const timer = setInterval(refreshCount, 30_000)

    return () => {
      window.removeEventListener('online',  handleOnline)
      window.removeEventListener('offline', handleOffline)
      clearInterval(timer)
    }
  }, [refreshCount, syncNow])

  return { isOnline, pendingCount, syncing, syncNow }
}
