self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);
  // Network-first for API
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(fetch(req));
    return;
  }
  // Always fetch fresh HTML (navigations) so the Matrix theme is consistent
  const accept = req.headers.get('accept') || '';
  if (req.mode === 'navigate' || accept.includes('text/html')) {
    event.respondWith(
      fetch(req).catch(() => caches.match(req))
    );
    return;
  }
  // Cache-first for other static assets (css/js/img), bump cache version to avoid stale behavior
  event.respondWith(
    caches.open('jai-static-v2').then(cache =>
      cache.match(req).then(resp => resp || fetch(req).then(r => { cache.put(req, r.clone()); return r; }))
    )
  );
});
