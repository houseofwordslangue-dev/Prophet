/* GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md */
(function(){
'use strict';
const MAP_URL='data/provider_access.json';
let byId=new Map();
const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function labelFor(x){return ['borrow-only','controlled-lending'].includes(String(x.accessMode||''))?'استعارة عبر المصدر':'عرض عبر المصدر'}
function decorateCard(card){
  const opener=card.querySelector('[data-open]');
  if(!opener)return;
  const id=String(opener.getAttribute('data-open')||'');
  const access=byId.get(id);
  if(!access||!access.providerUrl)return;
  const actions=card.querySelector('.actions');
  if(!actions||actions.querySelector('[data-provider-access]'))return;
  const a=document.createElement('a');
  a.href=access.providerUrl;
  a.target='_blank';
  a.rel='noopener noreferrer';
  a.dataset.providerAccess=id;
  a.className='provider-access-link';
  a.textContent=labelFor(access);
  a.setAttribute('aria-label',`${labelFor(access)} — ${access.provider||'المصدر'}`);
  actions.insertBefore(a,actions.firstChild);
}
function decorate(){document.querySelectorAll('.book-card').forEach(decorateCard)}
async function init(){
  try{
    const r=await fetch(MAP_URL,{cache:'no-store'});
    if(!r.ok)return;
    const j=await r.json();
    byId=new Map((j.items||[]).filter(x=>x.catalogueId&&x.providerUrl).map(x=>[String(x.catalogueId),x]));
    decorate();
    const grid=document.getElementById('bookGrid');
    if(grid)new MutationObserver(decorate).observe(grid,{childList:true,subtree:true});
  }catch(e){console.error('provider access ui',e)}
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
