(function(){
'use strict';
const ROUTES={
  '20260820-light-verses':{section:'messenger',subsection:'verses'},
  '20260820-light-hadith':{section:'messenger',subsection:'seerah'},
  '20260820-light-righteous':{section:'prophet',subsection:'righteous'},
  '20260820-light-research':{section:'prophet',subsection:'research'}
};
function remapArticle(o){
  if(!o||typeof o!=='object'||Array.isArray(o))return o;
  if(o.section==='light'){
    const r=ROUTES[o.id]||{section:'prophet',subsection:o.subsection||'research'};
    o={...o,section:r.section,subsection:r.subsection,sections:[r.section+'/'+r.subsection],lightSectionReclassified:true,lightSectionPreviousSubsection:o.subsection||null};
  }else if(Array.isArray(o.sections)&&o.sections.some(x=>String(x).startsWith('light/'))){
    const r=ROUTES[o.id]||{section:o.section||'prophet',subsection:o.subsection||'research'};
    o={...o,section:r.section,subsection:r.subsection,sections:o.sections.map(x=>String(x).startsWith('light/')?r.section+'/'+r.subsection:x),lightSectionReclassified:true};
  }
  for(const [k,v] of Object.entries(o)){
    if(v&&typeof v==='object')o[k]=walk(v);
  }
  return o;
}
function walk(v){
  if(Array.isArray(v))return v.map(walk);
  if(v&&typeof v==='object')return remapArticle(v);
  return v;
}
const nativeFetch=window.fetch.bind(window);
window.fetch=async function(input,init){
  const response=await nativeFetch(input,init);
  try{
    const url=typeof input==='string'?input:(input&&input.url)||'';
    if(!/data\/editorial\/.*\.json(?:[?#]|$)/i.test(url))return response;
    const clone=response.clone();
    const data=walk(await clone.json());
    return new Response(JSON.stringify(data),{status:response.status,statusText:response.statusText,headers:response.headers});
  }catch(_){return response}
};
function keepEmptyFilter(){
  const q=new URLSearchParams(location.search);
  if(q.get('section')!=='light')return;
  const f=document.getElementById('sectionFilter');
  if(!f)return;
  let opt=[...f.options].find(o=>o.value==='light');
  if(!opt){opt=document.createElement('option');opt.value='light';opt.textContent='النور';f.appendChild(opt)}
  if(f.value!=='light'){f.value='light';f.dispatchEvent(new Event('change'))}
}
document.addEventListener('DOMContentLoaded',()=>{
  keepEmptyFilter();
  const mo=new MutationObserver(keepEmptyFilter);
  mo.observe(document.documentElement,{subtree:true,childList:true});
  setTimeout(()=>{keepEmptyFilter();mo.disconnect()},20000);
});
})();
