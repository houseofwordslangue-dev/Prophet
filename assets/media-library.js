(function(){
'use strict';
const DATA='data/imported_media.json';
const labels={video:'فيديوهات',lecture:'محاضرات',podcast:'بودكاست',research:'أبحاث',documentary:'وثائقيات',audio:'صوتيات'};
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function medium(x){if(x.medium)return x.medium;if(x.kind==='audio')return'audio';if(x.category==='podcast')return'podcast';if(x.category==='research')return'research';if(x.category==='documentary')return'documentary';if(['lecture','course','conference','seerah','hadith','quran','mawlid','madih','hadra','burda','dalail-khayrat','sufi-song','nasheed'].includes(x.category))return'lecture';return'video'}
function title(x){return x.titleAr||x.titleEn||x.titleFr||'مادة وسائط'}
function render(items){const grid=document.getElementById('mediaGrid'),counts=document.getElementById('mediaCounts'),status=document.getElementById('mediaStatus'),q=document.getElementById('mediaSearch'),f=document.getElementById('mediaFilter');
 const tally={video:0,lecture:0,podcast:0,research:0,documentary:0,audio:0};items.forEach(x=>{const m=medium(x);if(m in tally)tally[m]++});counts.innerHTML=Object.keys(tally).map(k=>`<div class="count"><span>${labels[k]}</span><b>${tally[k]}</b></div>`).join('');status.textContent=`${items.length} مادة مفهرسة · التشغيل المحلي متاح للمواد ذات النسخة المحلية`;
 const draw=()=>{const needle=q.value.trim().toLowerCase(),sel=f.value;const rows=items.filter(x=>(!sel||medium(x)===sel)&&(!needle||[title(x),x.creator,x.series,x.category,...(x.topics||[])].join(' ').toLowerCase().includes(needle)));grid.innerHTML=rows.map((x,i)=>`<article class="media-card" data-i="${items.indexOf(x)}"><span class="tag">${esc(labels[medium(x)]||medium(x))}</span><h3>${esc(title(x))}</h3><div class="meta">${esc(x.creator||x.series||'')} ${x.language?'· '+esc(x.language):''}</div><div class="meta">${x.localUrl?'نسخة محلية':'مصدر خارجي مفهرس'}</div></article>`).join('')||'<div>لا توجد نتائج.</div>';grid.querySelectorAll('.media-card').forEach(card=>card.addEventListener('click',()=>play(items[Number(card.dataset.i)])));};
 function play(x){document.getElementById('mediaNow').innerHTML=`<strong>${esc(title(x))}</strong><br>${esc(x.creator||x.series||'')}<br><small>${esc((x.topics||[]).join(' · '))}</small>`;window.UniversalMediaPlayer.playItem(x,document.getElementById('mediaPlayer'))}
 q.addEventListener('input',draw);f.addEventListener('change',draw);draw();}
fetch(DATA,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('الفهرس غير موجود بعد');return r.json()}).then(j=>render(j.items||[])).catch(e=>{document.getElementById('mediaStatus').textContent='تعذر تحميل فهرس الوسائط: '+e.message});
})();
