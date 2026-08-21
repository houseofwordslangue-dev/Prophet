(function(){
'use strict';
const LABELS={
 light:'النور',prophet:'النبي',messenger:'الرسول',human:'الإنسان',mercy:'الرحمة العظمى',
 'prophetic-household':'الأسرة النبوية','prophetic-family':'العائلة النبوية',family:'الأسرة النبوية',
 companions:'الصحابة',followers:'التابعون','followers-followers':'تابعو التابعين',beloved:'أحباب الله',
 library:'المكتبة',sources:'المكتبة',media:'الوسائط',forums:'المنتدى',forum:'المنتدى',children:'للأطفال'
};
const MENU=[
 ['محمد ﷺ',null,[['النور','editorial.html?section=light'],['النبي','editorial.html?section=prophet'],['الرسول','editorial.html?section=messenger'],['الإنسان','editorial.html?section=human'],['الرحمة العظمى','editorial.html?section=mercy']],'reserved'],
 ['الأسرة النبوية',null,[['الأبناء','family.html?group=children'],['الأحفاد','family.html?group=grandchildren']]],
 ['العائلة النبوية',null,[['الوالدان','editorial.html?section=prophetic-family&subsection=parents'],['الأجداد','editorial.html?section=prophetic-family&subsection=ancestors'],['الأعمام والعمات','editorial.html?section=prophetic-family&subsection=paternal-relatives'],['الأخوال والخالات','editorial.html?section=prophetic-family&subsection=maternal-relatives'],['أبناء العمومة','editorial.html?section=prophetic-family&subsection=cousins'],['الأصهار','editorial.html?section=prophetic-family&subsection=in-laws'],['سائر الأقارب','editorial.html?section=prophetic-family']]],
 ['الصحابة','editorial.html?section=companions',[['التراجم','editorial.html?section=companions&subsection=biographies'],['العلم والأقوال','editorial.html?section=companions&subsection=knowledge'],['المواقف والأحداث','editorial.html?section=companions&subsection=events']]],
 ['التابعون','editorial.html?section=followers',[['التراجم','editorial.html?section=followers']]],
 ['تابعو التابعين','editorial.html?section=followers-followers',[['التراجم','editorial.html?section=followers-followers']]],
 ['أحباب الله','editorial.html?section=beloved',[['السير والتراجم','editorial.html?section=beloved'],['للأطفال · الأخلاق','editorial.html?section=beloved&subsection=children-character'],['للأطفال · العلم والمعرفة','editorial.html?section=beloved&subsection=children-knowledge'],['للأطفال · الرحمة والرفق','editorial.html?section=beloved&subsection=children-mercy'],['للأطفال · الأسرة والصحبة','editorial.html?section=beloved&subsection=children-family']]],
 ['المكتبة','library.html',[['الكتب','library.html?type=books'],['المخطوطات','library.html?type=manuscripts'],['الدراسات والبحوث','library.html?type=studies'],['التفسير وعلوم القرآن','library.html?type=quran'],['الحديث وشروحه','library.html?type=hadith'],['السيرة والشمائل','library.html?type=seerah'],['أهل البيت','library.html?type=ahl-al-bayt'],['PDF','library.html?format=pdf'],['EPUB','library.html?format=epub']]],
 ['الوسائط','media.html',[['الفيديو','media.html?type=video'],['الصوتيات','media.html?type=audio'],['المحاضرات','media.html?type=lecture'],['البودكاست','media.html?type=podcast'],['الوثائقيات','media.html?type=documentary'],['الأبحاث المرئية والمسموعة','media.html?type=research']]],
 ['المنتدى','editorial.html?section=forums',[]]
];
const COMMANDS=[
 ['السيرة','ابدأ من سيرة النبي ﷺ','editorial.html?section=prophet','⌁'],
 ['الأسرة النبوية','الأبناء والأحفاد','family.html','♢'],
 ['الصحابة','التراجم والعلم والمواقف','editorial.html?section=companions','◉'],
 ['المكتبة','الكتب والمخطوطات والدراسات','library.html','▤'],
 ['الوسائط','الصوتيات والفيديو والمحاضرات','media.html','▷'],
 ['الأشخاص','الفهرس العام للتراجم','people.html?lang=ar','◎']
];
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function mount(){
 if(document.querySelector('.pm-menu-toggle'))return;
 const toggle=document.createElement('button');toggle.className='pm-menu-toggle';toggle.type='button';toggle.setAttribute('aria-label','فتح القائمة');toggle.setAttribute('aria-expanded','false');toggle.innerHTML='☰';
 const back=document.createElement('div');back.className='pm-menu-backdrop';
 const drawer=document.createElement('aside');drawer.className='pm-drawer';drawer.setAttribute('aria-label','القائمة الرئيسية');
 let nav='';
 MENU.forEach(([label,href,children,flag],i)=>{
   if(children&&children.length){nav+=`<section class="pm-group${i===0?' open':''}"><button type="button">${esc(label)}</button>${flag==='reserved'?'<span class="pm-reserved">هذه الموضوعات الخمسة خاصة بالنبي ﷺ وحده.</span>':''}<div class="pm-sub">${children.map(x=>`<a href="${esc(x[1])}">${esc(x[0])}</a>`).join('')}</div></section>`}
   else nav+=`<a class="pm-single" href="${esc(href||'#')}">${esc(label)}</a>`;
 });
 drawer.innerHTML=`<div class="pm-drawer-head"><div><strong>محمد ﷺ</strong><small>سيرة موثّقة · مكتبة · معرفة</small></div><button class="pm-close" type="button" aria-label="إغلاق">×</button></div><button class="pm-command-launch" type="button" data-open-command><span>⌕</span><b>بحث واستكشاف سريع</b><kbd>Ctrl K</kbd></button><nav class="pm-nav">${nav}</nav>`;
 document.body.append(toggle,back,drawer);
 const open=()=>{document.documentElement.classList.add('pm-menu-open');toggle.setAttribute('aria-expanded','true')};
 const close=()=>{document.documentElement.classList.remove('pm-menu-open');toggle.setAttribute('aria-expanded','false')};
 toggle.addEventListener('click',()=>document.documentElement.classList.contains('pm-menu-open')?close():open());back.addEventListener('click',close);drawer.querySelector('.pm-close').addEventListener('click',close);
 drawer.querySelectorAll('.pm-group>button').forEach(b=>b.addEventListener('click',()=>b.parentElement.classList.toggle('open')));
 document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});
}
function mountCommand(){
 if(document.querySelector('.pm-command'))return;
 const wrap=document.createElement('div');wrap.className='pm-command';wrap.hidden=true;
 wrap.innerHTML=`<div class="pm-command-backdrop" data-command-close></div><section class="pm-command-panel" role="dialog" aria-modal="true" aria-label="البحث والاستكشاف"><div class="pm-command-search"><span>⌕</span><input type="search" placeholder="ابحث أو اختر مساراً…" autocomplete="off"><button type="button" data-command-close aria-label="إغلاق">×</button></div><div class="pm-command-list">${COMMANDS.map(([title,desc,href,icon])=>`<a href="${esc(href)}" data-command-item><span>${icon}</span><div><b>${esc(title)}</b><small>${esc(desc)}</small></div></a>`).join('')}</div><div class="pm-command-foot"><span>↑ ↓ للتنقل</span><span>Enter للفتح</span><span>Esc للإغلاق</span></div></section>`;
 document.body.appendChild(wrap);
 const input=wrap.querySelector('input'),items=[...wrap.querySelectorAll('[data-command-item]')];let active=0;
 const paint=()=>items.forEach((x,i)=>x.classList.toggle('active',i===active&&!x.hidden));
 const filter=()=>{const q=(input.value||'').trim().toLowerCase();items.forEach(x=>x.hidden=!!q&&!x.textContent.toLowerCase().includes(q));const first=items.findIndex(x=>!x.hidden);active=first<0?0:first;paint()};
 const open=()=>{wrap.hidden=false;document.documentElement.classList.add('pm-command-open');setTimeout(()=>input.focus(),0);filter()};
 const close=()=>{wrap.hidden=true;document.documentElement.classList.remove('pm-command-open');input.value=''};
 document.addEventListener('click',e=>{if(e.target.closest('[data-open-command]')){e.preventDefault();open()}if(e.target.closest('[data-command-close]'))close()});
 document.addEventListener('keydown',e=>{
   const tag=(document.activeElement&&document.activeElement.tagName)||'';
   if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();wrap.hidden?open():close();return}
   if(e.key==='/'&&!/INPUT|TEXTAREA|SELECT/.test(tag)&&wrap.hidden){e.preventDefault();open();return}
   if(wrap.hidden)return;
   if(e.key==='Escape'){e.preventDefault();close();return}
   if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();const visible=items.map((x,i)=>[x,i]).filter(([x])=>!x.hidden).map(([,i])=>i);if(!visible.length)return;let pos=visible.indexOf(active);pos=(pos+(e.key==='ArrowDown'?1:-1)+visible.length)%visible.length;active=visible[pos];paint();items[active].scrollIntoView({block:'nearest'})}
   if(e.key==='Enter'&&document.activeElement===input){const chosen=items[active];if(chosen&&!chosen.hidden)location.href=chosen.href;else if(input.value.trim())location.href='editorial.html?q='+encodeURIComponent(input.value.trim())}
 });
 input.addEventListener('input',filter);items.forEach((x,i)=>x.addEventListener('mouseenter',()=>{active=i;paint()}));
}
function mountReadingProgress(){
 if(document.querySelector('.pm-reading-progress'))return;
 const likely=/feature\.html|reader\.html|person\.html/.test(location.pathname)||document.querySelector('.ep-article,.person-view article,.text-content');
 if(!likely)return;
 const bar=document.createElement('div');bar.className='pm-reading-progress';bar.setAttribute('aria-hidden','true');bar.innerHTML='<span></span>';document.body.appendChild(bar);
 const fill=bar.firstElementChild,update=()=>{const h=document.documentElement.scrollHeight-innerHeight;const p=h>0?Math.min(1,Math.max(0,scrollY/h)):0;fill.style.transform=`scaleX(${p})`};
 addEventListener('scroll',update,{passive:true});addEventListener('resize',update,{passive:true});update();
}
function mountMobileDock(){
 if(document.querySelector('.pm-mobile-dock'))return;
 const dock=document.createElement('nav');dock.className='pm-mobile-dock';dock.setAttribute('aria-label','وصول سريع');dock.innerHTML='<a href="editorial.html"><span>⌂</span><small>الرئيسية</small></a><button type="button" data-open-command><span>⌕</span><small>بحث</small></button><a href="library.html"><span>▤</span><small>المكتبة</small></a><a href="media.html"><span>▷</span><small>الوسائط</small></a>';document.body.appendChild(dock);
}
function relabel(){
 document.querySelectorAll('#sectionFilter option').forEach(o=>{if(LABELS[o.value])o.textContent=LABELS[o.value]});
 document.querySelectorAll('.ep-card .meta,.ep-article .meta').forEach(el=>{for(const [k,v] of Object.entries(LABELS)){if(el.textContent.startsWith(k+' ·'))el.textContent=v+el.textContent.slice(k.length)}});
}
function sourceOnlyPublicView(){
 document.querySelectorAll('[data-ai-generated="true"],[data-ai-content="true"],[data-content-origin="ai"]').forEach(el=>el.remove());
 const status=document.getElementById('publicationStatus');
 if(status&&/الذكاء الاصطناعي|AI/i.test(status.textContent||'')){
   status.textContent=(status.textContent||'').replace(/\s*·\s*المحتوى الجوهري المولّد بالذكاء الاصطناعي:\s*0/gi,'').replace(/\s*·\s*AI[^·]*/gi,'');
 }
 document.querySelectorAll('.ep-card,.ep-article,.person-view article').forEach(el=>{
   const flagged=el.matches('[data-ai-generated="true"],[data-ai-content="true"],[data-content-origin="ai"]')||el.querySelector('[data-ai-generated="true"],[data-ai-content="true"],[data-content-origin="ai"]');
   if(flagged)el.remove();
 });
}
function applyQuery(){
 const q=new URLSearchParams(location.search),section=q.get('section'),sub=q.get('subsection'),searchQ=q.get('q');
 if(section){let tries=0;const t=setInterval(()=>{const f=document.getElementById('sectionFilter');if(f&&[...f.options].some(o=>o.value===section)){f.value=section;f.dispatchEvent(new Event('change'));clearInterval(t)}else if(++tries>160)clearInterval(t)},50)}
 if(sub){const search=document.getElementById('articleSearch');if(search){search.value=sub.replace(/[-_]/g,' ');search.dispatchEvent(new Event('input'))}}
 if(searchQ){let tries=0;const t=setInterval(()=>{const search=document.getElementById('articleSearch');if(search){search.value=searchQ;search.dispatchEvent(new Event('input'));search.focus();clearInterval(t)}else if(++tries>100)clearInterval(t)},50)}
 const type=q.get('type');if(type&&document.getElementById('mediaFilter')){const f=document.getElementById('mediaFilter');if([...f.options].some(o=>o.value===type)){f.value=type;f.dispatchEvent(new Event('change'))}}
}
function observe(){relabel();sourceOnlyPublicView();const mo=new MutationObserver(()=>{relabel();sourceOnlyPublicView()});mo.observe(document.documentElement,{subtree:true,childList:true,characterData:true});setTimeout(()=>mo.disconnect(),30000)}
document.addEventListener('DOMContentLoaded',()=>{mount();mountCommand();mountReadingProgress();mountMobileDock();applyQuery();observe()});
})();
