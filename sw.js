// Cache-first, damit die Karte im Flugmodus startet. Bei Netz wird im Hintergrund
// aufgefrischt, Korrekturen erscheinen so beim übernächsten Öffnen.
const CACHE="kas-kekova-v1";
const FILES=["./","index.html","Kas-Kekova_Woche.gpx","manifest.json","icon-192.png","icon-512.png","apple-touch-icon.png"];
self.addEventListener("install",e=>{
  e.waitUntil(caches.open(CACHE).then(c=>c.addAll(FILES)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate",e=>{
  e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));
});
self.addEventListener("fetch",e=>{
  if(e.request.method!=="GET"||new URL(e.request.url).origin!==location.origin) return;
  e.respondWith(caches.open(CACHE).then(async c=>{
    const hit=await c.match(e.request,{ignoreSearch:true});
    const net=fetch(e.request).then(r=>{if(r.ok) c.put(e.request,r.clone());return r;}).catch(()=>hit);
    return hit||net;
  }));
});
