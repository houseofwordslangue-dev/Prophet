(function(){
'use strict';
const SUPPORTED=['ar','en','fr'];
const q=new URLSearchParams(location.search);
const requested=(q.get('lang')||localStorage.getItem('editorial-lang')||document.documentElement.lang||'ar').toLowerCase();
const LANG=SUPPORTED.includes(requested)?requested:'ar';
localStorage.setItem('editorial-lang',LANG);
document.documentElement.lang=LANG;
document.documentElement.dir=LANG==='ar'?'rtl':'ltr';
document.body.dir=LANG==='ar'?'rtl':'ltr';
const UI={
 ar:{brand:'المقالات الموثّقة',library:'المكتبة',people:'الأشخاص',children:'للأطفال',articles:'المقالات',allArticles:'كل المقالات',search:'ابحث في العناوين والمحتوى…',allSections:'جميع الأقسام',loading:'جارٍ إعداد النسخة العربية…',unavailable:'تعذر إعداد الترجمة العربية على هذا المتصفح. بدّل اللغة لعرض النص الأصلي.',read:'قراءة المادة',verified:'موثّق المصدر 100%',sourceFirst:'المصدر أولاً، والإسناد محفوظ.',backLibrary:'العودة إلى المكتبة',coverage:'تغطية المصدر',coverageNote:'المواد المنشورة مرتبطة بسجل توثيق مصدرّي.',heroKicker:'تحرير قائم على المصدر',heroTitle:'المادة الأصلية أولاً',heroText:'كل مادة منشورة مشتقة من مصدر موثّق، وتعرض هنا في نسخة عربية مستقلة بلا خلط لغوي.',integrityTitle:'سجل النزاهة التحريرية',integrity:'تغطية المصدر: 100% · المحتوى الجوهري المولّد بالذكاء الاصطناعي: 0% · الفقرات الواقعية غير المسندة: 0 · الاقتباسات غير المتحقق منها: 0.',translated:'نسخة عربية مترجمة لغويًا من النص الموثّق',childrenTitle:'قراءات مصوّرة للصغار',childrenText:'قراءات خفيفة من مواد موثّقة، مع عرض عربي مستقل ورسوم غير تشخيصية.',childrenKicker:'قراءة خفيفة · مصدر محفوظ · رسم غير تشخيصي'},
 en:{brand:'Verified Articles',library:'Library',people:'People',children:'Children',articles:'Articles',allArticles:'All articles',search:'Search titles and content…',allSections:'All sections',loading:'Preparing the English version…',unavailable:'The English translation could not be prepared in this browser. Switch language to view the source text.',read:'Read article',verified:'100% source verified',sourceFirst:'Source first, with provenance preserved.',backLibrary:'Back to library',coverage:'Source coverage',coverageNote:'Published material is linked to a full provenance record.',heroKicker:'Source-based editorial work',heroTitle:'The original source comes first',heroText:'Every published item is derived from a verified source and is displayed here as a separate English version with no language mixing.',integrityTitle:'Editorial integrity record',integrity:'Source coverage: 100% · AI-original substantive content: 0% · Unsupported factual paragraphs: 0 · Unverified quotations: 0.',translated:'English linguistic translation of the verified source text',childrenTitle:'Illustrated readings for children',childrenText:'Light readings selected from verified material, presented as a separate English version with non-figurative illustrations.',childrenKicker:'Light reading · preserved source · non-figurative illustration'},
 fr:{brand:'Articles vérifiés',library:'Bibliothèque',people:'Personnes',children:'Enfants',articles:'Articles',allArticles:'Tous les articles',search:'Rechercher dans les titres et le contenu…',allSections:'Toutes les rubriques',loading:'Préparation de la version française…',unavailable:'La traduction française n’a pas pu être préparée dans ce navigateur. Changez de langue pour afficher le texte source.',read:'Lire l’article',verified:'Source vérifiée à 100 %',sourceFirst:'La source d’abord, avec provenance conservée.',backLibrary:'Retour à la bibliothèque',coverage:'Couverture des sources',coverageNote:'Chaque contenu publié est relié à son dossier complet de provenance.',heroKicker:'Édition fondée sur les sources',heroTitle:'La source originale d’abord',heroText:'Chaque contenu publié provient d’une source vérifiée et est présenté ici dans une version française distincte, sans mélange de langues.',integrityTitle:'Registre d’intégrité éditoriale',integrity:'Couverture des sources : 100 % · contenu substantiel original généré par IA : 0 % · paragraphes factuels non sourcés : 0 · citations non vérifiées : 0.',translated:'Traduction linguistique française du texte source vérifié',childrenTitle:'Lectures illustrées pour enfants',childrenText:'Lectures légères tirées de contenus vérifiés, présentées dans une version française distincte avec illustrations non figuratives.',childrenKicker:'Lecture légère · source conservée · illustration non figurative'}
};
const T=UI[LANG];
const SECTION={
 ar:{light:'النور',prophet:'النبي',messenger:'الرسول',human:'الإنسان',mercy:'الرحمة العظمى',family:'الأسرة',companions:'الصحابة',media:'الوسائط',forums:'المنتديات',children:'للأطفال',verses:'الآيات',hadith:'الحديث',righteous:'آثار الصالحين',research:'البحوث',seerah:'السيرة',documentaries:'الوثائقيات',videos:'الفيديو',lectures:'المحاضرات',podcasts:'البودكاست',audio:'الصوتيات',biographies:'السير',stories:'القصص',sayings:'الأقوال',kindness:'الرحمة والرفق',learning:'التعلّم والمعرفة',journeys:'الرحلات والأماكن',character:'الأخلاق الجميلة','daily-life':'من الحياة اليومية'},
 en:{light:'Light',prophet:'The Prophet',messenger:'The Messenger',human:'The Human Being',mercy:'Great Mercy',family:'Family',companions:'Companions',media:'Media',forums:'Forums',children:'Children',verses:'Verses',hadith:'Hadith',righteous:'Righteous reports',research:'Research',seerah:'Biography',documentaries:'Documentaries',videos:'Videos',lectures:'Lectures',podcasts:'Podcasts',audio:'Audio',biographies:'Biographies',stories:'Stories',sayings:'Sayings',kindness:'Kindness and mercy',learning:'Learning and knowledge',journeys:'Journeys and places',character:'Beautiful character','daily-life':'Daily life'},
 fr:{light:'Lumière',prophet:'Le Prophète',messenger:'Le Messager',human:'L’être humain',mercy:'Grande miséricorde',family:'Famille',companions:'Compagnons',media:'Médias',forums:'Forums',children:'Enfants',verses:'Versets',hadith:'Hadith',righteous:'Récits des vertueux',research:'Recherches',seerah:'Biographie',documentaries:'Documentaires',videos:'Vidéos',lectures:'Conférences',podcasts:'Podcasts',audio:'Audio',biographies:'Biographies',stories:'Récits',sayings:'Paroles',kindness:'Miséricorde et bienveillance',learning:'Apprentissage et savoir',journeys:'Voyages et lieux',character:'Beau caractère','daily-life':'Vie quotidienne'}
};
const S=SECTION[LANG];
function escRE(s){return s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}
function localeUrl(href){
 if(!href||href.startsWith('#')||href.startsWith('mailto:')||href.startsWith('tel:'))return href;
 try{const u=new URL(href,location.href);if(u.origin!==location.origin)return href;u.searchParams.set('lang',LANG);return u.pathname.replace(/^\//,'')+(u.search||'')+(u.hash||'')}catch(e){return href}
}
function injectSwitcher(){
 const nav=document.querySelector('.ep-nav');if(!nav||nav.querySelector('.ep-lang-switch'))return;
 const box=document.createElement('div');box.className='ep-lang-switch';
 box.innerHTML=SUPPORTED.map(l=>`<a href="${location.pathname.split('/').pop()||'editorial.html'}?${(()=>{const p=new URLSearchParams(location.search);p.set('lang',l);return p.toString()})()}" class="${l===LANG?'active':''}" hreflang="${l}">${l.toUpperCase()}</a>`).join('');
 nav.appendChild(box);
}
function localizeShell(){
 injectSwitcher();
 document.querySelectorAll('a[href]').forEach(a=>a.setAttribute('href',localeUrl(a.getAttribute('href'))));
 const brand=document.querySelector('.ep-brand b');if(brand)brand.textContent=document.body.dataset.page==='children'?T.children:T.brand;
 const links=[...document.querySelectorAll('.ep-nav nav a')];
 for(const a of links){const h=a.getAttribute('href')||'';if(h.includes('library'))a.textContent=T.library;else if(h.includes('people'))a.textContent=T.people;else if(h.includes('children'))a.textContent=T.children;else if(h.includes('editorial'))a.textContent=T.articles;}
 const search=document.getElementById('articleSearch');if(search)search.placeholder=T.search;
 const kicker=document.querySelector('.ep-kicker');const hero=document.querySelector('.ep-hero h1');const hp=document.querySelector('.ep-hero p:not(.ep-kicker)');
 if(document.body.dataset.page==='children'){
   if(kicker)kicker.textContent=T.childrenKicker;if(hero)hero.textContent=T.childrenTitle;if(hp)hp.textContent=T.childrenText;
 }else{
   if(kicker)kicker.textContent=T.heroKicker;if(hero)hero.textContent=T.heroTitle;if(hp)hp.textContent=T.heroText;
 }
 const cov=document.querySelector('.ep-integrity span');if(cov)cov.textContent=T.coverage;
 const covn=document.querySelector('.ep-integrity small');if(covn)covn.textContent=T.coverageNote;
 const foot=document.querySelector('.ep-foot strong');if(foot)foot.textContent=T.sourceFirst;
 const foota=document.querySelector('.ep-foot a');if(foota)foota.textContent=T.backLibrary;
}
function inferLanguage(text,el){
 const declared=(el&&el.closest('[lang]')&&el.closest('[lang]').getAttribute('lang')||'').slice(0,2).toLowerCase();if(SUPPORTED.includes(declared))return declared;
 const s=String(text||'');const ar=(s.match(/[\u0600-\u06ff]/g)||[]).length;if(ar>Math.max(3,s.length*.18))return 'ar';
 const low=' '+s.toLowerCase()+' ';if(/[àâçéèêëîïôùûüÿœæ]/i.test(s)||/\b(le|la|les|des|une|dans|avec|pour|sur|est|sont|qui|que|du|au|aux)\b/i.test(low))return 'fr';return 'en';
}
const translatorCache=new Map();
async function getTranslator(from,to){
 if(from===to)return null;const key=from+'>'+to;if(translatorCache.has(key))return translatorCache.get(key);
 let tr=null;
 try{
   if(globalThis.Translator&&typeof globalThis.Translator.create==='function')tr=await globalThis.Translator.create({sourceLanguage:from,targetLanguage:to});
   else if(globalThis.translation&&typeof globalThis.translation.createTranslator==='function')tr=await globalThis.translation.createTranslator({sourceLanguage:from,targetLanguage:to});
 }catch(e){tr=null}
 translatorCache.set(key,tr);return tr;
}
function cacheKey(from,to,text){let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619)}return 'etl:'+from+':'+to+':'+(h>>>0).toString(36)}
async function translateChunk(text,from,to){
 const t=String(text||'').trim();if(!t||from===to)return t;
 const k=cacheKey(from,to,t);try{const c=localStorage.getItem(k);if(c)return c}catch(e){}
 const tr=await getTranslator(from,to);if(!tr)throw new Error('translator unavailable');
 const out=await tr.translate(t);const value=String(out||'').trim();if(!value)throw new Error('empty translation');
 try{if(value.length<12000)localStorage.setItem(k,value)}catch(e){}
 return value;
}
function mixedPieces(text){
 const s=String(text||'');if(!s)return [];
 const out=[];let buf='',kind=null;
 const flush=()=>{if(buf)out.push({text:buf,kind});buf=''};
 for(const ch of s){const k=/[\u0600-\u06ff]/.test(ch)?'ar':/[A-Za-zÀ-ÿ]/.test(ch)?'lat':'neutral';if(k==='neutral'){buf+=ch;continue}if(kind&&k!==kind){flush();kind=k}else if(!kind)kind=k;buf+=ch}flush();return out;
}
async function translateStrict(text,el){
 const pieces=mixedPieces(text);if(pieces.length<=1){const from=inferLanguage(text,el);return translateChunk(text,from,LANG)}
 let out='';for(const p of pieces){if(p.kind==='neutral'){out+=p.text;continue}const from=p.kind==='ar'?'ar':inferLanguage(p.text,el);out+=from===LANG?p.text:await translateChunk(p.text,from,LANG)}return out;
}
function shouldTranslateNode(n){
 if(!n||n.nodeType!==3||!n.nodeValue.trim())return false;const p=n.parentElement;if(!p)return false;if(p.closest('script,style,svg,.ep-lang-switch'))return false;if(p.closest('.ep-byline'))return false;return true;
}
async function localizeElement(el){
 if(!el||el.dataset.localized===LANG)return;
 el.style.visibility='hidden';
 const nodes=[];const w=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,{acceptNode:n=>shouldTranslateNode(n)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT});while(w.nextNode())nodes.push(w.currentNode);
 try{
   for(const n of nodes){const original=n.nodeValue;if(!original.trim())continue;const from=inferLanguage(original,n.parentElement);if(from===LANG)continue;n.nodeValue=await translateStrict(original,n.parentElement)}
   el.querySelectorAll('[lang]').forEach(x=>{x.lang=LANG;x.dir=LANG==='ar'?'rtl':'ltr'});
   el.dataset.localized=LANG;el.style.visibility='visible';
 }catch(e){
   el.innerHTML=`<div class="ep-localization-unavailable">${T.unavailable}</div>`;el.dataset.localized=LANG;el.style.visibility='visible';
 }
}
function localizeStaticGeneratedLabels(root){
 if(!root)return;
 root.querySelectorAll('.ep-badge').forEach(x=>x.textContent=T.verified);
 root.querySelectorAll('.ep-card .foot a').forEach(x=>x.textContent=T.read);
 root.querySelectorAll('.meta,.ep-breadcrumb').forEach(x=>{let t=x.textContent;for(const map of [SECTION.ar,SECTION.en,SECTION.fr])for(const [k,v] of Object.entries(map))if(v&&S[k])t=t.replace(new RegExp(escRE(v),'g'),S[k]);x.textContent=t});
 const sel=document.getElementById('sectionFilter');if(sel){for(const o of sel.options){if(!o.value)o.textContent=T.allSections;else if(S[o.value])o.textContent=S[o.value]}}
}
function processCards(){
 const cards=[...document.querySelectorAll('.ep-card')];localizeStaticGeneratedLabels(document);
 if(!cards.length)return;
 if(!('IntersectionObserver' in window)){cards.forEach(localizeElement);return}
 const io=new IntersectionObserver(entries=>{entries.forEach(e=>{if(e.isIntersecting){io.unobserve(e.target);localizeElement(e.target)}})},{rootMargin:'650px 0px'});cards.forEach(c=>{if(c.dataset.localized!==LANG){c.style.visibility='hidden';io.observe(c)}});
}
async function processFeature(){
 const art=document.getElementById('articleView');if(!art)return;
 localizeStaticGeneratedLabels(art);art.style.visibility='hidden';
 const lead=art.querySelector('.ep-article-lead');if(lead){const strong=lead.querySelector('strong');const by=strong?strong.outerHTML:'';lead.innerHTML=by+(by?' · ':'')+T.translated;}
 const proof=art.querySelector('.ep-proof');if(proof)proof.innerHTML='<strong>'+T.integrityTitle+'</strong>'+T.integrity;
 art.querySelectorAll('.ep-article-actions a').forEach(a=>{const h=a.getAttribute('href')||'';a.textContent=h.includes('library')?T.library:T.allArticles;a.setAttribute('href',localeUrl(h))});
 await localizeElement(art);
}
function observeRender(){
 const target=document.getElementById('articleFeed')||document.getElementById('articleView');if(!target)return;
 let timer=null;const run=()=>{clearTimeout(timer);timer=setTimeout(()=>{if(document.body.dataset.page==='feature')processFeature();else processCards();},30)};
 new MutationObserver(run).observe(target,{childList:true,subtree:true});run();
}
localizeShell();
const style=document.createElement('style');style.textContent='.ep-lang-switch{display:flex;gap:4px;margin-inline-start:8px}.ep-lang-switch a{font:700 10px/1 Poppins,Cairo,sans-serif;color:#e6eee9;text-decoration:none;border:1px solid #ffffff35;border-radius:7px;padding:6px 7px}.ep-lang-switch a.active{background:#fff;color:#0b4c38}.ep-localization-unavailable{padding:18px;border:1px solid #d8cba9;border-radius:10px;background:#fffaf0;color:#675735;font-size:13px;line-height:1.8}html[dir=ltr] .ep-card:before{right:auto;left:0;border-radius:0 3px 3px 0}html[dir=ltr] .ep-proof{border-right:0;border-left:3px solid var(--g3)}';document.head.appendChild(style);
observeRender();
})();