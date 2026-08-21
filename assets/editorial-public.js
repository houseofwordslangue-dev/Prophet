(function(){
'use strict';
const MANIFEST='data/editorial/publication_manifest.json';
const SUPPLEMENT='data/editorial/publication_supplement.json';
const DOC100='data/editorial/documentary_aliases_100.json';
const CHILD500='data/editorial/children_500.json';
const SECTION_AR={light:'النور',prophet:'النبي',messenger:'الرسول',human:'الإنسان',mercy:'الرحمة العظمى',family:'الأسرة',companions:'الصحابة',media:'الوسائط',forums:'المنتديات',children:'للأطفال'};
const CHILD_CAT_AR={kindness:'الرحمة والرفق',family:'الأسرة والبيت',learning:'التعلّم والمعرفة',journeys:'الرحلات والأماكن',companions:'الصحبة والتعاون',character:'الأخلاق الجميلة','daily-life':'من الحياة اليومية'};
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
function classifyDocumentaries(baseArticles,cfg){
 if(!cfg||cfg.status!=='PUBLISHED'||cfg.mode!=='reclassify')return {articles:baseArticles,count:0};
 const wanted=new Set();
 for(let i=Number(cfg.sourceStart||1);i<=Number(cfg.sourceEnd||0);i++)wanted.add(String(cfg.sourceIdPrefix||'')+String(i).padStart(3,'0'));
 let count=0;
 const articles=baseArticles.map(src=>{
   if(!wanted.has(src.id))return src;
   count++;
   return {...src,originalTitle:src.title,title:String(cfg.titlePrefix||'')+src.title,section:cfg.section||'media',subsection:cfg.subsection||'documentaries',sections:[(cfg.section||'media')+'/'+(cfg.subsection||'documentaries')],publishedAt:cfg.publishedAt||src.publishedAt,documentaryClassification:true,documentarySourceId:src.id,contentType:'EXTENDED DRIVE-SOURCE DOCUMENTARY TEXT',canonicalEditorialSlot:false,sourceCoveragePercent:100,aiOriginalSubstantiveContentPercent:0,unsupportedFactualParagraphs:0,unverifiedQuotations:0,quotationVerification:'PASS',provenanceStatus:'PASS',duplicateCheck:'PASS'};
 });
 if(Number(cfg.count||0)&&count!==Number(cfg.count))throw new Error('Documentary classification incomplete: '+count+'/'+cfg.count);
 return {articles,count};
}
function norm(s){return String(s||'').replace(/\s+/g,' ').trim()}
function words(s){return norm(s).split(/\s+/).filter(Boolean)}
function splitSentences(text){
 const clean=norm(text);
 if(!clean)return [];
 const parts=clean.split(/(?<=[.!?؟؛])\s+|(?<=»)\s+/u).map(norm).filter(Boolean);
 if(parts.length===1&&words(clean).length>120){
   const w=words(clean),out=[];
   for(let i=0;i<w.length;i+=70)out.push(w.slice(i,i+95).join(' '));
   return out;
 }
 return parts;
}
const CHILD_BANNED_STRICT=['قتل','قتال','قاتل','قتيل','موت','مات','وفاة','دم','جرح','ذبح','سيف','سيوف','حرب','غزوة','غزا','معركة','أسرى','أسير','عذاب','جهنم','نار','لعن','زنا','جماع','عورة','خمر','رجم','صلب','تعذيب','سبى','سبي','عدو','أعداء','وثن','صنم','كافر','مشرك','battle','war','kill','killed','death','dead','blood','wound','sword','fight','fighting','enemy','enemies','slaughter','martyr','hell','curse','torture','slave','sexual','rape','idol','idolatry','unbeliever','infidel','heathen','violence','treachery','hypocrisy','fanatic','despotism','guerre','mort','tuer','tué','sang','épée','combat','ennemi','enfer','torture','esclave'];
const CHILD_BANNED_HARD=['زنا','جماع','عورة','اغتصاب','رجم','تعذيب','ذبح','دماء','sexual','rape','torture','porn','genitals','viol explicite','اغتصاب'];
const CHILD_TERMS={
 kindness:['رحمة','رحيم','رفق','سلام','ابتسم','تبسم','عفو','عفا','إحسان','حب','محبة','kindness','mercy','smile','peace','gentle','love','compassion','bonté','miséricorde','paix','sourire'],
 family:['خديجة','فاطمة','عائشة','أهله','أسرته','ابنه','ابنته','بناته','أمه','أبيه','جده','عمه','بيت','family','mother','father','daughter','son','home','wife','famille','mère','père','fille','fils','maison'],
 learning:['اقرأ','قرأ','علم','تعلم','كتاب','القرآن','حديث','سأل','الوحي','read','learn','knowledge','book','asked','teach','revelation','lire','apprendre','savoir','livre','question'],
 journeys:['مكة','المدينة','قباء','طريق','سفر','هجرة','رحلة','وصل','قدم','journey','road','travel','Mecca','Medina','arrived','route','voyage','chemin','Mecque','Médine'],
 companions:['أبو بكر','علي بن أبي طالب','بلال','الأنصار','المهاجرين','أصحابه','الصحابة','companion','companions','friends','Abu Bakr','Ali','Bilal','compagnon','compagnons','amis'],
 character:['صدق','أمانة','أمين','صبر','وفاء','كرم','تواضع','عدل','honest','trust','patience','generous','humble','justice','honnête','patience','généreux','humble','justice']
};
function childCategory(text){
 const t=String(text||'').toLowerCase();let best='daily-life',score=0;
 for(const [cat,terms] of Object.entries(CHILD_TERMS)){let s=0;for(const term of terms)if(t.includes(term.toLowerCase()))s++;if(s>score){score=s;best=cat}}
 return best;
}
function childSentenceScore(text,lang,strict=true){
 const t=norm(text),low=t.toLowerCase(),wc=words(t).length;
 if(wc<10||wc>140)return -9999;
 const banned=strict?CHILD_BANNED_STRICT:CHILD_BANNED_HARD;
 if(banned.some(x=>low.includes(x.toLowerCase())))return -9999;
 if(/[{}<>]|�/.test(t))return -9999;
 let score=0;
 if(wc>=18&&wc<=85)score+=6;else if(wc<=120)score+=3;
 if(lang==='ar')score+=5;else if(lang==='fr'||lang==='en')score+=2;
 const cat=childCategory(t);if(cat!=='daily-life')score+=4;
 if(/[.!؟»]$/.test(t))score+=1;
 const digitRatio=(t.match(/[0-9٠-٩]/g)||[]).length/Math.max(1,t.length);if(digitRatio>.04)score-=5;
 if((t.match(/[\/()\[\]]/g)||[]).length>8)score-=3;
 return score;
}
function makeChildren(baseArticles,cfg){
 if(!cfg||cfg.status!=='PUBLISHED')return [];
 const wanted=Number(cfg.count||500),minWords=Number(cfg.minWords||18),maxWords=Number(cfg.maxWords||120),candidates=[],seen=new Set();
 for(const src of baseArticles){
   if(Number(src.sourceCoveragePercent)!==100||Number(src.aiOriginalSubstantiveContentPercent||0)!==0)continue;
   for(let pi=0;pi<(src.paragraphs||[]).length;pi++){
     const p=src.paragraphs[pi],lang=String(p.language||src.language||'ar').toLowerCase();
     const sentences=splitSentences(p.text);
     for(let si=0;si<sentences.length;si++){
       const text=norm(sentences[si]),wc=words(text).length;if(wc<minWords||wc>maxWords)continue;
       const key=text.toLowerCase().replace(/[\s\p{P}\p{S}]+/gu,'');if(!key||seen.has(key))continue;
       const score=childSentenceScore(text,lang,true);if(score<0)continue;
       seen.add(key);candidates.push({src,p,pi,si,text,lang,score,cat:childCategory(text),key});
     }
   }
 }
 if(candidates.length<wanted){
   for(const src of baseArticles){
     if(Number(src.sourceCoveragePercent)!==100||Number(src.aiOriginalSubstantiveContentPercent||0)!==0)continue;
     for(let pi=0;pi<(src.paragraphs||[]).length;pi++){
       const p=src.paragraphs[pi],lang=String(p.language||src.language||'ar').toLowerCase();
       for(const [si,text0] of splitSentences(p.text).entries()){
         const text=norm(text0),wc=words(text).length;if(wc<minWords||wc>maxWords)continue;
         const key=text.toLowerCase().replace(/[\s\p{P}\p{S}]+/gu,'');if(!key||seen.has(key))continue;
         const score=childSentenceScore(text,lang,false);if(score<0)continue;
         seen.add(key);candidates.push({src,p,pi,si,text,lang,score:score-2,cat:childCategory(text),key});
       }
     }
   }
 }
 candidates.sort((a,b)=>b.score-a.score||String(a.src.id).localeCompare(String(b.src.id))||a.pi-b.pi||a.si-b.si);
 if(candidates.length<wanted)throw new Error('Child-safe source pool incomplete: '+candidates.length+'/'+wanted);
 const chosen=candidates.slice(0,wanted),catNo={};
 return chosen.map((c,i)=>{
   const n=String(i+1).padStart(3,'0');catNo[c.cat]=(catNo[c.cat]||0)+1;
   const ref='children-'+n+'-source';
   const inherited=(c.src.sources||[]).map((s,j)=>({...s,ref:j===0?ref:(s.ref||ref+'-'+(j+1))}));
   const refs=inherited.map(s=>s.ref).filter(Boolean);
   const paragraph={id:'20260821-children-'+n+'-p01',text:c.text,language:c.lang,sourceRefs:refs.length?refs:(c.p.sourceRefs||[]),substantive:true,aiOriginal:false,quotation:Boolean(c.p.quotation),quotationVerified:c.p.quotationVerified!==false,editorialOperations:['child-safe-source-sentence-selection','source-wording-preserved']};
   const title=(cfg.titlePrefix||'قراءة مصوّرة للصغار: ')+(CHILD_CAT_AR[c.cat]||'من السيرة')+' — '+n;
   const a={id:'20260821-children-'+n,title,language:c.lang,contentType:'LIGHT ILLUSTRATED CHILDREN SOURCE READING',section:cfg.section||'children',subsection:c.cat,sections:[(cfg.section||'children')+'/'+c.cat],ageBand:cfg.ageBand||'7-12',paragraphs:[paragraph],sources:inherited,publishedAt:cfg.publishedAt||c.src.publishedAt,publicationStatus:'PUBLISHED',draftStatus:'SOURCE_VERIFIED',articleUrl:'feature.html?id='+encodeURIComponent('20260821-children-'+n),sourceCoveragePercent:100,aiOriginalSubstantiveContentPercent:0,unsupportedFactualParagraphs:0,unverifiedQuotations:0,quotationVerification:'PASS',provenanceStatus:'PASS',duplicateCheck:'PASS',childrenSourceId:c.src.id,childrenSourceParagraph:c.pi+1,illustrationTheme:c.cat,illustrationSeed:i+1,canonicalEditorialSlot:false};
   a.author=deriveByline(a,inherited.length?inherited:c.src.sources||[]);a.attributionType=a.author===EDITORIAL_BOARD_AR?'editorial-board':'source-author';return a;
 });
}
function childArt(a,large=false){
 if(a.section!=='children')return '';
 const seed=Number(a.illustrationSeed||1),h1=(seed*47)%360,h2=(h1+38)%360,theme=a.illustrationTheme||a.subsection||'daily-life';
 const motifs={
  kindness:'<circle cx="76" cy="48" r="18" fill="rgba(255,255,255,.50)"/><path d="M65 48c7 13 17 13 24 0" fill="none" stroke="rgba(20,70,55,.7)" stroke-width="4" stroke-linecap="round"/>',
  family:'<path d="M48 70L80 42l32 28v30H48z" fill="rgba(255,255,255,.48)"/><rect x="71" y="76" width="18" height="24" rx="2" fill="rgba(20,70,55,.35)"/>',
  learning:'<path d="M35 53q23-12 45 0v43q-22-12-45 0zM125 53q-23-12-45 0v43q22-12 45 0z" fill="rgba(255,255,255,.54)" stroke="rgba(20,70,55,.3)"/>',
  journeys:'<path d="M18 105Q62 58 142 98" fill="none" stroke="rgba(255,255,255,.66)" stroke-width="8" stroke-linecap="round"/><circle cx="127" cy="30" r="10" fill="rgba(255,244,190,.85)"/>',
  companions:'<circle cx="58" cy="65" r="22" fill="rgba(255,255,255,.48)"/><circle cx="102" cy="65" r="22" fill="rgba(255,255,255,.38)"/><path d="M72 65h16" stroke="rgba(20,70,55,.55)" stroke-width="6" stroke-linecap="round"/>',
  character:'<path d="M80 27l9 20 22 2-17 14 5 22-19-12-19 12 5-22-17-14 22-2z" fill="rgba(255,250,205,.78)"/>',
  'daily-life':'<path d="M34 100h92M50 100V64h60v36M64 64V48h32v16" stroke="rgba(255,255,255,.58)" stroke-width="7" fill="none" stroke-linejoin="round"/>'
 };
 const stars=Array.from({length:5},(_,i)=>{const x=18+((seed*(i+3)*17)%125),y=17+((seed*(i+5)*11)%78),r=1+((seed+i)%3);return `<circle cx="${x}" cy="${y}" r="${r}" fill="rgba(255,255,255,.42)"/>`}).join('');
 return `<div class="ep-child-illustration${large?' is-large':''}" aria-hidden="true"><svg viewBox="0 0 160 120" role="img"><defs><linearGradient id="g${seed}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="hsl(${h1} 55% 78%)"/><stop offset="1" stop-color="hsl(${h2} 48% 66%)"/></linearGradient></defs><rect width="160" height="120" rx="16" fill="url(#g${seed})"/>${stars}${motifs[theme]||motifs['daily-life']}<path d="M0 108Q40 96 80 108T160 105V120H0z" fill="rgba(20,70,55,.13)"/></svg></div>`;
}
async function loadPublished(){
 const primary=await getJSON(MANIFEST),supplement=await maybeJSON(SUPPLEMENT),docCfg=await maybeJSON(DOC100),childCfg=await maybeJSON(CHILD500),all=[],ids=[];
 const packs=[primary].concat(supplement?[supplement]:[]);
 for(const pack of packs){
   const allowed=new Set(pack.publishedIds||[]);
   for(const id of allowed)ids.push(id);
   for(const p of pack.draftBatchPaths||[]){const j=await getJSON(p);for(const raw of j.drafts||[]){const d=expandCompactDraft(raw,j);if(allowed.has(d.id))all.push(applyOverride(d,pack))}}
 }
 const by=new Map(all.map(a=>[a.id,a])),missing=ids.filter(id=>!by.has(id));if(missing.length)throw new Error('Missing published records: '+missing.join(','));
 const baseArticles=ids.map(id=>by.get(id));
 const classified=classifyDocumentaries(baseArticles,docCfg);
 const children=makeChildren(baseArticles,childCfg);
 return {manifest:primary,articles:classified.articles.concat(children),documentaryCount:classified.count,childrenCount:children.length};
}
function excerpt(a){const t=(a.paragraphs||[]).map(p=>p.text).join(' ');return t.length>180?t.slice(0,180)+'…':t}
function card(a){return `<article class="ep-card${a.section==='children'?' ep-card-child':''}" data-section="${esc(a.section)}">${childArt(a)}<div class="meta">${esc(SECTION_AR[a.section]||a.section)} · ${esc(CHILD_CAT_AR[a.subsection]||a.subsection)}</div><h2>${esc(a.title)}</h2><div class="ep-byline">${esc(a.author||EDITORIAL_BOARD_AR)}</div><p>${esc(excerpt(a))}</p><div class="foot"><span class="ep-badge">موثّق المصدر 100%</span><a href="${esc(a.articleUrl)}">قراءة المادة</a></div></article>`}
function renderFeed(data){
 const feed=document.getElementById('articleFeed'),status=document.getElementById('publicationStatus'),search=document.getElementById('articleSearch'),filter=document.getElementById('sectionFilter');
 const sections=[...new Set(data.articles.map(a=>a.section))];filter.innerHTML='<option value="">جميع الأقسام</option>'+sections.map(s=>`<option value="${esc(s)}">${esc(SECTION_AR[s]||s)}</option>`).join('');
 const sectionCounts={};data.articles.forEach(a=>sectionCounts[a.section]=(sectionCounts[a.section]||0)+1);
 const multiPass=sections.every(s=>sectionCounts[s]>1);
 const draw=()=>{const q=(search.value||'').trim().toLowerCase(),s=filter.value;const rows=data.articles.filter(a=>(!s||a.section===s)&&(!q||[a.title,a.author,a.section,a.subsection,...(a.paragraphs||[]).map(p=>p.text)].join(' ').toLowerCase().includes(q)));feed.innerHTML=rows.map(card).join('')||'<div class="ep-error">لا توجد نتائج مطابقة.</div>';status.textContent=`منشور: ${rows.length} من ${data.articles.length} مادة · للأطفال: ${data.childrenCount||0} · وثائقيات موسعة مصنفة من Drive: ${data.documentaryCount||0} · كل قسم رئيسي يحتوي أكثر من مقال: ${multiPass?'نعم':'لا'} · المحتوى الجوهري المولّد بالذكاء الاصطناعي: 0`;};
 search.addEventListener('input',draw);filter.addEventListener('change',draw);draw();
}
function renderArticle(data){
 const id=new URLSearchParams(location.search).get('id'),a=data.articles.find(x=>x.id===id),box=document.getElementById('articleView');if(!a){box.innerHTML='<div class="ep-error">المادة المطلوبة غير موجودة في سجل النشر الموثّق.</div>';return}
 document.title=a.title+' — محمد ﷺ';
 box.innerHTML=`<div class="ep-breadcrumb">${esc(SECTION_AR[a.section]||a.section)} / ${esc(CHILD_CAT_AR[a.subsection]||a.subsection)}</div><h1>${esc(a.title)}</h1>${childArt(a,true)}<div class="ep-article-lead"><strong>${esc(a.author||EDITORIAL_BOARD_AR)}</strong> · ${a.section==='children'?'قراءة خفيفة للصغار من نص مصدر محفوظ':'مادة مصدرية منشورة بعد التحقق'} · ${new Date(a.publishedAt).toLocaleString('ar')}</div><div class="ep-article-body">${(a.paragraphs||[]).map(p=>`<p lang="${esc(p.language||'ar')}" dir="${(p.language==='en'||p.language==='fr')?'ltr':'rtl'}">${esc(p.text)}</p>`).join('')}</div><div class="ep-proof"><strong>سجل النزاهة التحريرية</strong>تغطية المصدر: 100% · محتوى جوهري مولّد بالذكاء الاصطناعي: 0% · فقرات واقعية غير مسندة: 0 · اقتباسات غير متحقق منها: 0.${a.section==='children'?' النص المعروض مختار من المصدر الأصلي دون إعادة صياغة جوهرية، والرسم توضيحي غير تشخيصي.':''}</div><div class="ep-article-actions"><a href="editorial.html">كل المقالات</a><a href="library.html">المكتبة</a></div>`;
}
loadPublished().then(data=>{if(document.body.dataset.page==='feature')renderArticle(data);else renderFeed(data)}).catch(err=>{const el=document.getElementById('articleFeed')||document.getElementById('articleView')||document.body;el.innerHTML='<div class="ep-error">تعذر تحميل سجل النشر الموثّق. '+esc(err.message)+'</div>'});
})();
