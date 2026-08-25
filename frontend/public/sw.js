/**
 * Service Worker — Estrategia offline para ModoRecreo (POS) y Comedor
 *
 * Cache strategy:
 *   - GET /api/v1/productos/, /api/v1/core/medios-pago/  → StaleWhileRevalidate
 *     (catálogo actualizado en background; siempre responde rápido)
 *   - GET /api/v1/core/tarjetas/                         → NetworkFirst con fallback a cache
 *     (saldo real si hay red; cache si offline — usado por ModoRecreo y Comedor)
 *   - POST /api/v1/ventas/ventas/                        → NetworkOnly con BackgroundSync
 *   - POST /api/v1/almuerzos/registros-consumo/          → NetworkOnly con BackgroundSync
 *     (se encolan en IndexedDB si falla la red; se reintentan solos al reconectar —
 *     misma cola genérica para ambos POST, la respuesta 202 optimista ya se trata
 *     como éxito del lado del frontend en los dos flujos)
 *   - Todo lo demás                                      → NetworkOnly (sin cache)
 */

const CACHE_NAME     = 'cantina-v2'
const SYNC_TAG       = 'sync-ventas'
const IDB_DB         = 'cantina-offline'
const IDB_STORE      = 'pending-ventas'  // cola genérica de POST pendientes (ventas + registros de consumo)

// URLs que cacheamos para catálogo (ModoRecreo)
const CATALOG_PATTERNS = [
  /\/api\/v1\/productos\/productos\//,
  /\/api\/v1\/core\/medios-pago\//,
]
const TARJETA_PATTERN = /\/api\/v1\/core\/tarjetas\//

// Datos financieros del portal — NetworkFirst (saldo siempre fresco)
const PORTAL_SALDO_PATTERNS = [
  /\/api\/v1\/usuarios\/portal\/mi-hijo\//,
]

// Resto del portal — StaleWhileRevalidate (historial, notificaciones; aceptable algo de lag)
const PORTAL_PATTERNS = [
  /\/api\/v1\/usuarios\/portal\/(?!mi-hijo)/,
  /\/api\/v1\/almuerzos\/suscripciones\//,
  /\/api\/v1\/notificaciones\/notificaciones\//,
]

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

// URLs de POST que se encolan en IndexedDB si falla la red (ventas y consumo de comedor)
const OFFLINE_QUEUE_POST_PATTERNS = [
  /\/api\/v1\/ventas\/ventas\//,
  /\/api\/v1\/almuerzos\/registros-consumo\//,
]

// ─── Fetch handler ────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const { request } = event
  const url = request.url

  // POST venta o registro de consumo → queue si offline
  if (request.method === 'POST' && OFFLINE_QUEUE_POST_PATTERNS.some(p => p.test(url))) {
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

  // GET mi-hijo (saldo) → NetworkFirst: datos financieros siempre frescos
  if (request.method === 'GET' && PORTAL_SALDO_PATTERNS.some(p => p.test(url))) {
    event.respondWith(networkFirst(request))
    return
  }

  // GET portal (historial, notificaciones, etc.) → StaleWhileRevalidate
  if (request.method === 'GET' && PORTAL_PATTERNS.some(p => p.test(url))) {
    event.respondWith(staleWhileRevalidate(request))
    return
  }

  // Todo lo demás → red normal
})

// ─── Push notifications ───────────────────────────────────────────────────────
self.addEventListener('push', event => {
  if (!event.data) return
  let payload
  try { payload = event.data.json() } catch { payload = { title: 'Cantina Tita', body: event.data.text() } }
  const {
    title = 'Cantina Tita',
    body  = '',
    icon  = '/logo_tita.png',
    url   = '/',
  } = payload
  event.waitUntil(
    self.registration.showNotification(title, {
      body,
      icon,
      badge: '/logo_tita.png',
      tag:   'cantina-notif',
      data:  { url },
      requireInteraction: false,
    })
  )
})

self.addEventListener('notificationclick', event => {
  event.notification.close()
  const target = event.notification.data?.url || '/'
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const client of list) {
        if ('focus' in client) { client.navigate(target); return client.focus() }
      }
      if (clients.openWindow) return clients.openWindow(target)
    })
  )
})

// ─── BackgroundSync: reintentar ventas y registros de consumo pendientes ──────
self.addEventListener('sync', event => {
  if (event.tag === SYNC_TAG) {
    event.waitUntil(flushPendingRequests())
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
      JSON.stringify({ _queued: true, message: 'Guardado offline. Se sincronizará al reconectar.' }),
      { status: 202, headers: { 'Content-Type': 'application/json' } }
    )
  }
}

async function flushPendingRequests() {
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
