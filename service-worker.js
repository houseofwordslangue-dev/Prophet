const CACHE='prophet-biography-v6-8-0-bookstore';
const ASSETS=[
'./','./index.html','./light.html','./prophet.html','./messenger.html','./human.html','./mercy.html','./family.html','./companions.html','./forums.html','./media.html',
'./quran.html','./hadith.html','./names.html','./daily-seerah.html','./latest.html','./ai-article.html',
'./collection.html','./library.html','./article.html','./timeline.html','./atlas.html','./editorial.html','./research.html','./account.html','./profile.html','./admin.html','./learn.html','./graph.html','./today.html','./workspace.html','./status.html','./privacy.html','./accessibility.html','./community-guidelines.html',
'./reference.html','./reader.html','./references.html','./assets/reference.js','./assets/reader.js','./assets/reader.css','./assets/universal-player.js','./assets/references.js','./assets/bookstore.js','./assets/bookstore.css',
'./assets/styles.css','./assets/names.js','./assets/fr-ui.js','./assets/app.js','./assets/api.js','./assets/knowledge.js','./assets/library.js','./assets/visuals.js','./assets/media.js','./assets/research.js','./assets/community.js','./assets/account.js','./assets/profile.js','./assets/admin.js','./assets/learning.js','./assets/graph.js','./assets/today.js','./assets/workspace.js','./assets/status.js','./assets/quran.js','./assets/hadith.js','./assets/seerah.js','./assets/latest.js','./assets/section-articles.js','./assets/home-articles.js','./assets/collection-article.js','./assets/ai-article.js','./assets/quoted-content.js',
'./assets/zellige-user-background.jpg','./assets/madinah-green-dome.png','./assets/logo.png'
];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
const NETWORK_FIRST=new Set(['/index.html','/assets/app.js','/assets/styles.css','/data/imported_media.json','/data/imported_quotes.json','/data/fr_generated.json','/data/quran_interpretive_overlay.json','/data/seerah_corpus.json','/data/ingested_library.json','/reference.html','/reader.html','/references.html','/library.html','/assets/reference.js','/assets/reader.js','/assets/reader.css','/assets/universal-player.js','/assets/references.js','/assets/bookstore.js','/assets/bookstore.css','/data/references.json']);
self.addEventListener('fetch',e=>{
  if(e.request.method!=='GET')return;
  const url=new URL(e.request.url);
  if(url.origin!==self.location.origin)return;
  if(url.pathname.startsWith('/api/'))return;
  if(NETWORK_FIRST.has(url.pathname)){
    e.respondWith(fetch(e.request,{cache:'no-store'}).then(resp=>{
      if(resp.ok){const copy=resp.clone();caches.open(CACHE).then(c=>c.put(e.request,copy))}
      return resp;
    }).catch(async()=>{
      const cached=await caches.match(e.request);
      return cached||Response.error();
    }));
    return;
  }
  e.respondWith(caches.match(e.request).then(async cached=>{
    if(cached)return cached;
    try{
      const resp=await fetch(e.request);
      if(resp.ok){const copy=resp.clone();caches.open(CACHE).then(c=>c.put(e.request,copy))}
      return resp;
    }catch(_err){
      if(e.request.mode==='navigate')return (await caches.match('./index.html'))||Response.error();
      return Response.error();
    }
  }));
});
