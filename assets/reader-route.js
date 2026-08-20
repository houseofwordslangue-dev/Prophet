/* Route existing Library read actions through the branded reader shell. */
(function(){
'use strict';
function bookIdFrom(anchor){const card=anchor.closest('.book-card');if(card){const open=card.querySelector('[data-open]');if(open)return open.dataset.open||''}const dialog=anchor.closest('#bookDialog');if(dialog){const id=dialog.querySelector('[data-favorite]')?.dataset.favorite||dialog.querySelector('[data-open]')?.dataset.open;return id||''}return''}
function route(anchor){const href=anchor.getAttribute('href');if(!href||href==='#'||href.startsWith('reader.html'))return null;const id=bookIdFrom(anchor);if(!id)return null;const u=new URL('reader.html',location.href);u.searchParams.set('id',id);u.searchParams.set('src',new URL(href,location.href).href);u.searchParams.set('return','library.html'+location.search+location.hash);return u.href}
document.addEventListener('click',e=>{const a=e.target.closest('.book-card .actions a.primary,#bookDialog .dialog-actions a.primary');if(!a)return;const target=route(a);if(!target)return;e.preventDefault();location.href=target},true);
})();
