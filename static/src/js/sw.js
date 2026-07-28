const CACHE_NAME = "syncora-static-v1";
const STATIC_ASSETS = [
  "/static/manifest.json",
  "/static/img/icon-192.png",
  "/static/img/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
  );
  self.clients.claim();
});

// Só intercepta pedidos de assets estáticos (cache-first). Páginas HTML e
// chamadas de API vão direto pra rede de propósito — um app multiempresa
// com dado sensível não deve ficar em cache offline por padrão.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(caches.match(event.request).then((cached) => cached || fetch(event.request)));
  }
});
