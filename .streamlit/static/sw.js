const STATIC_CACHE = "static-v1";
const STATIC_ASSETS = [
  "/static/manifest.json",
  "/static/icons/icon-192.png",
  "/static/icons/icon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(STATIC_CACHE).then((c) => c.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(
      caches.match(event.request).then(
        (res) =>
          res ||
          fetch(event.request).then((net) => {
            const clone = net.clone();
            caches.open(STATIC_CACHE).then((c) => c.put(event.request, clone));
            return net;
          })
      )
    );
  }
});
