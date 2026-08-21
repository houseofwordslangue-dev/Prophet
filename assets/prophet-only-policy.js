(function(){
'use strict';
const PROPHET_ONLY=new Set(['light','prophet','messenger','human','mercy']);
const FALLBACK_SECTION='sources';
const FALLBACK_SUBSECTION='research';
const MARKERS=[
 /محمد/u,/رسول الله/u,/النبي محمد/u,/المصطفى/u,/المحمدية/u,/السيرة النبوية/u,/الشمائل النبوية/u,
 /\bMuhammad\b/i,/\bMahomet\b/i,/Prophet Muhammad/i,/Messenger of (?:God|Allah)/i,
 /Prophète Muhammad/i,/Messager de (?:Dieu|Allah)/i
];
function textOf(d){
 const ps=(d&&d.paragraphs||[]).map(p=>typeof p==='string'?p:(p&&p.text)||'').join(' ');
 return String((d&&d.title)||'')+' '+ps;
}
function explicitScope(d){return String((d&&d.subjectScope)||'').trim().toLowerCase()}
function isProphetSpecific(d){
 const scope=explicitScope(d);
 if(scope==='prophet-muhammad'||scope==='prophet-muhammad-only')return true;
 if(scope&&scope!=='prophet-muhammad'&&scope!=='prophet-muhammad-only')return false;
 const text=textOf(d);
 return MARKERS.some(r=>r.test(text));
}
function enforceDraft(d){
 if(!d||typeof d!=='object'||!PROPHET_ONLY.has(String(d.section||'')))return d;
 if(isProphetSpecific(d))return {...d,subjectScope:'prophet-muhammad',prophetOnlyValidated:true};
 return {...d,
   reclassifiedFrom:{section:d.section,subsection:d.subsection},
   section:FALLBACK_SECTION,
   subsection:FALLBACK_SUBSECTION,
   sections:[FALLBACK_SECTION+'/'+FALLBACK_SUBSECTION],
   canonicalEditorialSlot:false,
   prophetOnlyValidated:false,
   prophetOnlyPolicyAction:'RECLASSIFIED_OUT_OF_PROPHET_ONLY_SECTION',
   prophetOnlyPolicyReason:'Primary text does not contain a direct Prophet-Muhammad marker and no explicit subjectScope=prophet-muhammad was supplied.'
 };
}
function transformJson(data){
 if(!data||typeof data!=='object')return data;
 if(Array.isArray(data))return data.map(transformJson);
 if(Array.isArray(data.drafts))return {...data,drafts:data.drafts.map(enforceDraft)};
 return data;
}
const nativeFetch=window.fetch.bind(window);
window.fetch=async function(input,init){
 const res=await nativeFetch(input,init);
 let url='';try{url=typeof input==='string'?input:(input&&input.url)||''}catch(e){}
 if(!/\.json(?:\?|$)/i.test(url))return res;
 try{
   const clone=res.clone(),data=await clone.json();
   if(!data||(!Array.isArray(data.drafts)&&!Array.isArray(data)))return res;
   const body=JSON.stringify(transformJson(data));
   const headers=new Headers(res.headers);headers.set('content-type','application/json; charset=utf-8');
   return new Response(body,{status:res.status,statusText:res.statusText,headers});
 }catch(e){return res}
};
window.ProphetOnlyPolicy={prophetOnlySections:[...PROPHET_ONLY],isProphetSpecific,enforceDraft};
})();
