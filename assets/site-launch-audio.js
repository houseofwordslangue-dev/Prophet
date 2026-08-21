(function(){
'use strict';
if(window.__siteLaunchAudioMounted)return;
window.__siteLaunchAudioMounted=true;
const VIDEO_ID='M64ELezZihw';
const lang=(document.documentElement.lang||'ar').toLowerCase().slice(0,2);
const T={
 ar:{title:'التسجيل الصوتي',mute:'كتم الصوت',unmute:'تشغيل الصوت',volume:'مستوى الصوت',source:'المصدر على YouTube',blocked:'اضغط في أي مكان لبدء التشغيل'},
 en:{title:'Audio recording',mute:'Mute',unmute:'Unmute',volume:'Volume',source:'Source on YouTube',blocked:'Click anywhere to start playback'},
 fr:{title:'Enregistrement audio',mute:'Couper le son',unmute:'Activer le son',volume:'Volume',source:'Source sur YouTube',blocked:'Cliquez n’importe où pour démarrer la lecture'}
};
const tr=T[lang]||T.ar;
function mount(){
 if(document.getElementById('siteLaunchAudio'))return;
 const wrap=document.createElement('section');wrap.id='siteLaunchAudio';wrap.setAttribute('aria-label',tr.title);
 wrap.innerHTML=`<div class="sla-head"><strong>${tr.title}</strong><button type="button" class="sla-collapse" aria-label="${tr.title}">−</button></div><div class="sla-body"><div id="siteLaunchYoutube" class="sla-video" aria-label="${tr.source}"></div><div class="sla-controls"><button type="button" class="sla-mute" aria-pressed="false">🔊 <span>${tr.mute}</span></button><label><span>${tr.volume}</span><input class="sla-volume" type="range" min="0" max="100" step="1" value="35"></label></div><small class="sla-status" aria-live="polite"></small><a class="sla-source" href="https://www.youtube.com/watch?v=${VIDEO_ID}" target="_blank" rel="noopener noreferrer">${tr.source}</a></div>`;
 const style=document.createElement('style');
 style.textContent=`#siteLaunchAudio{position:fixed;z-index:2147483000;right:14px;bottom:14px;width:min(250px,calc(100vw - 28px));background:rgba(7,29,24,.96);color:#f7fbf8;border:1px solid rgba(219,193,138,.42);border-radius:16px;box-shadow:0 18px 55px rgba(0,0,0,.38);backdrop-filter:blur(16px);font-family:inherit;overflow:hidden}#siteLaunchAudio .sla-head{display:flex;align-items:center;justify-content:space-between;padding:9px 11px;background:rgba(255,255,255,.05)}#siteLaunchAudio .sla-head strong{font-size:12px}#siteLaunchAudio button{font:inherit;color:inherit;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:10px;cursor:pointer}#siteLaunchAudio .sla-collapse{width:30px;height:30px}#siteLaunchAudio .sla-body{padding:10px}#siteLaunchAudio.collapsed .sla-body{display:none}#siteLaunchAudio .sla-video{width:220px;max-width:100%;height:200px;margin:auto;border-radius:12px;overflow:hidden;background:#000}#siteLaunchAudio iframe{width:100%;height:100%;border:0}#siteLaunchAudio .sla-controls{display:grid;gap:8px;margin-top:9px}#siteLaunchAudio .sla-mute{padding:8px 10px;display:flex;align-items:center;justify-content:center;gap:6px}#siteLaunchAudio label{display:grid;grid-template-columns:auto 1fr;align-items:center;gap:8px;font-size:11px}#siteLaunchAudio input[type=range]{width:100%;accent-color:#dbc18a}#siteLaunchAudio .sla-status{display:block;min-height:15px;margin-top:6px;color:#d7e8df;font-size:10px}#siteLaunchAudio .sla-source{display:block;margin-top:4px;color:#dbc18a;font-size:10px;text-decoration:none}@media(max-width:560px){#siteLaunchAudio{right:8px;bottom:8px;width:220px}#siteLaunchAudio .sla-video{height:200px}}`;
 document.head.appendChild(style);document.body.appendChild(wrap);
 const collapse=wrap.querySelector('.sla-collapse');collapse.addEventListener('click',()=>{wrap.classList.toggle('collapsed');collapse.textContent=wrap.classList.contains('collapsed')?'+':'−'});
 loadPlayer(wrap);
}
function loadPlayer(wrap){
 const mute=wrap.querySelector('.sla-mute'),vol=wrap.querySelector('.sla-volume'),status=wrap.querySelector('.sla-status');
 let player=null;let desiredVolume=Number(localStorage.getItem('siteLaunchVolume')||35);if(!Number.isFinite(desiredVolume))desiredVolume=35;desiredVolume=Math.max(0,Math.min(100,desiredVolume));vol.value=String(desiredVolume);
 function updateMute(){if(!player||typeof player.isMuted!=='function')return;const m=player.isMuted();mute.setAttribute('aria-pressed',String(m));mute.innerHTML=m?`🔇 <span>${tr.unmute}</span>`:`🔊 <span>${tr.mute}</span>`;}
 function start(){if(!player||typeof player.playVideo!=='function')return;try{player.setVolume(desiredVolume);player.playVideo();status.textContent='';}catch(_){}}
 function armGesture(){status.textContent=tr.blocked;const go=()=>{start();document.removeEventListener('pointerdown',go,true);document.removeEventListener('keydown',go,true);};document.addEventListener('pointerdown',go,true);document.addEventListener('keydown',go,true);}
 function createPlayer(){if(player||!window.YT||!YT.Player)return;player=new YT.Player('siteLaunchYoutube',{width:'220',height:'200',videoId:VIDEO_ID,playerVars:{autoplay:1,playsinline:1,controls:0,rel:0,modestbranding:1,origin:location.origin},events:{onReady:function(){player.setVolume(desiredVolume);start();setTimeout(()=>{try{if(player.getPlayerState()!==YT.PlayerState.PLAYING)armGesture();}catch(_){armGesture();}},900);updateMute();},onStateChange:function(e){if(e.data===YT.PlayerState.PLAYING)status.textContent='';}}});}
 if(window.YT&&YT.Player){createPlayer();}else{const previous=window.onYouTubeIframeAPIReady;window.onYouTubeIframeAPIReady=function(){if(typeof previous==='function')previous();createPlayer();};if(!document.querySelector('script[src="https://www.youtube.com/iframe_api"]')){const api=document.createElement('script');api.src='https://www.youtube.com/iframe_api';api.async=true;document.head.appendChild(api);}}
 mute.addEventListener('click',()=>{if(!player)return;if(player.isMuted())player.unMute();else player.mute();updateMute();});
 vol.addEventListener('input',()=>{desiredVolume=Number(vol.value);localStorage.setItem('siteLaunchVolume',String(desiredVolume));if(player){player.setVolume(desiredVolume);if(desiredVolume>0&&player.isMuted())player.unMute();updateMute();}});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
