(function(){
'use strict';
const CFG='data/editorial/empty_section_five_articles.json';
const q=new URLSearchParams(location.search);
const section=q.get('section')||'';
const subsection=q.get('subsection')||'';
if(!section||!subsection)return;
let cfg=null,applying=false,lastSig='';
const esc=s=>String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot',"'":'&#39;'}[c]));
function cardId(card){
 const a=card.querySelector('a[href*="feature.html?id="]');
 if(!a)return '';
 try{return new URL(a.getAttribute('href'),location.href).searchParams.get('id')||''}catch(e){return ''}
}
function signature(feed){return [...feed.querySelectorAll('.ep-card')].map(cardId).filter(Boolean).join('|')}
function apply(){
 if(applying||!cfg)return;
 const feed=document.getElementById('articleFeed');
 if(!feed)return;
 const cards=[...feed.querySelectorAll('.ep-card')];
 if(!cards.length)return;
 const sig=signature(feed);
 if(sig===lastSig&&cards.length===cfg.articleIds.length)return;
 const by=new Map(cards.map(c=>[cardId(c),c]).filter(x=>x[0]));
 const selected=cfg.articleIds.map(id=>by.get(id)).filter(Boolean);
 if(selected.length!==cfg.articleIds.length)return;
 applying=true;
 const sectionLabel=cfg.section==='prophetic-family'?'العائلة النبوية':'الصحابة';
 const frag=document.createDocumentFragment();
 selected.forEach(card=>{
   const clone=card.cloneNode(true);
   clone.dataset.presentationSection=cfg.section;
   clone.dataset.presentationSubsection=cfg.subsection;
   const meta=clone.querySelector('.meta');
   if(meta)meta.textContent=sectionLabel+' · '+cfg.labelAr;
   frag.appendChild(clone);
 });
 feed.replaceChildren(frag);
 const status=document.getElementById('publicationStatus');
 if(status)status.textContent='5 مواد';
 lastSig=signature(feed);
 applying=false;
}
fetch(CFG,{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject(new Error(String(r.status)))).then(j=>{
 cfg=(j.sections||[]).find(x=>x.section===section&&x.subsection===subsection)||null;
 if(!cfg)return;
 const obs=new MutationObserver(()=>setTimeout(apply,0));
 const feed=document.getElementById('articleFeed');
 if(feed)obs.observe(feed,{childList:true,subtree:false});
 [0,100,300,700,1500,3000].forEach(ms=>setTimeout(apply,ms));
}).catch(()=>{});
})();
