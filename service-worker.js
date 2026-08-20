const CACHE='prophet-biography-v6-8-7-people-v1';
const PRECACHE=[
  './library.html',
  './reader.html',
  './people.html',
  './manifest.webmanifest',
  './assets/bookstore.css',
  './assets/bookstore-published.css',
  './assets/library-extended.css',
  './assets/tarjma-fonts.css',
  './assets/prophet-bookreader.css',
  './assets/people.css',
  './assets/bookstore.js',
  './assets/library-extended.js',
  './assets/reader-route.js',
  './assets/prophet-bookreader.js',
  './assets/universal-player.js',
  './assets/api.js',
  './assets/people.js',
  './data/reader_config.json',
  './data/published_user_books.json',
  './data/user_ingested_books.json',
  './data/generated_epubs.json',
  './data/people/manifest.json',
  './data/people/family-core.json',
  './data/people/rijal-audit.json',
  './private/acquisition_candidates.json'
];
self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(cache=>Promise.allSettled(PRECACHE.map(asset=>cache.add(asset)))).then(()=>self.skipWaiting()));
});
self.addEventListener('activate',event=>{
  event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));
});
const NETWORK_FIRST=new Set([
  '/library.html','/reader.html','/people.html','/assets/bookstore.js','/assets/bookstore.css','/assets/bookstore-published.css',
  '/assets/library-extended.js','/assets/library-extended.css','/assets/tarjma-fonts.css',
  '/assets/reader-route.js','/assets/prophet-bookreader.js','/assets/prophet-bookreader.css','/assets/people.js','/assets/people.css',
  '/data/reader_config.json','/data/published_user_books.json','/data/user_ingested_books.json','/data/generated_epubs.json',
  '/data/people/manifest.json','/data/people/family-core.json','/data/people/rijal-audit.json','/data/people/rijal-index.json'
]);
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
  if(NETWORK_FIRST.has(url.pathname)){
    event.respondWith(fetch(event.request,{cache:'no-store'}).then(response=>{
      if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));}
      return response;
    }).catch(async()=>await caches.match(event.request)||Response.error()));
    return;
  }
  event.respondWith(caches.match(event.request).then(async cached=>{
    if(cached)return cached;
    try{
      const response=await fetch(event.request);
      if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy));}
      return response;
    }catch(_err){return Response.error();}
  }));
});
