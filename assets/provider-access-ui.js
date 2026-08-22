/* GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md */
(function(){
'use strict';
const MAP_URL='data/provider_access.json';
const PUBLIC_URL='data/public_catalog_all.generated.json';
const CHUNKS=Array.from({length:14},(_,i)=>`data/catalogue/chunk-${String(i+1).padStart(2,'0')}.json`);
let byId=new Map();
function archiveUrl(u){
  try{const x=new URL(String(u||''),location.href);return /(^|\.)archive\.org$/i.test(x.hostname)?x.href:''}catch(_){return''}
}
function deriveArchiveId(u){
  try{const x=new URL(u);const p=x.pathname.split('/').filter(Boolean);const i=p.findIndex(v=>['details','download','stream','embed'].includes(v));return i>=0&&p[i+1]?decodeURIComponent(p[i+1]):''}catch(_){return''}
}
function labelFor(x){return ['borrow-only','controlled-lending'].includes(String(x.accessMode||''))?'استعارة عبر المصدر':'عرض عبر أرشيف الإنترنت'}
function add(id,url,seed={}){
  id=String(id||'');url=archiveUrl(url);if(!id||!url)return;
  const old=byId.get(id)||{};
  byId.set(id,{...old,...seed,catalogueId:id,provider:'Internet Archive',providerUrl:url,archiveId:seed.archiveId||old.archiveId||deriveArchiveId(url),accessMode:seed.accessMode||old.accessMode||'external-provider'});
}
function decorateCard(card){
  const opener=card.querySelector('[data-open]');if(!opener)return;
  const id=String(opener.getAttribute('data-open')||'');const access=byId.get(id);if(!access||!access.providerUrl)return;
  const actions=card.querySelector('.actions');if(!actions||actions.querySelector('[data-provider-access]'))return;
  const a=document.createElement('a');a.href=access.providerUrl;a.target='_blank';a.rel='noopener noreferrer';a.dataset.providerAccess=id;a.className='provider-access-link';a.textContent=labelFor(access);a.setAttribute('aria-label',`${labelFor(access)} — ${access.provider||'المصدر'}`);actions.insertBefore(a,actions.firstChild);
}
function decorate(){document.querySelectorAll('.book-card').forEach(decorateCard)}
async function readJson(url){try{const r=await fetch(url,{cache:'no-store'});return r.ok?await r.json():{items:[]}}catch(_){return{items:[]}}}
async function init(){
  try{
    const [manual,pub,...chunks]=await Promise.all([readJson(MAP_URL),readJson(PUBLIC_URL),...CHUNKS.map(readJson)]);
    (manual.items||[]).forEach(x=>add(x.catalogueId||x.id,x.providerUrl,x));
    (pub.items||[]).forEach(x=>{const urls=[...(x.sources||[]),x.sourceUrl,x.readerUrl,x.downloadUrl].filter(Boolean);const u=urls.map(archiveUrl).find(Boolean);if(u)add(x.id||x.workId,u,{accessMode:x.accessMode||'external-provider'});});
    chunks.flatMap(j=>j.items||[]).forEach(r=>{if(!Array.isArray(r))return;const u=archiveUrl(r[12]);if(u)add(r[0],u,{title:r[3]||r[4]||''});});
    decorate();
    const grid=document.getElementById('bookGrid');if(grid)new MutationObserver(decorate).observe(grid,{childList:true,subtree:true});
    document.documentElement.dataset.archiveProviderCount=String(byId.size);
  }catch(e){console.error('provider access ui',e)}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
