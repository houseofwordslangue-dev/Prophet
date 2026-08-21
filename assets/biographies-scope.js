(function(){'use strict';
const excluded=new Set([
'النبي','الأسرة','الأسرة النبوية','العائلة النبوية','الأجداد','الصحابة','التابعون','تابعو التابعين','الرواة',
'Prophet','Family','Prophetic Household','Prophetic Family','Ancestors','Companions','Followers','Followers of Followers','Narrators',
'Prophète','Famille','Famille prophétique','Ascendance','Compagnons','Successeurs','Successeurs des successeurs','Transmetteurs'
]);
function hasPrimaryHome(card){
 const metas=[...card.querySelectorAll('.meta')].map(x=>x.textContent.trim()).filter(Boolean);
 return metas.some(meta=>excluded.has(meta)||[...excluded].some(label=>meta===label||meta.startsWith(label+' ·')||meta.startsWith(label+' —')));
}
function filter(){
 const grid=document.getElementById('peopleGrid');if(!grid)return;
 grid.querySelectorAll('.person-card').forEach(card=>{if(hasPrimaryHome(card))card.remove()});
 const st=document.getElementById('peopleStatus');if(st){const n=grid.querySelectorAll('.person-card').length;st.textContent=(document.documentElement.lang==='ar'?`${n} ترجمة لأشخاص لا يملكون قسمًا رئيسيًا آخر`:document.documentElement.lang==='fr'?`${n} biographies sans autre rubrique principale`:`${n} biographies without another primary section`)}}
const mo=new MutationObserver(filter);mo.observe(document.documentElement,{subtree:true,childList:true});document.addEventListener('DOMContentLoaded',filter);setTimeout(()=>{filter();mo.disconnect()},30000);
})();