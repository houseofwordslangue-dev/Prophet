const CACHE='prophet-biography-v6-11-animated-children-600-localized';
const CATALOGUE_CHUNKS=Array.from({length:14},(_,i)=>`./data/catalogue/chunk-${String(i+1).padStart(2,'0')}.json`);
const PRECACHE=[
  './library.html','./reader.html','./editorial.html','./feature.html','./children.html','./children-stories.html','./children-animated.html','./family.html','./people.html','./person.html','./media.html','./manifest.webmanifest',
  './assets/bookstore.css','./assets/bookstore-published.css','./assets/library-extended.css','./assets/tarjma-fonts.css','./assets/site-professional.css','./assets/prophet-bookreader.css','./assets/editorial-public.css','./assets/family.css','./assets/people.css','./assets/media-library.css','./assets/children-stories.css','./assets/children-animated.css',
  './assets/catalogue-restore.js','./assets/bookstore.js','./assets/library-extended.js','./assets/reader-route.js','./assets/prophet-bookreader.js','./assets/editorial-public.js','./assets/family.js','./assets/people.js','./assets/media-library.js','./assets/children-stories.js','./assets/children-animated.js','./assets/universal-player.js','./assets/api.js',
  './data/reader_config.json','./data/published_user_books.json','./data/user_ingested_books.json','./data/generated_epubs.json','./data/imported_media.json','./data/people.json','./data/family_people.json','./data/family_biographies.json',
  './data/catalogue/manifest.json','./data/catalogue/professional_catalogue.json.gz.b64','./data/catalogue/professional_audit.json','./data/catalogue/disputed_attributions.json',...CATALOGUE_CHUNKS,
  './data/children/stories/manifest.json','./data/children/animated/manifest.json','./data/children/animated/index.json','./data/children/animated/status.json',
  './data/editorial/publication_manifest.json','./data/editorial/publication_supplement.json','./data/editorial/source_extract_100_audit.json','./data/editorial/source_extract_500_drive_audit.json','./data/editorial_sections.json','./private/acquisition_candidates.json'
];
self.addEventListener('install',event=>{event.waitUntil(caches.open(CACHE).then(cache=>Promise.allSettled(PRECACHE.map(asset=>cache.add(asset)))).then(()=>self.skipWaiting()))});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim()))});
const NETWORK_FIRST=new Set([
  '/library.html','/reader.html','/editorial.html','/feature.html','/children.html','/children-stories.html','/children-animated.html','/family.html','/people.html','/person.html','/media.html',
  '/assets/bookstore.js','/assets/bookstore.css','/assets/bookstore-published.css','/assets/catalogue-restore.js','/assets/library-extended.js','/assets/library-extended.css','/assets/tarjma-fonts.css','/assets/site-professional.css',
  '/assets/reader-route.js','/assets/prophet-bookreader.js','/assets/prophet-bookreader.css','/assets/editorial-public.js','/assets/editorial-public.css','/assets/family.js','/assets/family.css','/assets/people.js','/assets/people.css','/assets/media-library.js','/assets/media-library.css','/assets/children-stories.js','/assets/children-stories.css','/assets/children-animated.js','/assets/children-animated.css','/assets/universal-player.js',
  '/data/reader_config.json','/data/published_user_books.json','/data/user_ingested_books.json','/data/generated_epubs.json','/data/imported_media.json','/data/people.json','/data/family_people.json','/data/family_biographies.json',
  '/data/catalogue/manifest.json','/data/catalogue/professional_catalogue.json.gz.b64','/data/catalogue/professional_audit.json','/data/catalogue/disputed_attributions.json',
  '/data/children/animated/manifest.json','/data/children/animated/index.json','/data/children/animated/status.json',
  '/data/editorial/publication_manifest.json','/data/editorial/publication_supplement.json','/data/editorial/source_extract_100_audit.json','/data/editorial/source_extract_500_drive_audit.json','/data/editorial_sections.json'
]);
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET')return;
  const url=new URL(event.request.url);
  if(url.origin!==self.location.origin||url.pathname.startsWith('/api/'))return;
  const editorialBatch=/^\/data\/editorial\/drafts\/\d{4}-\d{2}-\d{2}\/batch-\d+\.json$/.test(url.pathname);
  const catalogueChunk=/^\/data\/catalogue\/chunk-\d{2}\.json$/.test(url.pathname);
  const animatedStory=/^\/data\/children\/animated\/age-(5-7|8-10|11-13|14-16)\/animated-story-\d{3}\.json$/.test(url.pathname);
  if(NETWORK_FIRST.has(url.pathname)||editorialBatch||catalogueChunk||animatedStory){
    event.respondWith(fetch(event.request,{cache:'no-store'}).then(response=>{if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy))}return response}).catch(async()=>await caches.match(event.request)||Response.error()));return;
  }
  event.respondWith(caches.match(event.request).then(async cached=>{if(cached)return cached;try{const response=await fetch(event.request);if(response.ok){const copy=response.clone();caches.open(CACHE).then(cache=>cache.put(event.request,copy))}return response}catch(_err){return Response.error()}}));
});
