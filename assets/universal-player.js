(function(){
'use strict';
function enhance(media){if(!media||media.getAttribute('data-universal-enhanced'))return;media.setAttribute('data-universal-enhanced','1');media.setAttribute('playsinline','');media.setAttribute('webkit-playsinline','');var wrap=document.createElement('div');wrap.className='universal-media-shell';media.parentNode.insertBefore(wrap,media);wrap.appendChild(media);var bar=document.createElement('div');bar.className='universal-media-tools';bar.innerHTML='<button type="button" data-skip="-10">−10s</button><button type="button" data-skip="10">+10s</button><label><span class="sr-only">Speed</span><select data-speed><option value="0.75">0.75×</option><option value="1" selected>1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label><button type="button" data-fullscreen>⛶</button>';wrap.appendChild(bar);var bs=bar.getElementsByTagName('button'),i;for(i=0;i<bs.length;i++){if(bs[i].getAttribute('data-skip'))bs[i].onclick=function(){try{media.currentTime=Math.max(0,Math.min(media.duration||1e12,media.currentTime+parseInt(this.getAttribute('data-skip'),10)))}catch(e){}};else bs[i].onclick=function(){var fn=wrap.requestFullscreen||wrap.webkitRequestFullscreen;if(fn)fn.call(wrap)}}var sel=bar.getElementsByTagName('select')[0];sel.onchange=function(){try{media.playbackRate=parseFloat(this.value)||1}catch(e){}};media.onerror=function(){wrap.classList.add('media-load-error')};}
function scan(root){root=root||document;var a=root.querySelectorAll?root.querySelectorAll('audio,video'):[];for(var i=0;i<a.length;i++)enhance(a[i])}
function medium(item){if(item.medium)return item.medium;if(item.kind==='audio')return'audio';var c=String(item.category||'').toLowerCase();if(c==='audio'||c==='podcast')return c;return'video'}
function localEndpoint(item){return item&&item.id?'/api/media/stream?id='+encodeURIComponent(item.id):''}
function createNative(item,host,src){var tag=(medium(item)==='audio'||medium(item)==='podcast')?'audio':'video';var el=document.createElement(tag);el.controls=true;el.autoplay=true;el.preload='metadata';el.src=src;if(item.thumbnail&&tag==='video')el.poster=item.thumbnail;host.appendChild(el);enhance(el);el.play().catch(function(){});return el}
function playItem(item,host){
 if(!host)return;
 host.innerHTML='';
 var local=item.localUrl||'';
 if(local){createNative(item,host,local);return;}
 var endpoint=localEndpoint(item);
 if(endpoint){
  var el=createNative(item,host,endpoint);
  el.addEventListener('error',function(){
   host.innerHTML='<div class="media-external-note"><strong>تعذر تشغيل البث المحلي.</strong><br>شغّل الموقع بواسطة <code>python server.py</code> ليقوم الخادم المحلي بجلب الوسائط وتشغيلها داخل المشغل بدون صفحة موافقة YouTube.</div>';
  },{once:true});
  return;
 }
 var note=document.createElement('div');note.className='media-external-note';note.innerHTML='<strong>لا يوجد معرّف وسائط صالح للتشغيل المحلي.</strong>';host.appendChild(note);
}
window.UniversalMediaPlayer={scan:scan,enhance:enhance,playItem:playItem};if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){scan(document)});else scan(document);
})();
