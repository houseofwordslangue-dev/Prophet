(function(){
'use strict';
const nativeFetch=window.fetch.bind(window);
const MANIFEST='data/catalogue/manifest.json';
const OLD_SCHEMA=['id','entryNumber','category','titleAr','title','authorAr','author','kind','rightsStatus','verificationStatus','availabilityStatus','modesCsv','verifiedSource','editionNoteAr','ingestionStatus','century','language','publicationYear'];
const FALLBACK_CATEGORY={research:'البحث والدراسات'};
function asLanguage(v,titleAr){
  const s=String(v||'').trim().toLowerCase();
  if(s==='ar'||s==='arabic'||s==='العربية')return'ar';
  if(s==='en'||s==='english'||s==='الإنجليزية')return'en';
  if(s==='fr'||s==='french'||s==='الفرنسية')return'fr';
  return titleAr?'ar':'';
}
function urlOrBlank(v){const s=String(v||'').trim();return /^https?:\/\//i.test(s)?s:''}
function csv(v){return String(v||'').split(',').map(s=>s.trim()).filter(Boolean)}
function professionalLabel(x){
  if(x.bibliographicStatus==='RESEARCH_PENDING')return'سجل مهني — التحقق الببليوغرافي مستمر';
  if(x.localAssetStatus)return'سجل مهني — أصل محلي موثّق';
  if(x.accessResolutionStatus==='EXACT_SOURCE_REGISTERED')return'سجل مهني — مصدر محدد';
  if(x.accessResolutionStatus==='DISCOVERY_SOURCE_REGISTERED')return'سجل مهني — مصدر اكتشاف مسجل';
  return'سجل ببليوغرافي مهني';
}
function professionalNote(x){
  const notes=[x.publicNotes,x.blockerAr].map(v=>String(v||'').trim()).filter(Boolean);
  if(!notes.length&&x.bibliographicStatus==='RESEARCH_PENDING')notes.push('هوية السجل محفوظة، وتبقى بعض بيانات الإسناد الببليوغرافي قيد التحقق من مصدر موثوق.');
  return notes.join(' — ');
}
function unpackProfessional(row,schema,categories){
  const x={};schema.forEach((key,i)=>x[key]=row[i]??'');
  const categoryAr=x.categoryAr||(categories.get(x.category)||{}).ar||FALLBACK_CATEGORY[x.category]||x.category||'المصادر';
  const exactSource=urlOrBlank(x.exactSourceUrl);
  return {
    id:String(x.id),workId:String(x.id),entryNumber:x.entryNumber||'',category:x.category||'',categoryAr,
    titleAr:x.titleAr||'',titleOriginal:x.originalTitle||x.titleRomanized||x.titleAr||'',titleEn:x.titleRomanized||'',titleRomanized:x.titleRomanized||'',
    authorAr:x.authorAr||'',author:x.authorAr||x.authorRomanized||'',authorRomanized:x.authorRomanized||'',authorDates:x.authorDates||'',
    description:x.description||'',language:asLanguage(x.language,x.titleAr),languageOriginal:x.language||'',format:x.kind||'record',kind:x.kind||'record',
    workDate:x.workDate||'',centuryHijri:x.century||'',editionAr:x.edition||'',editorAr:x.editor||'',publisherAr:x.publisher||'',
    publicationYear:x.publicationYear||'',volume:x.volume||'',pages:x.page||'',isbn:x.isbn||'',doi:x.doi||'',institution:x.institution||'',manuscriptShelfmark:x.manuscriptShelfmark||'',
    rightsStatus:x.rightsStatus||'unknown',verificationStatus:x.verificationStatus||'',availabilityStatus:x.availabilityStatus||'',provenanceGroup:x.provenanceGroup||'',provenanceLabel:x.provenanceLabel||'',
    confidenceLevel:x.confidenceLevel||'',sourceType:x.sourceType||'',ingestionStatus:x.ingestionStatus||'',blockerAr:x.blockerAr||'',eligibleForFullTextCopy:String(x.eligibleForFullTextCopy||'').toLowerCase()==='true',
    sourceUrl:exactSource,sourceDiscoveryUrl:urlOrBlank(x.sourceDiscoveryUrl),archiveIdentifier:x.archiveIdentifier||'',localAssetStatus:x.localAssetStatus||'',heritageScope:x.heritageScope||'',moroccanHeritage:x.moroccanHeritage||'',retrievalDate:x.retrievalDate||'',
    recordLevel:x.recordLevel||'work',bibliographicStatus:x.bibliographicStatus||'RESEARCH_PENDING',accessResolutionStatus:x.accessResolutionStatus||'SOURCE_RESEARCH_PENDING',manifestationStatus:x.manifestationStatus||'NOT_APPLICABLE',
    identityMissing:csv(x.identityMissingCsv),manifestationMissing:csv(x.manifestationMissingCsv),subjects:[categoryAr],siteSections:[categoryAr],
    sourceRepository:'الفهرس المرجعي المهني للمشروع',publicationStatus:'restored-professional-catalogue',publicationLabelAr:professionalLabel(x),publicationNoteAr:professionalNote(x),
    capabilities:{readable:false,searchable:false,listenable:false,watchable:false},restoredCatalogue:true,professionalCatalogue:true
  };
}
function unpackLegacy(row,schema,categories){
  const x={};schema.forEach((key,i)=>x[key]=row[i]??'');
  const categoryAr=(categories.get(x.category)||{}).ar||FALLBACK_CATEGORY[x.category]||x.category||'المصادر';
  return {
    id:String(x.id),workId:String(x.id),entryNumber:x.entryNumber||'',category:x.category||'',categoryAr,
    titleAr:x.titleAr||'',titleOriginal:x.title||x.titleAr||'',titleEn:x.title||'',authorAr:x.authorAr||'',author:x.authorAr||x.author||'',
    language:asLanguage(x.language,x.titleAr),format:x.kind||'record',kind:x.kind||'record',rightsStatus:x.rightsStatus||'unknown',verificationStatus:x.verificationStatus||'',availabilityStatus:x.availabilityStatus||'',ingestionStatus:x.ingestionStatus||'',
    subjects:[categoryAr],siteSections:[categoryAr],sourceRepository:'الفهرس المرجعي الكامل المستعاد',sourceUrl:urlOrBlank(x.verifiedSource),publicationStatus:'restored-catalogue',publicationLabelAr:'فهرس مرجعي مستعاد',publicationNoteAr:x.editionNoteAr||'سجل مستعاد؛ بعض بياناته في طبقة التوافق القديمة.',centuryHijri:x.century||'',publicationYear:x.publicationYear||'',
    bibliographicStatus:'RESEARCH_PENDING',accessResolutionStatus:'SOURCE_RESEARCH_PENDING',recordLevel:'work',manifestationStatus:'NOT_APPLICABLE',capabilities:{readable:false,searchable:false,listenable:false,watchable:false},restoredCatalogue:true
  };
}
async function gunzipBase64(text){
  if(typeof DecompressionStream==='undefined')throw new Error('DecompressionStream unavailable');
  const clean=String(text||'').replace(/\s+/g,'');
  const binary=atob(clean);const bytes=new Uint8Array(binary.length);for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
  const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));
  return JSON.parse(await new Response(stream).text());
}
async function loadProfessional(manifest,categories){
  const r=await nativeFetch(manifest.compressedPayload,{cache:'no-store'});if(!r.ok)throw new Error('professional catalogue payload unavailable');
  const payload=await gunzipBase64(await r.text());
  const schema=payload.schema||manifest.schema||[];const rows=payload.items||[];
  if(rows.length!==Number(manifest.baselineCount))throw new Error('professional catalogue count mismatch: '+rows.length);
  const items=rows.map(row=>unpackProfessional(row,schema,categories));
  const ids=new Set(items.map(x=>x.id));if(ids.size!==items.length)throw new Error('duplicate professional catalogue ids');
  return items;
}
async function loadLegacy(manifest,categories){
  const chunks=manifest.fallbackChunks||manifest.chunks||[];
  const results=await Promise.all(chunks.map(async c=>{const r=await nativeFetch(c.path,{cache:'no-store'});if(!r.ok)throw new Error('catalogue fallback unavailable: '+c.path);const j=await r.json();return j.items||[]}));
  const rows=results.flat();if(rows.length!==Number(manifest.baselineCount))throw new Error('catalogue fallback count mismatch: '+rows.length);
  return rows.map(r=>unpackLegacy(r,OLD_SCHEMA,categories));
}
async function loadRestored(){
  const mr=await nativeFetch(MANIFEST,{cache:'no-store'});if(!mr.ok)throw new Error('catalogue manifest unavailable');
  const manifest=await mr.json();const categories=new Map((manifest.categories||[]).map(x=>[x.id,x]));
  let items,mode='professional';
  try{items=await loadProfessional(manifest,categories)}catch(err){console.warn('[catalogue-restore] professional payload fallback:',err);items=await loadLegacy(manifest,categories);mode='legacy-fallback'}
  const ids=new Set(items.map(x=>x.id));window.__restoredLibraryMeta={...manifest,loadedCount:items.length,uniqueBaselineIds:ids.size,loadMode:mode};
  return items;
}
window.__restoredLibraryPromise=loadRestored();
window.fetch=async function(input,init){
  const url=typeof input==='string'?input:(input&&input.url)||'';
  if(/(?:^|\/)data\/ingested_library\.json(?:\?|$)/.test(url)){
    try{const items=await window.__restoredLibraryPromise;return new Response(JSON.stringify({version:'professional-enrichment-v2',items}),{status:200,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}})}
    catch(err){console.error('[catalogue-restore]',err);return new Response('',{status:404,statusText:'Professional catalogue unavailable'})}
  }
  return nativeFetch(input,init);
};
})();
