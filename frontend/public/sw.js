/**
 * Service Worker — Estrategia offline para ModoRecreo (POS)
 *
 * Cache strategy:
 *   - GET /api/v1/productos/, /api/v1/core/medios-pago/  → StaleWhileRevalidate
 *     (catálogo actualizado en background; siempre responde rápido)
 *   - GET /api/v1/core/tarjetas/                         → NetworkFirst con fallback a cache
 *     (saldo real si hay red; cache si offline)
 *   - POST /api/v1/ventas/ventas/                        → NetworkOnly con BackgroundSync
 *     (la venta se encola en IndexedDB si falla; se reintenta al reconectar)
 *   - Todo lo demás                                      → NetworkOnly (sin cache)
 */

const CACHE_NAME     = 'cantina-v1'
const SYNC_TAG       = 'sync-ventas'
const IDB_DB         = 'cantina-offline'
const IDB_STORE      = 'pending-ventas'

// URLs que cacheamos para catálogo
const CATALOG_PATTERNS = [
  /\/api\/v1\/productos\/productos\//,
  /\/api\/v1\/core\/medios-pago\//,
]
const TARJETA_PATTERN = /\/api\/v1\/core\/tarjetas\//

// ─── Install: pre-cache shell de la app ──────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(() => self.skipWaiting())
  )
})

// ─── Activate: limpiar caches viejas ─────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  )
})

// ─── Fetch handler ────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event
  const url = request.url

  // POST /api/v1/ventas/ventas/ → queue si offline
  if (request.method === 'POST' && /\/api\/v1\/ventas\/ventas\//.test(url)) {
    event.respondWith(networkWithOfflineQueue(request))
    return
  }

  // GET tarjetas → NetworkFirst con fallback
  if (request.method === 'GET' && TARJETA_PATTERN.test(url)) {
    event.respondWith(networkFirst(request))
    return
  }

  // GET catálogo → StaleWhileRevalidate
  if (request.method === 'GET' && CATALOG_PATTERNS.some(p => p.test(url))) {
    event.respondWith(staleWhileRevalidate(request))
    return
  }

  // Todo lo demás → red normal
})

// ─── BackgroundSync: reintentar ventas pendientes ─────────────────────────────
self.addEventListener('sync', event => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(flushPendingVentas())
  }
})

// ─── Strategies ───────────────────────────────────────────────────────────────
async function staleWhileRevalidate(request) {
  const cache = await caches.open(CACHE_NAME)
  const cached = await cache.match(request)
  const fetchPromise = fetch(request).then(res => {
    if (res.ok) cache.put(request, res.clone())
    return res
  }).catch(() => null)
  return cached || await fetchPromise || new Response('', { status: 503 })
}

async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME)
  try {
    const res = await fetch(request)
    if (res.ok) cache.put(request, res.clone())
    return res
  } catch {
    const cached = await cache.match(request)
    return cached || new Response(
      JSON.stringify({ results: [], count: 0, _offline: true }),
      { status: 200, headers: { 'Content-Type': 'application/json' } }
    )
  }
}

async function networkWithOfflineQueue(request) {
  try {
    const res = await fetch(request.clone())
    return res
  } catch {
    // Red no disponible → guardar en IDB para BackgroundSync
    const body = await request.clone().text()
    await idbPut(IDB_STORE, {
      id:        Date.now(),
      url:       request.url,
      method:    request.method,
      body,
      headers:   Object.fromEntries(request.headers.entries()),
      timestamp: new Date().toISOString(),
    })

    // Registrar sync tag si el API está disponible
    if ('serviceWorker' in self && 'SyncManager' in self) {
      await self.registration.sync.register(SYNC_TAG).catch(() => {})
    }

    return new Response(
      JSON.stringify({ _queued: true, message: 'Venta guardada offline. Se sincronizará al reconectar.' }),
      { status: 202, headers: { 'Content-Type': 'application/json' } }
    )
  }
}

async function flushPendingVentas() {
  const pending = await idbGetAll(IDB_STORE)
  for (const item of pending) {
    try {
      const res = await fetch(item.url, {
        method:  item.method,
        body:    item.body,
        headers: item.headers,
      })
      if (res.ok || res.status === 400) {
        // 400 = error de negocio (no reintentable), eliminamos igual
        await idbDelete(IDB_STORE, item.id)
      }
    } catch {
      // Seguir offline — se intentará en el próximo sync
    }
  }
}

// ─── Helpers IndexedDB (sin librería externa) ─────────────────────────────────
function openIDB() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(IDB_DB, 1)
    req.onupgradeneeded = e => {
      e.target.result.createObjectStore(IDB_STORE, { keyPath: 'id' })
    }
    req.onsuccess  = e => resolve(e.target.result)
    req.onerror    = e => reject(e.target.error)
  })
}

async function idbPut(store, value) {
  const db = await openIDB()
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(store, 'readwrite')
    const req = tx.objectStore(store).put(value)
    req.onsuccess = () => resolve(req.result)
    req.onerror   = () => reject(req.error)
  })
}

async function idbGetAll(store) {
  const db = await openIDB()
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(store, 'readonly')
    const req = tx.objectStore(store).getAll()
    req.onsuccess = () => resolve(req.result)
    req.onerror   = () => reject(req.error)
  })
}

async function idbDelete(store, id) {
  const db = await openIDB()
  return new Promise((resolve, reject) => {
    const tx  = db.transaction(store, 'readwrite')
    const req = tx.objectStore(store).delete(id)
    req.onsuccess = () => resolve()
    req.onerror   = () => reject(req.error)
  })
}
