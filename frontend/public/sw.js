const CACHE_NAME = 'cantina-tita-v1.0.0';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/manifest.json',
  '/assets/logo192.png',
  '/assets/logo512.png'
];

// Lista de URLs de la API que queremos cachear para offline
const apiUrlsToCache = [
  '/api/v1/auth/profile',
  '/api/v1/dashboard/kpis',
  '/api/v1/productos/',
  '/api/v1/clientes/',
];

// Install event - cachear recursos estáticos
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching app shell');
        return cache.addAll(urlsToCache);
      })
      .then(() => {
        console.log('[ServiceWorker] Installed successfully');
        return self.skipWaiting(); // Activar inmediatamente
      })
      .catch((error) => {
        console.error('[ServiceWorker] Install failed:', error);
      })
  );
});

// Activate event - limpiar caches antiguos
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[ServiceWorker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[ServiceWorker] Activated successfully');
        return self.clients.claim(); // Tomar control inmediato
      })
  );
});

// Fetch event - estrategia de cache
self.addEventListener('fetch', (event) => {
  const requestUrl = new URL(event.request.url);
  
  // Solo manejar requests HTTP/HTTPS
  if (!requestUrl.protocol.startsWith('http')) {
    return;
  }

  event.respondWith(
    caches.match(event.request)
      .then((response) => {
        // Si está en cache, devolverlo
        if (response) {
          console.log('[ServiceWorker] Serving from cache:', event.request.url);
          return response;
        }

        // Si es una request a la API, usar estrategia Network First
        if (requestUrl.pathname.startsWith('/api/')) {
          return networkFirstStrategy(event.request);
        }

        // Para otros recursos, usar Cache First
        return cacheFirstStrategy(event.request);
      })
  );
});

/**
 * Estrategia Network First - para APIs
 * Intenta obtener de la red, si falla usa cache
 */
async function networkFirstStrategy(request) {
  try {
    console.log('[ServiceWorker] Network first for:', request.url);
    
    const networkResponse = await fetch(request);
    
    // Si la respuesta es exitosa, guardarla en cache
    if (networkResponse && networkResponse.status === 200) {
      const responseClone = networkResponse.clone();
      
      caches.open(CACHE_NAME).then((cache) => {
        cache.put(request, responseClone);
      });
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[ServiceWorker] Network failed, trying cache:', request.url);
    
    // Si la red falla, buscar en cache
    const cacheResponse = await caches.match(request);
    if (cacheResponse) {
      return cacheResponse;
    }
    
    // Si tampoco está en cache, devolver offline page o error
    if (request.headers.get('accept').includes('text/html')) {
      return new Response(
        '<html><body><h1>Sin conexión</h1><p>No hay conexión a internet y esta página no está disponible offline.</p></body></html>',
        {
          headers: { 'Content-Type': 'text/html' },
          status: 503,
          statusText: 'Service Unavailable'
        }
      );
    }
    
    return new Response('Offline', { status: 503 });
  }
}

/**
 * Estrategia Cache First - para recursos estáticos
 * Usa cache primero, si no existe va a la red
 */
async function cacheFirstStrategy(request) {
  try {
    console.log('[ServiceWorker] Cache first for:', request.url);
    
    // Intentar obtener de la red
    const networkResponse = await fetch(request);
    
    // Cachear la respuesta si es exitosa
    if (networkResponse && networkResponse.status === 200) {
      const responseClone = networkResponse.clone();
      
      caches.open(CACHE_NAME).then((cache) => {
        cache.put(request, responseClone);
      });
    }
    
    return networkResponse;
  } catch (error) {
    console.log('[ServiceWorker] Network failed for static resource:', request.url);
    return new Response('Offline', { status: 503 });
  }
}

// Evento para manejar notificaciones push
self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received');
  
  if (!event.data) {
    console.log('Push event but no data');
    return;
  }
  
  const data = event.data.json();
  const options = {
    body: data.body || 'Nueva notificación de Cantina Tita',
    icon: '/assets/logo192.png',
    badge: '/assets/logo192.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: data.primaryKey || 1,
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver más',
        icon: '/assets/logo192.png',
      },
      {
        action: 'close',
        title: 'Cerrar',
        icon: '/assets/logo192.png',
      },
    ],
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Cantina Tita', options)
  );
});

// Manejar clicks en notificaciones
self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification click received');
  
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'close') {
    console.log('Notification closed by user action');
  } else {
    // Click en la notificación (no en una acción específica)
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Manejar mensajes del main thread
self.addEventListener('message', (event) => {
  console.log('[ServiceWorker] Message received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

console.log('[ServiceWorker] Service Worker loaded successfully');