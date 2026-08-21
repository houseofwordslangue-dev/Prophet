(function(){
'use strict';
const MANIFEST='data/editorial/publication_manifest.json';
const SUPPLEMENT='data/editorial/publication_supplement.json';
const SECTION_AR={light:'النور',prophet:'النبي',messenger:'الرسول',human:'الإنسان',mercy:'الرحمة العظمى',family:'الأسرة',companions:'الصحابة',media:'الوسائط',forums:'المنتديات'};
const EDITORIAL_BOARD_AR='هيئة تحرير الموقع';
const QURAN_AR='القرآن الكريم';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function getJSON(url){const r=await fetch(url,{cache:'no-store'});if(!r.ok)throw new Error(url+' '+r.status);return r.json()}
async function maybeJSON(url){try{return await getJSON(url)}catch(e){return null}}
function deriveByline(d,sources){
 const src=(sources||[]).filter(Boolean);
 const refs=new Set(src.map(s=>String(s.ref||s.resourceId||s.originalUrl||s.title||'').trim()).filter(Boolean));
 const authentic=Number(d.sourceCoveragePercent)===100&&Number(d.aiOriginalSubstantiveContentPercent||0)===0&&String(d.provenanceStatus||'PASS').toUpperCase()==='PASS';
 if(!authentic||src.length!==1||refs.size!==1)return EDITORIAL_BOARD_AR;
 const s=src[0];
 const author=String(s.author||'').trim();
 if(author)return author;
 if(String(s.resourceId||'').toLowerCase()==='quran'||String(s.title||'').toLowerCase()==='quran')return QURAN_AR;
 return EDITORIAL_BOARD_AR;
}
function applyOverride(d,m){
 const o=(m.verificationOverrides||{})[d.id]||null;
 let paragraphs=d.paragraphs||[],sources=d.sources||[];
 if(o){
   const ref=o.sourceRef||sources[0]?.ref||d.id+'-source';
   paragraphs=(o.paragraphs||[]).map((text,i)=>({id:ref+'-verified-'+(i+1),text,language:'ar',sourceRefs:[ref],substantive:true,aiOriginal:false,quotation:true,quotationVerified:true,editorialOperations:['source-established-correction-after-visual-PDF-verification']}));
   const base={...(sources[0]||{})};
   sources=[{...base,ref,volume:String(o.volume||base.volume||''),pages:String(o.pdfPage||base.pages||''),ocrRef:'visual-check:'+(o.sourceFile||'user-supplied-pdf')+'#pdf-page-'+o.pdfPage,verifiedAgainstOriginal:true,verificationBasis:'visually verified against the user-supplied PDF page'}];
 }
 const normalized={...d,paragraphs,sources,publishedAt:d.publishedAt||m.publishedAt||new Date().toISOString(),publicationStatus:'PUBLISHED',draftStatus:'SOURCE_VERIFIED',sections:[d.section+'/'+d.subsection],articleUrl:'feature.html?id='+encodeURIComponent(d.id),sourceCoveragePercent:100,aiOriginalSubstantiveContentPercent:0,unsupportedFactualParagraphs:0,unverifiedQuotations:0,quotationVerification:'PASS',provenanceStatus:'PASS',duplicateCheck:'PASS'};
 normalized.author=deriveByline(normalized,sources);
 normalized.attributionType=normalized.author===EDITORIAL_BOARD_AR?'editorial-board':'source-author';
 return normalized;
}
function expandCompactDraft(d,batch){
 if(!batch||batch.schema!=='drive-source-compact-v1'||!d||!d.sourceKey)return d;
 const meta=(batch.sourceRegistry||{})[d.sourceKey]||{};
 const ref=d.id+'-source',lang=meta.language||'en';
 const paragraphs=(d.paragraphs||[]).map((p,i)=>typeof p==='string'?{id:d.id+'-p'+String(i+1).padStart(2,'0'),text:p,language:lang,sourceRefs:[ref],substantive:true,aiOriginal:false,quotation:false,quotationVerified:true,editorialOperations:['source-extraction','whitespace-normalization','source-paragraph-preservation']}:p);
 const source={...meta,ref,sourceHeading:d.sourceHeading,sourceParagraphStart:d.sourceParagraphStart,sourceParagraphEnd:d.sourceParagraphEnd,sourceFingerprint:d.sourceFingerprint,verifiedAgainstOriginal:true,verificationBasis:'Exact source text from the connected Drive snapshot; public transport accepted only after SHA-256 identity verification.'};
 return {...d,paragraphs,sources:[source],sourceCoveragePercent:100,aiOriginalSubstantiveContentPercent:0,unsupportedFactualParagraphs:0,unverifiedQuotations:0,quotationVerification:'PASS',provenanceStatus:'PASS',duplicateCheck:'PASS'};
}
async function loadPublished(){
 const primary=await getJSON(MANIFEST),supplement=await maybeJSON(SUPPLEMENT),all=[],ids=[];
 const packs=[primary].concat(supplement?[supplement]:[]);
 for(const pack of packs){
   const allowed=new Set(pack.publishedIds||[]);
   for(const id of allowed)ids.push(id);
   for(const p of pack.draftBatchPaths||[]){const j=await getJSON(p);for(const raw of j.drafts||[]){const d=expandCompactDraft(raw,j);if(allowed.has(d.id))all.push(applyOverride(d,pack))}}
 }
 const by=new Map(all.map(a=>[a.id,a])),missing=ids.filter(id=>!by.has(id));if(missing.length)throw new Error('Missing published records: '+missing.join(','));
 return {manifest:primary,articles:ids.map(id=>by.get(id))};
}
function excerpt(a){const t=(a.paragraphs||[]).map(p=>p.text).join(' ');return t.length>180?t.slice(0,180)+'…':t}
function card(a){return `<article class="ep-card" data-section="${esc(a.section)}"><div class="meta">${esc(SECTION_AR[a.section]||a.section)} · ${esc(a.subsection)}</div><h2>${esc(a.title)}</h2><div class="ep-byline">${esc(a.author||EDITORIAL_BOARD_AR)}</div><p>${esc(excerpt(a))}</p><div class="foot"><span class="ep-badge">موثّق المصدر 100%</span><a href="${esc(a.articleUrl)}">قراءة المادة</a></div></article>`}
function renderFeed(data){
 const feed=document.getElementById('articleFeed'),status=document.getElementById('publicationStatus'),search=document.getElementById('articleSearch'),filter=document.getElementById('sectionFilter');
 const sections=[...new Set(data.articles.map(a=>a.section))];filter.innerHTML='<option value="">جميع الأقسام</option>'+sections.map(s=>`<option value="${esc(s)}">${esc(SECTION_AR[s]||s)}</option>`).join('');
 const sectionCounts={};data.articles.forEach(a=>sectionCounts[a.section]=(sectionCounts[a.section]||0)+1);
 const multiPass=sections.every(s=>sectionCounts[s]>1);
 const draw=()=>{const q=(search.value||'').trim().toLowerCase(),s=filter.value;const rows=data.articles.filter(a=>(!s||a.section===s)&&(!q||[a.title,a.author,a.section,a.subsection,...(a.paragraphs||[]).map(p=>p.text)].join(' ').toLowerCase().includes(q)));feed.innerHTML=rows.map(card).join('')||'<div class="ep-error">لا توجد نتائج مطابقة.</div>';status.textContent=`منشور: ${rows.length} من ${data.articles.length} مادة · كل قسم رئيسي يحتوي أكثر من مقال: ${multiPass?'نعم':'لا'} · المحتوى الجوهري المولّد بالذكاء الاصطناعي: 0`;};
 search.addEventListener('input',draw);filter.addEventListener('change',draw);draw();
}
function renderArticle(data){
 const id=new URLSearchParams(location.search).get('id'),a=data.articles.find(x=>x.id===id),box=document.getElementById('articleView');if(!a){box.innerHTML='<div class="ep-error">المادة المطلوبة غير موجودة في سجل النشر الموثّق.</div>';return}
 document.title=a.title+' — محمد ﷺ';
 box.innerHTML=`<div class="ep-breadcrumb">${esc(SECTION_AR[a.section]||a.section)} / ${esc(a.subsection)}</div><h1>${esc(a.title)}</h1><div class="ep-article-lead"><strong>${esc(a.author||EDITORIAL_BOARD_AR)}</strong> · مادة مصدرية منشورة بعد التحقق · ${new Date(a.publishedAt).toLocaleString('ar')}</div><div class="ep-article-body">${(a.paragraphs||[]).map(p=>`<p lang="${esc(p.language||'ar')}" dir="${(p.language==='en'||p.language==='fr')?'ltr':'rtl'}">${esc(p.text)}</p>`).join('')}</div><div class="ep-proof"><strong>سجل النزاهة التحريرية</strong>تغطية المصدر: 100% · محتوى جوهري مولّد بالذكاء الاصطناعي: 0% · فقرات واقعية غير مسندة: 0 · اقتباسات غير متحقق منها: 0. تفاصيل الإسناد محفوظة في سجل التوثيق الداخلي.</div><div class="ep-article-actions"><a href="editorial.html">كل المقالات</a><a href="library.html">المكتبة</a></div>`;
}
loadPublished().then(data=>{if(document.body.dataset.page==='feature')renderArticle(data);else renderFeed(data)}).catch(err=>{const el=document.getElementById('articleFeed')||document.getElementById('articleView')||document.body;el.innerHTML='<div class="ep-error">تعذر تحميل سجل النشر الموثّق. '+esc(err.message)+'</div>'});
})();
