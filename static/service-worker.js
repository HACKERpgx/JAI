self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  // Network-first for API, cache-first for static
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(event.request));
  } else {
    event.respondWith(
      caches.open('jai-static-v1').then(cache =>
        cache.match(event.request).then(resp => resp || fetch(event.request).then(r => { cache.put(event.request, r.clone()); return r; }))
      )
    );
  }
});
