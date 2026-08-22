/*
 * Prophet Muhammad Site — BookReader integration
 * Integration module licensed under GNU AGPL-3.0-or-later.
 * Upstream engine: Internet Archive BookReader (AGPL-3.0).
 */
(function(){
'use strict';
const DEFAULT_CONFIG={engine:'Internet Archive BookReader',version:'5.0.0-116',fallbackVersion:'5.0.0-87',license:'AGPL-3.0',cdn:'https://cdn.jsdelivr.net/npm/@internetarchive/bookreader@{version}/BookReader/'};
const $=s=>document.querySelector(s);
const params=new URLSearchParams(location.search);
const state={item:null,config:DEFAULT_CONFIG,engineVersion:null,mode:null,bookReader:null};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const titleOf=x=>x?.titleAr||x?.titleOriginal||x?.titleEn||x?.titleFr||params.get('title')||'الكتاب';
const authorOf=x=>x?.author||x?.authorAr||'';
const idOf=x=>String(x?.id||x?.workId||'');
function setStatus(text,tone=''){const el=$('#readerStatus');if(!el)return;el.textContent=text;el.dataset.tone=tone}
function setLoading(show){const el=$('#readerLoading');if(el)el.hidden=!show}
function setMode(mode){state.mode=mode;document.body.dataset.readerMode=mode;['#bookReaderMode','#frameMode','#textMode','#readerUnavailable'].forEach(sel=>{const el=$(sel);if(el)el.hidden=true});const map={bookreader:'#bookReaderMode',frame:'#frameMode',text:'#textMode',unavailable:'#readerUnavailable'};if(map[mode]&&$(map[mode]))$(map[mode]).hidden=false}
function updateHeader(item){$('#readerTitle').textContent=titleOf(item);$('#readerAuthor').textContent=authorOf(item)||'مكتبة محمد ﷺ';document.title=titleOf(item)+' — القارئ';const meta=[];if(item?.pages)meta.push(`${item.pages} صفحة`);if(item?.language)meta.push(item.language==='ar'?'العربية':item.language);if(item?.editionAr)meta.push(item.editionAr);$('#readerMeta').textContent=meta.join(' · ');const back=params.get('return')||'library.html';$('#readerBack').href=back}
function archiveIdentifier(url){if(!url)return'';try{const u=new URL(url,location.href);if(!/(^|\.)archive\.org$/i.test(u.hostname))return'';const p=u.pathname.split('/').filter(Boolean);const i=p.findIndex(x=>['details','download','stream','embed'].includes(x));return i>=0&&p[i+1]?decodeURIComponent(p[i+1]):''}catch(_){return''}}
function sourceUrl(item){return params.get('src')||item?.readerUrl||item?.localUrl||item?.publicUrl||item?.sourceUrl||item?.downloadUrl||''}
function loadJson(url){return fetch(url,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()})}
function loadCatalog(){const id=params.get('id');if(!id)return Promise.resolve(null);const base=fetch('data/ingested_library.json',{cache:'no-store'}).then(r=>r.ok?r.json():Promise.reject()).catch(()=>fetch('private/acquisition_candidates.json',{cache:'no-store'}).then(r=>r.ok?r.json():{items:[]}).then(j=>({items:(j.items||[]).map(x=>({id:x.workId,workId:x.workId,titleOriginal:x.titleOriginal,titleEn:x.titleEn,author:x.author,language:x.language,format:x.format,subjects:x.subjects||[],siteSections:x.siteSections||[],sourceUrl:x.sourceUrl,downloadUrl:x.downloadUrl,readerUrl:x.downloadUrl||x.sourceUrl,archiveIdentifier:x.archiveIdentifier}))})).catch(()=>({items:[]})));
return Promise.all([
 base,
 fetch('data/published_user_books.json',{cache:'no-store'}).then(r=>r.ok?r.json():{items:[]}).catch(()=>({items:[]})),
 fetch('data/generated_epubs.json',{cache:'no-store'}).then(r=>r.ok?r.json():{items:[]}).catch(()=>({items:[]}))
]).then(([b,p,e])=>{const m=new Map();(b.items||[]).forEach(x=>m.set(idOf(x),{...x}));(p.items||[]).forEach(x=>m.set(idOf(x),{...(m.get(idOf(x))||{}),...x}));(e.items||[]).forEach(x=>m.set(String(x.id),{...(m.get(String(x.id))||{id:x.id,titleAr:x.titleAr}),epub:x}));return m.get(String(id))||null})}
function loadConfig(){return loadJson('data/reader_config.json').then(j=>({...DEFAULT_CONFIG,...j})).catch(()=>DEFAULT_CONFIG)}
function addCss(url){return new Promise((resolve,reject)=>{const l=document.createElement('link');l.rel='stylesheet';l.href=url;l.onload=()=>resolve();l.onerror=()=>reject(new Error('CSS load failed'));document.head.appendChild(l)})}
function addScript(url,module=false){return new Promise((resolve,reject)=>{const s=document.createElement('script');if(module)s.type='module';s.src=url;s.async=false;s.onload=()=>resolve();s.onerror=()=>reject(new Error(`Script load failed: ${url}`));document.head.appendChild(s)})}
function vendorBase(version){return state.config.cdn.replace('{version}',encodeURIComponent(version))}
async function probeVersion(version){const url=vendorBase(version)+'BookReader.js';try{const r=await fetch(url,{method:'HEAD',mode:'cors',cache:'no-store'});return r.ok}catch(_){return false}}
async function loadBookReaderEngine(){if(window.BookReader)return state.engineVersion||state.config.version;let version=state.config.version;if(!(await probeVersion(version)))version=state.config.fallbackVersion;const base=vendorBase(version);await addCss(base+'BookReader.css');await addScript(base+'webcomponents-bundle.js');await addScript(base+'jquery-3.js');await addScript(base+'BookReader.js');await addScript(base+'plugins/plugin.iiif.js');await addScript(base+'plugins/plugin.url.js');try{await addScript(base+'ia-bookreader-bundle.js',true)}catch(_){/* core reader still works without the web-component shell */}state.engineVersion=version;const engineEl=$('#readerEngine');if(engineEl)engineEl.textContent=`BookReader ${version} · ${state.config.license}`;return version}
function bookReaderMetadata(item){return [
 {label:'العنوان',value:titleOf(item)},
 authorOf(item)?{label:'المؤلف',value:authorOf(item)}:null,
 item?.editorAr?{label:'التحقيق',value:item.editorAr}:null,
 item?.publisherAr?{label:'الناشر',value:item.publisherAr}:null,
 item?.editionAr?{label:'الطبعة',value:item.editionAr}:null,
 item?.pages?{label:'الصفحات',value:String(item.pages)}:null,
].filter(Boolean)}
async function startIiif(manifestUrl,item){setLoading(true);setStatus('جارٍ تجهيز القارئ…');await loadBookReaderEngine();const manifest=typeof manifestUrl==='string'?await loadJson(manifestUrl):manifestUrl;setMode('bookreader');const options={el:'#BookReader',ui:'full',bookTitle:titleOf(item),bookUrl:'library.html',bookUrlText:'العودة إلى المكتبة',bookUrlTitle:'العودة إلى المكتبة',metadata:bookReaderMetadata(item),imagesBaseURL:vendorBase(state.engineVersion)+'images/',plugins:{iiif:{manifest}}};window.br=state.bookReader=new window.BookReader(options);state.bookReader.init();setLoading(false);setStatus(`القارئ المتقدم · BookReader ${state.engineVersion}`,'ok')}
function pageDataFromManifest(manifest){const pages=Array.isArray(manifest?.pages)?manifest.pages:[];if(!pages.length)return null;const leaves=pages.map((p,i)=>({width:Number(p.width)||1200,height:Number(p.height)||1600,uri:p.uri||p.url,pageNum:p.pageNum||p.label||String(i+1)})).filter(p=>p.uri);if(!leaves.length)return null;const data=[];for(let i=0;i<leaves.length;i+=2){if(i===0)data.push([leaves[i]]);else data.push([leaves[i],leaves[i+1]].filter(Boolean))}return data}
async function startPageManifest(manifest,item){setLoading(true);await loadBookReaderEngine();const data=pageDataFromManifest(manifest);if(!data)throw new Error('No readable pages in manifest');setMode('bookreader');const options={el:'#BookReader',ui:'full',data,bookTitle:titleOf(item),metadata:bookReaderMetadata(item),imagesBaseURL:vendorBase(state.engineVersion)+'images/'};window.br=state.bookReader=new window.BookReader(options);state.bookReader.init();setLoading(false);setStatus(`القارئ المتقدم · BookReader ${state.engineVersion}`,'ok')}
function showFrame(url,type='document'){setMode('frame');setLoading(false);const frame=$('#readerFrame');frame.src=url;frame.title=titleOf(state.item);$('#frameOpen').href=url;setStatus(type==='pdf'?'عارض PDF داخل القارئ':'المصدر داخل القارئ','ok')}
async function showText(url){setLoading(true);setStatus('جارٍ تحميل النص…');const r=await fetch(url);if(!r.ok)throw new Error(`HTTP ${r.status}`);let text=await r.text();if(/\.html?(?:$|[?#])/i.test(url)){const doc=new DOMParser().parseFromString(text,'text/html');text=doc.body?.innerText||text}setMode('text');$('#textContent').textContent=text;$('#textSearch').disabled=false;$('#textListen').disabled=false;setLoading(false);setStatus('قارئ نصي · بحث واستماع متاحان','ok')}
function showUnavailable(message,url=''){setMode('unavailable');setLoading(false);$('#readerUnavailableText').textContent=message||'لا تتوفر لهذا السجل مادة عامة قابلة للفتح في القارئ.';const a=$('#readerSourceLink');if(url){a.href=url;a.hidden=false}else a.hidden=true;setStatus('المادة غير متاحة للقارئ العام','warn')}
async function resolveAndStart(){state.config=await loadConfig();state.item=await loadCatalog();updateHeader(state.item);const item=state.item||{};let src=sourceUrl(item);const explicitManifest=params.get('manifest')||item.iiifManifest||item.readerManifest||item.pageManifest;const ia=params.get('ia')||item.archiveIdentifier||archiveIdentifier(src)||archiveIdentifier(item.sourceUrl)||archiveIdentifier(item.downloadUrl);
try{
 if(explicitManifest){const m=typeof explicitManifest==='string'?await loadJson(explicitManifest):explicitManifest;if(m?.pages)return await startPageManifest(m,item);return await startIiif(m,item)}
 if(ia){const manifest=`https://iiif.archive.org/iiif/3/${encodeURIComponent(ia)}/manifest.json`;return await startIiif(manifest,{...item,archiveIdentifier:ia})}
 if(src&&/\.json(?:$|[?#])/i.test(src)){const m=await loadJson(src);if(m?.pages)return await startPageManifest(m,item);if(m?.items||m?.sequences||m?.['@context'])return await startIiif(m,item)}
 if(src&&/\.pdf(?:$|[?#])/i.test(src))return showFrame(src,'pdf');
 if(src&&/\.(?:txt|html?|md)(?:$|[?#])/i.test(src))return await showText(src);
 if(src)return showFrame(src,'source');
 if(item.epub?.publicUrl)return showUnavailable('نسخة EPUB متاحة للتنزيل، لكن لا يوجد حالياً أصل صفحات/IIIF عام لهذا الكتاب.',item.epub.publicUrl);
 return showUnavailable(item.publicationNoteAr||'لا يوجد أصل عام صالح للفتح في القارئ لهذا السجل.');
}catch(err){console.error(err);showUnavailable('تعذر تشغيل القارئ لهذا المصدر. يمكنك فتح المصدر الأصلي عند توفره.',src);setStatus('تعذر تحميل المصدر','error')}
}
function bindShell(){
 $('#readerFullscreen')?.addEventListener('click',()=>{const el=$('#readerStage');const fn=el.requestFullscreen||el.webkitRequestFullscreen;if(fn)fn.call(el)});
 $('#readerTheme')?.addEventListener('click',()=>{document.body.classList.toggle('reader-sepia')});
 $('#readerInfo')?.addEventListener('click',()=>{$('#readerInfoPanel').toggleAttribute('hidden')});
 $('#readerInfoClose')?.addEventListener('click',()=>{$('#readerInfoPanel').hidden=true});
 $('#textSize')?.addEventListener('input',e=>{$('#textContent').style.fontSize=`${e.target.value}px`});
 $('#textSearch')?.addEventListener('click',()=>{const q=prompt('اكتب كلمة أو عبارة للبحث داخل الكتاب:');if(!q)return;const t=$('#textContent').textContent||'',i=t.indexOf(q);if(i<0)return alert('لم يتم العثور على العبارة.');const before=t.slice(Math.max(0,i-180),i),hit=t.slice(i,i+q.length),after=t.slice(i+q.length,i+q.length+260);$('#textExcerpt').innerHTML=`${esc(before)}<mark>${esc(hit)}</mark>${esc(after)}`;$('#textExcerpt').hidden=false});
 $('#textListen')?.addEventListener('click',()=>{const text=$('#textContent').textContent||'';speechSynthesis.cancel();const u=new SpeechSynthesisUtterance(text.slice(0,15000));u.lang='ar-MA';speechSynthesis.speak(u)});
}
bindShell();resolveAndStart();
})();
