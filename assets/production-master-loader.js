(function(){'use strict';
const MASTER='data/production_manifest_all.json';
async function json(path){try{const r=await fetch(path,{cache:'no-store'});return r.ok?await r.json():null}catch(_){return null}}
function countItems(j){if(!j)return 0;if(Array.isArray(j.items))return j.items.length;if(Array.isArray(j.sources))return j.sources.length;if(Number.isFinite(Number(j.count)))return Number(j.count);return 0}
function idOf(x){return String(x&&((x.id??x.workId??x.slug))||'')}
async function load(){const m=await json(MASTER);if(!m)return;const sourceRows=await Promise.all((m.sources||[]).map(async s=>({source:s,data:await json(s.manifest)})));const unique=new Map();for(const row of sourceRows){const s=row.source,j=row.data;if(!j)continue;if(s.id==='drive-books')continue;for(const x of (j.items||[])){const id=idOf(x);if(id&&!unique.has(id))unique.set(id,x)}}
const drive=window.ProphetDriveProduction?.items||[];drive.forEach(x=>{const id=idOf(x);if(id&&!unique.has(id))unique.set(id,x)});
const detail={manifest:m,sources:sourceRows.map(r=>({id:r.source.id,loaded:!!r.data,count:countItems(r.data)})),knownUniqueLibraryWorks:Math.max(Number(m.knownPublishedWorkCount||0),[...unique.keys()].filter(Boolean).length),runtimeUniqueRecords:unique.size};window.ProphetProductionMaster=detail;document.dispatchEvent(new CustomEvent('prophet:production-master',{detail}));
const stat=document.getElementById('statBooks');if(stat&&Number(m.knownPublishedWorkCount)>0){const current=Number(String(stat.textContent||'').replace(/[^0-9]/g,''))||0;const n=Math.max(current,Number(m.knownPublishedWorkCount));stat.textContent=new Intl.NumberFormat(document.documentElement.lang||'ar').format(n)}
const count=document.getElementById('resultCount');if(count&&/تحميل|loading/i.test(count.textContent||''))count.textContent=`${new Intl.NumberFormat(document.documentElement.lang||'ar').format(Number(m.knownPublishedWorkCount||0))} سجل مكتبي منشور في الفهرس الموحد`;
}
document.addEventListener('prophet:drive-production',()=>setTimeout(load,0),{once:true});document.addEventListener('DOMContentLoaded',()=>setTimeout(load,80));
})();