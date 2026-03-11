const CACHE_NAME = "nurcoran-v1";
const STATIC_ASSETS = [
  "/",
  "/offline/",
  "/static/css/nurapp.css",
  "/static/css/custom.css",
  "/static/js/nurapp.js",
  "/static/js/main.js",
  "/static/images/icon-192.png",
  "/static/images/icon-512.png",
  "/azkar/",
  "/tasbih/",
  "/prayer-times/",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(STATIC_ASSETS))
  );
});

self.addEventListener("fetch", (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      if (response) return response;

      return fetch(event.request)
        .then((networkResponse) => {
          if (networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        })
        .catch(() => caches.match("/offline/"));
    })
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
});
