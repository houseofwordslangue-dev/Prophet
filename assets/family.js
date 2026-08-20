(function(){
'use strict';
const PEOPLE='data/people.json', GROUPS='data/family_groups.json';
const P=new URLSearchParams(location.search);let lang=P.get('lang')||localStorage.getItem('pm-lang')||'ar';if(!['ar','en','fr'].includes(lang))lang='ar';localStorage.setItem('pm-lang',lang);
const UI={
 ar:{dir:'rtl',title:'آل البيت والأسرة',intro:'الأقارب مصنفون بحسب صلة القرابة المثبتة. كل اسم يفتح صفحته المستقلة، وتُضاف السيرة عند وجود مادة مصدرية موثقة.',search:'ابحث في أفراد الأسرة…',all:'كل الأقسام',empty:'لا توجد أسماء مطابقة.',person:'فتح الصفحة'},
 en:{dir:'ltr',title:'Household and Family',intro:'Relatives are grouped only by established kinship. Every name opens a dedicated page; biography is added when verified source material is available.',search:'Search family members…',all:'All groups',empty:'No matching individuals.',person:'Open page'},
 fr:{dir:'ltr',title:'Maison et famille',intro:'Les proches sont classés uniquement selon un lien de parenté établi. Chaque nom ouvre une page dédiée ; la biographie est ajoutée lorsqu’une source vérifiée est disponible.',search:'Rechercher un membre de la famille…',all:'Toutes les catégories',empty:'Aucune personne correspondante.',person:'Ouvrir la page'}
};
const t=UI[lang];document.documentElement.lang=lang;document.documentElement.dir=t.dir;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function n(p){return p?.name?.[lang]||p?.name?.ar||p?.id||''}
function passageCount(p){return (p?.sourcePassages||[]).filter(x=>(x.language||'ar')===lang).length}
Promise.all([fetch(PEOPLE,{cache:'no-store'}).then(r=>r.ok?r.json():{people:[]}),fetch(GROUPS,{cache:'no-store'}).then(r=>r.json())]).then(([pd,gd])=>{
 const by=new Map((pd.people||[]).map(p=>[p.id,p]));
 const title=document.getElementById('familyTitle'),intro=document.getElementById('familyIntro'),search=document.getElementById('familySearch'),filter=document.getElementById('familyFilter'),grid=document.getElementById('familyGrid');
 title.textContent=t.title;intro.textContent=t.intro;search.placeholder=t.search;document.title=t.title+' — Muhammad';
 filter.innerHTML=`<option value="">${esc(t.all)}</option>`+(gd.groups||[]).map(g=>`<option value="${esc(g.id)}">${esc(g.labels?.[lang]||g.labels?.ar||g.id)}</option>`).join('');
 function draw(){const q=(search.value||'').trim().toLowerCase(),f=filter.value;let html='';for(const g of gd.groups||[]){if(f&&g.id!==f)continue;const rows=(g.people||[]).map(id=>by.get(id)).filter(Boolean).filter(p=>!q||[p.name?.ar,p.name?.en,p.name?.fr].join(' ').toLowerCase().includes(q));if(!rows.length)continue;html+=`<section class="family-group"><h2>${esc(g.labels?.[lang]||g.labels?.ar||g.id)}</h2><div class="family-people">${rows.map(p=>`<a class="family-person" href="person.html?id=${encodeURIComponent(p.id)}&lang=${lang}"><strong>${esc(n(p))}</strong><span>${passageCount(p)} ${lang==='ar'?'مقطع موثّق':lang==='fr'?'passage(s) vérifié(s)':'verified passage(s)'}</span><b>${esc(t.person)} ↗</b></a>`).join('')}</div></section>`}grid.innerHTML=html||`<div class="family-empty">${esc(t.empty)}</div>`}
 search.addEventListener('input',draw);filter.addEventListener('change',draw);draw();
}).catch(e=>{document.getElementById('familyGrid').innerHTML='<div class="family-empty">'+esc(e.message)+'</div>'});
})();
