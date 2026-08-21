(function(){
'use strict';
const player=window.UniversalMediaPlayer;
if(!player||typeof player.playItem!=='function')return;
const original=player.playItem.bind(player);
function youtubeId(item){
  const source=String(item&& (item.embed||item.url||item.sourceUrl)||'');
  const match=source.match(/(?:embed\/|v=|youtu\.be\/)([A-Za-z0-9_-]{11})/);
  return match?match[1]:'';
}
player.playItem=function(item,host){
  const start=Math.max(0,Math.floor(Number(item&&item.startSeconds)||0));
  const id=start?youtubeId(item):'';
  if(!id||!host)return original(item,host);
  host.innerHTML='';
  const note=document.createElement('div');
  note.className='media-external-note player-fallback-note';
  note.innerHTML='<strong>تشغيل مادة يوتيوب داخل الموقع.</strong><span>يبدأ التسجيل من الموضع المحدد في الفهرس.</span>';
  host.appendChild(note);
  const frame=document.createElement('iframe');
  frame.src='https://www.youtube-nocookie.com/embed/'+id+'?autoplay=1&rel=0&modestbranding=1&playsinline=1&start='+start;
  frame.title=item.titleAr||item.titleEn||item.titleFr||'فيديو';
  frame.allow='accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture';
  frame.allowFullscreen=true;
  frame.referrerPolicy='strict-origin-when-cross-origin';
  host.appendChild(frame);
  return frame;
};
})();
