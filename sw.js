// Luo Étudiant Oyé — service worker
// Stratégie : toujours essayer le réseau d'abord pour index.html (le jeu ne peut plus rester vieux),
// cache-first pour les gros fichiers (modèles, données) qui changent rarement.
const CACHE = 'luo-v3.2.2';
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
      .then(() => self.skipWaiting())   // l'ancien SW se fait remplacer tout de suite
      .catch(err => console.warn('SW install: assets manquants', err))
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// document (index.html / racine) : RESEAU D'ABORD, cache en secours hors ligne
// assets lourds : cache-first, réseau en secours + mise a jour du cache
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  const isOurs = url.origin === self.location.origin;
  const isDoc = url.pathname === '/' || /index\.html$/.test(url.pathname);

  const cacheFirst = res => {
    if (res && res.ok){ const clone = res.clone(); caches.open(CACHE).then(c => c.put(e.request, clone)); }
    return res;
  };

  if (isOurs && isDoc){
    e.respondWith(
      fetch(e.request).then(cacheFirst).catch(() => caches.match(e.request).then(r => r || caches.match('./index.html')))
    );
  } else if (isOurs){
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(cacheFirst).catch(() => caches.match('./index.html')))
    );
  } else {
    // satellite Esri, CDN three.js : cache dynamique pour jouer hors ligne
    e.respondWith(
      caches.match(e.request).then(r => r || fetch(e.request).then(cacheFirst).catch(() => r))
    );
  }
});
