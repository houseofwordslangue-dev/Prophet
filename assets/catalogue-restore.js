(function(){
'use strict';
const nativeFetch=window.fetch.bind(window);
const MANIFEST='data/catalogue/manifest.json';
const OLD_SCHEMA=['id','entryNumber','category','titleAr','title','authorAr','author','kind','rightsStatus','verificationStatus','availabilityStatus','modesCsv','verifiedSource','editionNoteAr','ingestionStatus','century','language','publicationYear'];
const FALLBACK_CATEGORY={research:'البحث والدراسات'};
const csv=v=>String(v||'').split(',').map(s=>s.trim()).filter(Boolean);
const urlOrBlank=v=>{const s=String(v||'').trim();return /^https?:\/\//i.test(s)?s:''};
function asLanguage(v,titleAr){const s=String(v||'').trim().toLowerCase();if(['ar','arabic','العربية'].includes(s))return'ar';if(['en','english','الإنجليزية'].includes(s))return'en';if(['fr','french','الفرنسية'].includes(s))return'fr';return titleAr?'ar':''}
function bool(v){return v===true||['true','1','yes'].includes(String(v||'').toLowerCase())}
function professionalLabel(x){if(x.localAssetStatus)return'سجل مهني — أصل محلي موثّق';if(x.accessResolutionStatus==='EXACT_SOURCE_REGISTERED')return'سجل مهني — مصدر محدد';if(x.bibliographicStatus==='RESEARCH_PENDING')return'سجل مهني — التحقق الببليوغرافي مستمر';return'سجل ببليوغرافي مهني'}
function professionalNote(x){return [x.publicNotes,x.blockerAr].map(v=>String(v||'').trim()).filter(Boolean).join(' — ')}
function unpackProfessional(row,schema,categories){
 const x={};schema.forEach((k,i)=>x[k]=row[i]??'');
 const categoryAr=x.categoryAr||(categories.get(x.category)||{}).ar||FALLBACK_CATEGORY[x.category]||x.category||'المصادر';
 return {id:String(x.id),workId:String(x.id),entryNumber:x.entryNumber||'',category:x.category||'',categoryAr,
  titleAr:x.titleAr||'',titleOriginal:x.originalTitle||x.titleRomanized||x.titleAr||'',titleEn:x.titleRomanized||'',titleRomanized:x.titleRomanized||'',
  authorAr:x.authorAr||'',author:x.authorAr||x.authorRomanized||'',authorRomanized:x.authorRomanized||'',authorDates:x.authorDates||'',description:x.description||'',
  language:asLanguage(x.language,x.titleAr),languageOriginal:x.language||'',format:x.kind||'record',kind:x.kind||'record',workDate:x.workDate||'',centuryHijri:x.century||'',
  editionAr:x.edition||'',editorAr:x.editor||'',publisherAr:x.publisher||'',publicationYear:x.publicationYear||'',volume:x.volume||'',pages:x.page||'',isbn:x.isbn||'',doi:x.doi||'',institution:x.institution||'',manuscriptShelfmark:x.manuscriptShelfmark||'',
  rightsStatus:x.rightsStatus||'unknown',verificationStatus:x.verificationStatus||'',availabilityStatus:x.availabilityStatus||'',provenanceGroup:x.provenanceGroup||'',provenanceLabel:x.provenanceLabel||'',confidenceLevel:x.confidenceLevel||'',sourceType:x.sourceType||'',ingestionStatus:x.ingestionStatus||'',blockerAr:x.blockerAr||'',eligibleForFullTextCopy:bool(x.eligibleForFullTextCopy),
  sourceUrl:urlOrBlank(x.exactSourceUrl),sourceDiscoveryUrl:urlOrBlank(x.sourceDiscoveryUrl),archiveIdentifier:x.archiveIdentifier||'',localAssetStatus:x.localAssetStatus||'',heritageScope:x.heritageScope||'',moroccanHeritage:x.moroccanHeritage||'',retrievalDate:x.retrievalDate||'',
  recordLevel:x.recordLevel||'work',bibliographicStatus:x.bibliographicStatus||'RESEARCH_PENDING',accessResolutionStatus:x.accessResolutionStatus||'SOURCE_RESEARCH_PENDING',manifestationStatus:x.manifestationStatus||'NOT_APPLICABLE',identityMissing:csv(x.identityMissingCsv),manifestationMissing:csv(x.manifestationMissingCsv),
  subjects:[categoryAr],siteSections:[categoryAr],sourceRepository:'الفهرس المرجعي المهني للمشروع',publicationStatus:'restored-professional-catalogue',publicationLabelAr:professionalLabel(x),publicationNoteAr:professionalNote(x),capabilities:{readable:false,searchable:false,listenable:false,watchable:false},restoredCatalogue:true,professionalCatalogue:true};
}
function unpackLegacy(row,categories){
 const x={};OLD_SCHEMA.forEach((k,i)=>x[k]=row[i]??'');const categoryAr=(categories.get(x.category)||{}).ar||FALLBACK_CATEGORY[x.category]||x.category||'المصادر';
 return {id:String(x.id),workId:String(x.id),entryNumber:x.entryNumber||'',category:x.category||'',categoryAr,titleAr:x.titleAr||'',titleOriginal:x.title||x.titleAr||'',titleEn:x.title||'',authorAr:x.authorAr||'',author:x.authorAr||x.author||'',language:asLanguage(x.language,x.titleAr),format:x.kind||'record',kind:x.kind||'record',rightsStatus:x.rightsStatus||'unknown',verificationStatus:x.verificationStatus||'',availabilityStatus:x.availabilityStatus||'',ingestionStatus:x.ingestionStatus||'',subjects:[categoryAr],siteSections:[categoryAr],sourceRepository:'الفهرس المرجعي الكامل المستعاد',sourceUrl:urlOrBlank(x.verifiedSource),publicationStatus:'restored-catalogue',publicationLabelAr:'فهرس مرجعي مستعاد',publicationNoteAr:x.editionNoteAr||'',centuryHijri:x.century||'',publicationYear:x.publicationYear||'',bibliographicStatus:'RESEARCH_PENDING',accessResolutionStatus:'SOURCE_RESEARCH_PENDING',recordLevel:'work',manifestationStatus:'NOT_APPLICABLE',capabilities:{readable:false,searchable:false,listenable:false,watchable:false},restoredCatalogue:true};
}
async function gunzipBase64(text){
 if(typeof DecompressionStream==='undefined')throw new Error('DecompressionStream unavailable');
 const clean=String(text||'').replace(/\s+/g,'');const binary=atob(clean);const bytes=new Uint8Array(binary.length);for(let i=0;i<binary.length;i++)bytes[i]=binary.charCodeAt(i);
 const stream=new Blob([bytes]).stream().pipeThrough(new DecompressionStream('gzip'));return JSON.parse(await new Response(stream).text());
}
async function loadRestored(){
 const mr=await nativeFetch(MANIFEST,{cache:'no-store'});if(!mr.ok)throw new Error('catalogue manifest unavailable');const manifest=await mr.json();const categories=new Map((manifest.categories||[]).map(x=>[x.id,x]));let items,mode='professional';
 try{const r=await nativeFetch(manifest.compressedPayload,{cache:'no-store'});if(!r.ok)throw new Error('professional payload unavailable');const payload=await gunzipBase64(await r.text());const schema=payload.schema||manifest.schema||[];if((payload.items||[]).length!==Number(manifest.baselineCount))throw new Error('professional catalogue count mismatch');items=(payload.items||[]).map(row=>unpackProfessional(row,schema,categories));}
 catch(err){console.warn('[catalogue-restore] professional payload fallback:',err);mode='legacy-fallback';const chunks=manifest.fallbackChunks||manifest.chunks||[];const groups=await Promise.all(chunks.map(async c=>{const r=await nativeFetch(c.path,{cache:'no-store'});if(!r.ok)throw new Error('fallback unavailable');return (await r.json()).items||[]}));items=groups.flat().map(row=>unpackLegacy(row,categories));}
 const ids=new Set(items.map(x=>x.id));window.__restoredLibraryMeta={...manifest,loadedCount:items.length,uniqueBaselineIds:ids.size,loadMode:mode};return items;
}
function mergeLive(restored,live){
 const byWork=new Map(restored.map(x=>[String(x.workId||x.id),{...x}]));const extras=[];
 for(const raw of live||[]){const x={...raw};const wid=String(x.workId||'');if(wid&&byWork.has(wid)){const base=byWork.get(wid);byWork.set(wid,{...base,...x,id:base.id,workId:wid,titleAr:x.titleAr||base.titleAr,titleOriginal:x.titleOriginal||base.titleOriginal,author:x.author||base.author,subjects:(x.subjects&&x.subjects.length)?x.subjects:base.subjects,siteSections:(x.siteSections&&x.siteSections.length)?x.siteSections:base.siteSections,publicationStatus:'locally-ingested',publicationLabelAr:'متاح محليًا',publicationNoteAr:'تم تنزيل نسخة محلية موثقة وإتاحتها عبر القارئ الداخلي.',restoredCatalogue:true,professionalCatalogue:!!base.professionalCatalogue});}else extras.push(x);}
 return [...byWork.values(),...extras];
}
window.__restoredLibraryPromise=loadRestored();
window.fetch=async function(input,init){
 const url=typeof input==='string'?input:(input&&input.url)||'';
 if(/(?:^|\/)data\/ingested_library\.json(?:\?|$)/.test(url)){
  try{
   const restored=await window.__restoredLibraryPromise;let live=[];
   try{const rr=await nativeFetch(input,init);if(rr.ok){const j=await rr.json();live=j.items||[]}}catch(_){live=[]}
   const items=mergeLive(restored,live);window.__restoredLibraryMeta={...(window.__restoredLibraryMeta||{}),liveIngestedCount:live.length,combinedCount:items.length};
   return new Response(JSON.stringify({version:'professional-enrichment-v2+live-ingestion',count:items.length,liveIngestedCount:live.length,items}),{status:200,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}});
  }catch(err){console.error('[catalogue-restore]',err);return nativeFetch(input,init)}
 }
 return nativeFetch(input,init);
};
})();
