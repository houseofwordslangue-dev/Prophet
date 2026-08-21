(function(){'use strict';
const MANIFEST='data/real_asset_sources_20260821.json';
const driveView=id=>id?`https://drive.google.com/file/d/${encodeURIComponent(id)}/preview`:'';
function allDriveIds(d){return [d.completePdfId,d.pdfId,d.alternatePdfId,...(d.volumePdfIds||[])].filter(Boolean)}
function toLibrary(x){const d=x.drive||{};const driveAssets=allDriveIds(d).map(driveView);const preferred=driveAssets[0]||x.publicAsset||'';return {id:x.id,workId:x.id,titleAr:x.titleAr,author:x.authorAr,authorAr:x.authorAr,language:x.language||'ar',format:'pdf',subjects:[x.category].filter(Boolean),siteSections:x.siteSections||[x.category].filter(Boolean),readerUrl:`reader.html?id=${encodeURIComponent(x.id)}&src=${encodeURIComponent(preferred)}`,localUrl:preferred,sourceUrl:preferred,capabilities:x.capabilities||{},realAsset:true,publicDomain:!!x.publicDomain,driveAssetIds:d,sourceCandidates:[...driveAssets,x.publicAsset].filter(Boolean),publicationPolicy:'DRIVE_CONTENT_AUTHORIZED_FOR_PUBLICATION'};}
async function load(){try{const r=await fetch(MANIFEST,{cache:'no-store'});if(!r.ok)return;const j=await r.json();const items=(j.items||[]).map(toLibrary);window.ProphetRealAssets={items,manifest:j};document.dispatchEvent(new CustomEvent('prophet:real-assets',{detail:{items,manifest:j}}));}catch(e){console.warn('real assets manifest unavailable',e)}}
load();
})();