(function(){
'use strict';
const nativeFetch=window.fetch.bind(window);
const MANIFEST='data/catalogue/manifest.json';
const FALLBACK_CATEGORY={research:'البحث والدراسات'};
function asLanguage(v,titleAr){
  const s=String(v||'').trim().toLowerCase();
  if(s==='ar'||s==='arabic'||s==='العربية')return'ar';
  if(s==='en'||s==='english'||s==='الإنجليزية')return'en';
  if(s==='fr'||s==='french'||s==='الفرنسية')return'fr';
  return titleAr?'ar':'en';
}
function urlOrBlank(v){const s=String(v||'').trim();return /^https?:\/\//i.test(s)?s:''}
function unpack(row,schema,categories){
  const x={};schema.forEach((key,i)=>x[key]=row[i]??'');
  const categoryAr=(categories.get(x.category)||{}).ar||FALLBACK_CATEGORY[x.category]||x.category||'المصادر';
  const sourceUrl=urlOrBlank(x.verifiedSource);
  return {
    id:String(x.id),workId:String(x.id),entryNumber:x.entryNumber||'',category:x.category||'',categoryAr,
    titleAr:x.titleAr||'',titleOriginal:x.title||x.titleAr||'',titleEn:x.title||'',authorAr:x.authorAr||'',author:x.authorAr||x.author||'',
    language:asLanguage(x.language,x.titleAr),format:x.kind||'book',kind:x.kind||'book',rightsStatus:x.rightsStatus||'unknown',
    verificationStatus:x.verificationStatus||'',availabilityStatus:x.availabilityStatus||'',ingestionStatus:x.ingestionStatus||'',
    subjects:[categoryAr],siteSections:[categoryAr],sourceRepository:'الفهرس المرجعي الكامل المستعاد',sourceUrl,
    publicationStatus:'restored-catalogue',publicationLabelAr:'فهرس مرجعي مستعاد',
    publicationNoteAr:x.editionNoteAr||'سجل ببليوغرافي مستعاد من الفهرس الكامل للمشروع. لا تُفعّل وظائف القراءة أو التنزيل إلا عند وجود أصل عام فعلي متاح للموقع.',
    centuryHijri:x.century||'',publicationYear:x.publicationYear||'',
    capabilities:{readable:false,searchable:false,listenable:false,watchable:false},restoredCatalogue:true
  };
}
async function loadRestored(){
  const mr=await nativeFetch(MANIFEST,{cache:'no-store'});if(!mr.ok)throw new Error('catalogue manifest unavailable');
  const manifest=await mr.json();const categories=new Map((manifest.categories||[]).map(x=>[x.id,x]));
  const results=await Promise.all((manifest.chunks||[]).map(async c=>{const r=await nativeFetch(c.path,{cache:'no-store'});if(!r.ok)throw new Error('catalogue chunk unavailable: '+c.path);const j=await r.json();return j.items||[]}));
  const rows=results.flat();
  if(rows.length!==Number(manifest.baselineCount))throw new Error('catalogue count mismatch: '+rows.length);
  const items=rows.map(r=>unpack(r,manifest.schema||[],categories));
  const ids=new Set(items.map(x=>x.id));if(ids.size!==items.length)throw new Error('duplicate restored catalogue ids');
  window.__restoredLibraryMeta={...manifest,loadedCount:items.length,uniqueBaselineIds:ids.size};
  return items;
}
window.__restoredLibraryPromise=loadRestored();
window.fetch=async function(input,init){
  const url=typeof input==='string'?input:(input&&input.url)||'';
  if(/(?:^|\/)data\/ingested_library\.json(?:\?|$)/.test(url)){
    try{
      const items=await window.__restoredLibraryPromise;
      return new Response(JSON.stringify({version:'restored-689-packed-v1',items}),{status:200,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}});
    }catch(err){console.error('[catalogue-restore]',err);return new Response('',{status:404,statusText:'Restored catalogue unavailable'});}
  }
  return nativeFetch(input,init);
};
})();
