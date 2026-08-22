/* GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md */
(function(){
'use strict';
const nativeFetch=window.fetch.bind(window);
const TARGET='data/ingested_library.json';
const chunkUrls=Array.from({length:14},(_,i)=>`data/catalogue/chunk-${String(i+1).padStart(2,'0')}.json`);
const escParam=v=>encodeURIComponent(String(v||''));
function compact(r){
  const id=String(r?.[0]||'');
  const category=String(r?.[2]||'غير مصنف');
  const titleAr=String(r?.[3]||'');
  const titleEn=String(r?.[4]||'');
  const author=String(r?.[5]||r?.[6]||'');
  const sourceUrl=String(r?.[12]||'');
  const state=String(r?.[14]||r?.[10]||'catalogued');
  return {id,workId:id,titleAr,titleOriginal:titleAr||titleEn,titleEn,author,language:/[\u0600-\u06ff]/.test(titleAr)?'ar':'en',subjects:[category],siteSections:[category],format:'catalogue',catalogueVisible:true,publicationLabelAr:state==='source-ready-limited'?'المصدر جاهز جزئياً':'مدرج في المكتبة',publicationNoteAr:String(r?.[13]||''),sourceUrl,capabilities:{readable:false,searchable:false,listenable:false,watchable:false}};
}
function overlayItem(x){
  const src=String((x.sources&&x.sources[0])||x.sourceUrl||'');
  const full=x.access==='PUBLIC_FULL_TEXT'&&!!src;
  const id=String(x.id||x.workId||'');
  const reader=full?`reader.html?id=${escParam(id)}&src=${escParam(src)}&title=${escParam(x.title||x.titleAr||'')}&return=${escParam('library.html')}`:'';
  const cap=x.capabilities||{};
  return {id,workId:id,titleAr:x.titleAr||x.title||'',titleOriginal:x.title||x.titleOriginal||'',titleEn:x.titleEn||'',author:x.author||x.authorAr||'',language:x.language||(/[\u0600-\u06ff]/.test(x.title||'')?'ar':'en'),subjects:[x.category||'غير مصنف'],siteSections:[x.category||'غير مصنف'],format:(x.formats&&x.formats[0])||x.format||'catalogue',catalogueVisible:true,access:x.access,state:x.state,publicationLabelAr:x.access==='PUBLIC_FULL_TEXT'?'نص كامل متاح':(x.state||'مدرج في المكتبة'),sourceUrl:src,readerUrl:reader,localUrl:reader,capabilities:{readable:full&&cap.read!==false,searchable:full&&cap.search!==false,listenable:full&&!!cap.listen,watchable:full&&!!cap.watch}};
}
async function build(original){
  const [overlay,...chunks]=await Promise.all([
    nativeFetch('data/public_catalog_all.generated.json',{cache:'no-store'}).then(r=>r.ok?r.json():{items:[]}).catch(()=>({items:[]})),
    ...chunkUrls.map(u=>nativeFetch(u,{cache:'no-store'}).then(r=>r.ok?r.json():{items:[]}).catch(()=>({items:[]})))
  ]);
  const m=new Map();
  (original.items||[]).forEach(x=>{const k=String(x.id||x.workId||'');if(k)m.set(k,x)});
  chunks.flatMap(j=>j.items||[]).map(compact).forEach(x=>{if(!x.id)return;const old=m.get(x.id)||{};m.set(x.id,{...x,...old,subjects:[...new Set([...(x.subjects||[]),...(old.subjects||[])])],siteSections:[...new Set([...(x.siteSections||[]),...(old.siteSections||[])])]})});
  (overlay.items||[]).map(overlayItem).forEach(x=>{if(!x.id)return;const old=m.get(x.id)||{};m.set(x.id,{...old,...x,subjects:[...new Set([...(old.subjects||[]),...(x.subjects||[])])],siteSections:[...new Set([...(old.siteSections||[]),...(x.siteSections||[])])]})});
  const items=[...m.values()].filter(x=>x.id||x.workId);
  return {...original,schema:'ingested-library-v3-plus-unified-bookstore-catalogue',count:items.length,items};
}
window.fetch=async function(input,init){
  const url=typeof input==='string'?input:(input&&input.url)||'';
  if(!url.endsWith(TARGET))return nativeFetch(input,init);
  const res=await nativeFetch(input,init);
  if(!res.ok)return res;
  try{
    const original=await res.clone().json();
    const merged=await build(original);
    return new Response(JSON.stringify(merged),{status:200,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}});
  }catch(e){console.error('bookstore catalogue bridge',e);return res}
};
})();
