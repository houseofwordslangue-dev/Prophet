(function(){
'use strict';
function safePlay(media){
 var src=media.getAttribute('src');
 if(!src){var saved=media.getAttribute('data-player-src');if(saved){media.src=saved;media.load();}}
 var p=media.play();if(p&&p.catch)p.catch(function(){});
}
function stopMedia(media){
 try{media.pause()}catch(e){}
 try{media.currentTime=0}catch(e){}
 var src=media.getAttribute('src');if(src)media.setAttribute('data-player-src',src);
 media.removeAttribute('src');
 try{media.load()}catch(e){}
}
function enhance(media){
 if(!media||media.getAttribute('data-universal-enhanced'))return;
 media.setAttribute('data-universal-enhanced','1');
 media.setAttribute('playsinline','');media.setAttribute('webkit-playsinline','');
 if(media.getAttribute('src'))media.setAttribute('data-player-src',media.getAttribute('src'));
 var wrap=document.createElement('div');wrap.className='universal-media-shell';media.parentNode.insertBefore(wrap,media);wrap.appendChild(media);
 var bar=document.createElement('div');bar.className='universal-media-tools';
 bar.innerHTML='<button type="button" data-action="play" aria-label="تشغيل">▶ تشغيل</button><button type="button" data-action="pause" aria-label="إيقاف مؤقت">⏸ إيقاف مؤقت</button><button type="button" data-action="stop" aria-label="إيقاف">■ إيقاف</button><button type="button" data-skip="-10" aria-label="الرجوع عشر ثوان">−10s</button><button type="button" data-skip="10" aria-label="التقديم عشر ثوان">+10s</button><button type="button" data-action="mute" aria-label="كتم الصوت">🔇 كتم</button><label class="volume-control"><span class="sr-only">مستوى الصوت</span><input type="range" min="0" max="1" step="0.05" value="1" data-volume aria-label="مستوى الصوت"></label><label><span class="sr-only">السرعة</span><select data-speed aria-label="سرعة التشغيل"><option value="0.75">0.75×</option><option value="1" selected>1×</option><option value="1.25">1.25×</option><option value="1.5">1.5×</option><option value="2">2×</option></select></label><button type="button" data-action="fullscreen" aria-label="ملء الشاشة">⛶ ملء الشاشة</button>';
 wrap.appendChild(bar);
 var playBtn=bar.querySelector('[data-action="play"]'),pauseBtn=bar.querySelector('[data-action="pause"]'),stopBtn=bar.querySelector('[data-action="stop"]'),muteBtn=bar.querySelector('[data-action="mute"]'),fullBtn=bar.querySelector('[data-action="fullscreen"]');
 playBtn.onclick=function(){safePlay(media)};
 pauseBtn.onclick=function(){try{media.pause()}catch(e){}};
 stopBtn.onclick=function(){stopMedia(media)};
 var skips=bar.querySelectorAll('[data-skip]');for(var i=0;i<skips.length;i++)skips[i].onclick=function(){try{var delta=parseInt(this.getAttribute('data-skip'),10)||0;var dur=isFinite(media.duration)?media.duration:1e12;media.currentTime=Math.max(0,Math.min(dur,(media.currentTime||0)+delta))}catch(e){}};
 muteBtn.onclick=function(){media.muted=!media.muted;this.textContent=media.muted?'🔊 إلغاء الكتم':'🔇 كتم';this.setAttribute('aria-pressed',media.muted?'true':'false')};
 var vol=bar.querySelector('[data-volume]');vol.oninput=function(){var v=Math.max(0,Math.min(1,parseFloat(this.value)||0));media.volume=v;if(v>0&&media.muted){media.muted=false;muteBtn.textContent='🔇 كتم';muteBtn.setAttribute('aria-pressed','false')}};
 var sel=bar.querySelector('[data-speed]');sel.onchange=function(){try{media.playbackRate=parseFloat(this.value)||1}catch(e){}};
 var fs=wrap.requestFullscreen||wrap.webkitRequestFullscreen;if(fs){fullBtn.onclick=function(){var fn=wrap.requestFullscreen||wrap.webkitRequestFullscreen;if(fn)fn.call(wrap)}}else{fullBtn.remove()}
 media.addEventListener('volumechange',function(){if(!media.muted)vol.value=String(media.volume)});
 media.onerror=function(){wrap.classList.add('media-load-error')};
}
function scan(root){root=root||document;var a=root.querySelectorAll?root.querySelectorAll('audio,video'):[];for(var i=0;i<a.length;i++)enhance(a[i])}
function medium(item){if(item.medium)return item.medium;if(item.kind==='audio')return'audio';var c=String(item.category||'').toLowerCase();if(c==='audio'||c==='podcast')return c;return'video'}
function localEndpoint(item){return item&&item.id?'/api/media/stream?id='+encodeURIComponent(item.id):''}
function createNative(item,host,src){var tag=(medium(item)==='audio'||medium(item)==='podcast')?'audio':'video';var el=document.createElement(tag);el.controls=true;el.autoplay=true;el.preload='metadata';el.src=src;el.setAttribute('data-player-src',src);if(item.thumbnail&&tag==='video')el.poster=item.thumbnail;host.appendChild(el);enhance(el);safePlay(el);return el}
function playItem(item,host){
 if(!host)return;
 var old=host.querySelector('audio,video');if(old)stopMedia(old);
 host.innerHTML='';
 var local=item.localUrl||'';
 if(local){createNative(item,host,local);return;}
 var endpoint=localEndpoint(item);
 if(endpoint){
  var el=createNative(item,host,endpoint);
  el.addEventListener('error',function(){host.innerHTML='<div class="media-external-note"><strong>تعذر تشغيل البث المحلي.</strong><br>شغّل الموقع بواسطة <code>python server.py</code> ليقوم الخادم المحلي بجلب الوسائط وتشغيلها داخل المشغل بدون صفحة موافقة YouTube.</div>'},{once:true});
  return;
 }
 var note=document.createElement('div');note.className='media-external-note';note.innerHTML='<strong>لا يوجد معرّف وسائط صالح للتشغيل المحلي.</strong>';host.appendChild(note);
}
window.UniversalMediaPlayer={scan:scan,enhance:enhance,playItem:playItem,stop:stopMedia};if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',function(){scan(document)});else scan(document);
})();
