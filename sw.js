// Luvaka — service worker : l'app fonctionne hors ligne (apres 1re visite)
const CACHE = 'luvaka-v3.0.0';
const ASSETS = [
  './',
  './index.html',
  './roads.js',
  './manifest.json',
  './icon.svg',
  './models/models.json',
  './models/casual_man.glb',
  './models/fairheaven.glb',
  './models/fiat_punto.glb',
  './models/gman.glb',
  './models/hero_ps1.glb',
  './models/luaz.glb',
  './models/man_woman_walk.glb',
  './models/mercedes.glb',
  './models/rail_piece.glb',
  './models/runner.glb',
  './models/talking_man.glb'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
      .catch(err => console.warn('SW install: assets manquants', err))
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// cache-first pour les fichiers du jeu ; reseau en secours (et pour le satellite live)
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  const isOurs = url.origin === self.location.origin;
  if (isOurs){
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(res => {
        // on met aussi en cache les nouveaux fichiers requetes (roads.js au cas ou)
        if (res.ok){ const clone = res.clone(); caches.open(CACHE).then(c => c.put(e.request, clone)); }
        return res;
      }).catch(() => caches.match('./index.html')))
    );
  } else {
    // satellite Esri, CDN three.js : cache dynamique pour jouer hors ligne
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(res => {
        if (res.ok){ const clone = res.clone(); caches.open(CACHE).then(c => c.put(e.request, clone)); }
        return res;
      }).catch(() => r))
    );
  }
});
