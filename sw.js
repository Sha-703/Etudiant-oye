// Luo Étudiant Oyé — service worker
// Stratégie : toujours essayer le réseau d'abord pour index.html (le jeu ne peut plus rester vieux),
// cache-first pour les gros fichiers (modèles, données) qui changent rarement.
const CACHE = 'luo-v1.11.0';
const ASSETS = [
  './',
  './index.html',
  './roads.js',
  './manifest.json',
  './icon.svg',
  './vendor/three.module.min.js',
  './vendor/addons/math/SimplexNoise.js',
  './vendor/addons/loaders/GLTFLoader.js',
  './vendor/addons/loaders/DRACOLoader.js',
  './vendor/addons/utils/SkeletonUtils.js',
  './vendor/addons/utils/BufferGeometryUtils.js',
  './vendor/addons/libs/meshopt_decoder.module.js',
  './vendor/addons/postprocessing/EffectComposer.js',
  './vendor/addons/postprocessing/RenderPass.js',
  './vendor/addons/postprocessing/UnrealBloomPass.js',
  './vendor/addons/postprocessing/OutputPass.js',
  './vendor/addons/postprocessing/SMAAPass.js',
  './vendor/addons/postprocessing/SSAOPass.js',
  './vendor/addons/postprocessing/Pass.js',
  './vendor/addons/postprocessing/ShaderPass.js',
  './vendor/addons/postprocessing/MaskPass.js',
  './vendor/addons/shaders/CopyShader.js',
  './vendor/addons/shaders/LuminosityHighPassShader.js',
  './vendor/addons/shaders/OutputShader.js',
  './vendor/addons/shaders/SMAAShader.js',
  './vendor/addons/shaders/SSAOShader.js',
  /* Les modeles (12 Mo) ne sont PLUS precharges a l'installation : ils sont
     mis en cache a la demande par le fetch ci-dessous. Cela evite de les
     telecharger deux fois au premier lancement et accelere nettement le demarrage. */
  './bg-login.jpg'
];
/* Modeles : mis en cache plus tard, a la demande de la page (message warm-models).
   Ils ne bloquent ni l'installation ni le premier demarrage. */
const MODEL_ASSETS = [
  './models/models.json',
  './models/casual_man.glb',
  './models/casual_tex.webp',
  './models/fairheaven.glb',
  './models/fiat_punto.glb',
  './models/gman.glb',
  './models/hero_ps1.glb',
  './models/luaz.glb',
  './models/man_woman_walk.glb',
  './models/mercedes.glb',
  './models/rail_piece.glb',
  './models/runner.glb',
  './models/talking_man.glb',
  './models/casual_man_red.glb',
  './models/casual_man_green.glb',
  './models/casual_man_purple.glb'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      // allSettled : un fichier manquant ne bloque plus toute l'installation
      .then(c => Promise.allSettled(ASSETS.map(u => c.add(u))))
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

/* La page demande la mise en cache des modeles une fois le jeu lance
   (pas pendant le demarrage : la bande passante reste au heros). */
self.addEventListener('message', e => {
  if (!e.data || e.data.type !== 'warm-models') return;
  e.waitUntil(
    caches.open(CACHE).then(c => Promise.allSettled(MODEL_ASSETS.map(u => c.add(u))))
  );
});

// document (index.html / racine) : RESEAU D'ABORD, cache en secours hors ligne
// assets lourds : cache-first, réseau en secours + mise a jour du cache
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.protocol === 'blob:' || url.protocol === 'data:') return;   // textures GLB : ne pas intercepter
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
