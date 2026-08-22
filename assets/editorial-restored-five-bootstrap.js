(function(){
'use strict';
const RESTORED_BATCH='data/editorial/drafts/2026-08-22/batch-restored-five-slots.json';
const RESTORED_IDS=[
 '20260820-messenger-righteous',
 '20260820-messenger-research',
 '20260820-human-verses',
 '20260820-media-videos',
 '20260820-media-lectures'
];
const nativeFetch=window.fetch.bind(window);
window.fetch=async function(input,init){
 const url=typeof input==='string'?input:(input&&input.url)||'';
 const response=await nativeFetch(input,init);
 if(!/data\/editorial\/publication_manifest\.json(?:[?#]|$)/.test(url))return response;
 try{
   const data=await response.clone().json();
   data.draftBatchPaths=Array.from(new Set([...(data.draftBatchPaths||[]),RESTORED_BATCH]));
   data.publishedIds=Array.from(new Set([...(data.publishedIds||[]),...RESTORED_IDS]));
   data.integrity={...(data.integrity||{}),restoredSourceBackedSlots:5};
   return new Response(JSON.stringify(data),{
     status:response.status,
     statusText:response.statusText,
     headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}
   });
 }catch(e){return response}
};
})();
