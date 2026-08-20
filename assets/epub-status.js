(function(){'use strict';
let manifest=new Map();
function label(item){if(item.mode==='cover-only')return 'EPUB — غلاف فقط';if(item.mode==='reflowable-text'||item.mode==='merged-reflowable')return 'EPUB — نص مرن';return 'EPUB — صفحات محفوظة'}
function annotate(){
  document.querySelectorAll('.book-card').forEach(card=>{
    const open=card.querySelector('[data-open]');if(!open)return;
    const item=manifest.get(String(open.dataset.open));if(!item)return;
    const badges=card.querySelector('.badges');if(badges&&!badges.querySelector('[data-epub-badge]')){
      const b=document.createElement('span');b.className='badge on';b.dataset.epubBadge='1';b.textContent=label(item);badges.appendChild(b);
    }
  });
}
function annotateDialog(id){
  const item=manifest.get(String(id));if(!item)return;
  setTimeout(()=>{
    const box=document.querySelector('#dialogBody .dialog-details');if(!box||box.querySelector('[data-epub-detail]'))return;
    const span=document.createElement('span');span.dataset.epubDetail='1';span.innerHTML='<b>EPUB:</b> '+label(item)+' — محفوظ في مكتبة المشروع';box.appendChild(span);
  },0);
}
fetch('data/generated_epubs.json',{cache:'no-store'}).then(r=>r.ok?r.json():{items:[]}).then(j=>{
  (j.items||[]).forEach(x=>manifest.set(String(x.id),x));annotate();
  new MutationObserver(annotate).observe(document.getElementById('bookGrid'),{childList:true,subtree:true});
}).catch(()=>{});
document.addEventListener('click',e=>{const o=e.target.closest('[data-open]');if(o)annotateDialog(o.dataset.open)});
})();
