(function(){
'use strict';
/* Public editorial cleanup: operational/editorial workflow language must never leak into reader-facing content. */
const AR_PATTERNS=[
 /معاينة(?:\s+ديناميكية)?[^.!؟\n]*(?:فرع|مراجعة|مستودع|بيانات الموقع)[^.!؟\n]*[.!؟]?/giu,
 /(?:وقد\s+)?ظهر\s+الاسم\s+في\s+\d+\s+من\s+موارد\s+(?:Drive|درايف)[^.!؟\n]*[.!؟]?/giu,
 /تُ?ستخدم\s+هذه\s+الموارد\s+للتحقق\s+والتوسعة[^.!؟\n]*[.!؟]?/giu,
 /ولا?\s*يُنقل\s+(?:OCR|النص\s+الممسوح)[^.!؟\n]*قبل\s+المراجعة[^.!؟\n]*[.!؟]?/giu,
 /قد\s+أفردت\s+لها?\s+الشجرة\s+فرعًا\s+مستقلًا\s+حتى\s+لا\s+تختلط[^.!؟\n]*[.!؟]?/giu,
 /تم\s+(?:حجب|استبعاد|عزل)\s+(?:الفصول|المواد|المحتوى)[^.!؟\n]*(?:مؤقتًا|للمراجعة|إعادة\s+البناء|خلل\s+التصنيف)[^.!؟\n]*[.!؟]?/giu,
 /(?:هذه|تلك)\s+(?:معاينة|نسخة)\s+(?:فنية|للمراجعة|تجريبية)[^.!؟\n]*[.!؟]?/giu,
 /(?:الملف|الفصل|السجل)\s+الحالي[^.!؟\n]*(?:خلل|التجميع|المراجعة|المستودع)[^.!؟\n]*[.!؟]?/giu,
 /(?:جارٍ|يجري)\s+(?:تحميل|استخراج|تجميع|مراجعة)\s+(?:المواد|البيانات|السيرة|المحتوى)[^.!؟\n]*[.!؟]?/giu,
 /(?:سياسة|قاعدة)\s+النشر\s*:[^.!؟\n]*[.!؟]?/giu,
 /(?:المحتوى|المادة)\s+(?:الحالية|الحالي)\s+(?:كما|في)\s+(?:المستودع|الفرع|بيانات\s+الموقع)[^.!؟\n]*[.!؟]?/giu,
 /(?:إجمالي|مجموع)\s+الكلمات\s+(?:المعلن|المعلنة)[^.!؟\n]*[.!؟]?/giu,
 /(?:لا\s+توجد|لم\s+توجد)\s+مقاطع\s+مصدرية[^.!؟\n]*(?:السجل|البيانات)[^.!؟\n]*[.!؟]?/giu
];
const EN_PATTERNS=[
 /dynamic preview[^.!?\n]*(?:branch|review|repository|site data)[^.!?\n]*[.!?]?/giu,
 /(?:the\s+)?name (?:was )?found in \d+ (?:Drive )?resources?[^.!?\n]*[.!?]?/giu,
 /these resources are used for (?:verification|expansion)[^.!?\n]*[.!?]?/giu,
 /OCR[^.!?\n]*(?:not|never)[^.!?\n]*(?:quoted|published|copied)[^.!?\n]*review[^.!?\n]*[.!?]?/giu,
 /temporarily (?:hidden|withheld|quarantined|excluded)[^.!?\n]*(?:review|rebuild|classification)[^.!?\n]*[.!?]?/giu,
 /publication (?:policy|rule)\s*:[^.!?\n]*[.!?]?/giu,
 /current (?:file|record|chapter)[^.!?\n]*(?:repository|branch|review|assembly defect)[^.!?\n]*[.!?]?/giu
];
const FR_PATTERNS=[
 /aperçu dynamique[^.!?\n]*(?:branche|révision|dépôt|données du site)[^.!?\n]*[.!?]?/giu,
 /le nom (?:a été|est) trouvé dans \d+ ressources?[^.!?\n]*[.!?]?/giu,
 /ces ressources sont utilisées pour (?:vérification|l’enrichissement|l'enrichissement)[^.!?\n]*[.!?]?/giu,
 /OCR[^.!?\n]*(?:révision|vérification)[^.!?\n]*[.!?]?/giu,
 /(?:masqué|retiré|isolé|exclu) temporairement[^.!?\n]*(?:révision|reconstruction|classement)[^.!?\n]*[.!?]?/giu,
 /politique de publication\s*:[^.!?\n]*[.!?]?/giu
];
const EXACT_OR_PREFIX=[
 'ملاحظة: تم اختصار بقية الفصل في هذه المعاينة',
 'مواد حُجبت لخلل التصنيف',
 'مراجعة الفصول الموسعة',
 'الموضع الصحيح',
 'معاينة ديناميكية',
 'معاينة فنية',
 'تنبيه مراجعة',
 'Public preview',
 'Review notice',
 'Aperçu dynamique',
 'Note de révision'
];
function cleanText(s){
 let out=String(s||'');
 for(const p of [...AR_PATTERNS,...EN_PATTERNS,...FR_PATTERNS]) out=out.replace(p,' ');
 out=out.replace(/[ \t]{2,}/g,' ').replace(/\s+([،؛:,.!?؟])/g,'$1').replace(/\n{3,}/g,'\n\n').trim();
 return out;
}
function isOperationalBlock(el){
 const txt=(el.textContent||'').trim();
 if(!txt)return false;
 return EXACT_OR_PREFIX.some(x=>txt.startsWith(x));
}
function cleanNode(root){
 if(!root||root.nodeType!==1)return;
 if(root.closest&&root.closest('script,style,pre,code,textarea,input,select,option,[data-keep-operational]'))return;
 if(isOperationalBlock(root)){root.remove();return;}
 const w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:n=>{
   const p=n.parentElement;
   if(!p||p.closest('script,style,pre,code,textarea,input,select,option,[data-keep-operational]'))return NodeFilter.FILTER_REJECT;
   return NodeFilter.FILTER_ACCEPT;
 }});
 const nodes=[];while(w.nextNode())nodes.push(w.currentNode);
 for(const n of nodes){const before=n.nodeValue||'',after=cleanText(before);if(after!==before)n.nodeValue=after;}
 root.querySelectorAll('p,div,span,section,article,li,small,.source-passage,.source-meta,.meta,.notice,.status').forEach(el=>{
   if(isOperationalBlock(el)){el.remove();return;}
   if(!el.textContent.trim()&&!el.querySelector('img,audio,video,iframe,button,a,input,select'))el.remove();
 });
}
function run(){cleanNode(document.body)}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
const mo=new MutationObserver(ms=>{for(const m of ms)for(const n of m.addedNodes)if(n.nodeType===1)cleanNode(n)});
mo.observe(document.documentElement,{subtree:true,childList:true});
setTimeout(()=>mo.disconnect(),60000);
window.ProphetPublicContentCleaner={run,cleanText};
})();
