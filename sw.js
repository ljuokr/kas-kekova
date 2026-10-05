// Die ganze Karte samt Routenexporten wird vor der Aktivierung gespeichert.
const CACHE_PREFIX = "kas-kekova-";
const CACHE = "kas-kekova-v4";
const FILES = [
  "./", "index.html", "route-data.json",
  "Kas-Kekova_Woche.gpx", "Kas-Kekova_Woche.kml",
  "Kas-Kekova_ohne-Goekkaya.gpx", "Kas-Kekova_ohne-Goekkaya.kml",
  "Goekkaya-Andriake_Option.gpx", "Goekkaya-Andriake_Option.kml",
  "manifest.json", "icon-192.png", "icon-512.png", "apple-touch-icon.png"
];
const SCOPE = new URL(self.registration.scope);
const fileURL = path => new URL(path, SCOPE).href;
const cacheKey = request => {
  const url = new URL(request.url);
  url.search = "";
  return url.href;
};

self.addEventListener("install", event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(FILES.map(path => new Request(fileURL(path), {cache: "reload"}))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys
        .filter(key => key.startsWith(CACHE_PREFIX) && key !== CACHE)
        .map(key => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

async function refresh(request, cache) {
  const response = await fetch(request, {cache: "no-cache"});
  if (response.ok) {
    try {
      await cache.put(cacheKey(request), response.clone());
    } catch {
      // Eine volle Offline-Ablage darf die Online-Antwort nicht verhindern.
    }
  }
  return response;
}

async function navigation(request, cache) {
  const fallback = () => cache.match(cacheKey(request))
    .then(hit => hit || cache.match(fileURL("index.html")));
  try {
    const response = await refresh(request, cache);
    return response.ok ? response : (await fallback()) || response;
  } catch {
    return (await fallback()) || Response.error();
  }
}

self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== SCOPE.origin || !url.pathname.startsWith(SCOPE.pathname)) return;

  const cache = caches.open(CACHE);
  if (request.mode === "navigate") {
    const response = cache.then(store => navigation(request, store));
    event.respondWith(response);
    event.waitUntil(response.then(() => {}, () => {}));
    return;
  }

  // Gespeicherte Dateien sofort ausliefern; Aktualisierung bis zum Ende abwarten.
  const network = cache.then(store => refresh(request, store));
  event.waitUntil(network.then(() => {}, () => {}));
  event.respondWith(cache
    .then(async store => (await store.match(cacheKey(request))) || network)
    .catch(() => Response.error()));
});

self.addEventListener("message", event => {
  if (event.data?.type !== "CHECK_OFFLINE" || !event.ports?.[0]) return;
  const port = event.ports[0];
  event.waitUntil(caches.open(CACHE)
    .then(cache => Promise.all(FILES.map(path => cache.match(fileURL(path)))))
    .then(files => port.postMessage({ready: files.every(Boolean), version: CACHE}))
    .catch(() => port.postMessage({ready: false, version: CACHE})));
});
