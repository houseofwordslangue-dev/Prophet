(function(){
'use strict';
if(window.__siteLaunchAudioMounted)return;
window.__siteLaunchAudioMounted=true;
const AUDIO_SRC='assets/audio/start-recording-salawat.mp3';
const SOURCE_URL='https://www.youtube.com/watch?v=M64ELezZihw&t=294s';
const lang=(document.documentElement.lang||'ar').toLowerCase().slice(0,2);
const T={
 ar:{title:'الصلاة والسلام على رسول الله',play:'تشغيل',pause:'إيقاف',mute:'كتم الصوت',unmute:'تشغيل الصوت',volume:'مستوى الصوت',source:'التسجيل الكامل في الوسائط',blocked:'اضغط تشغيل لبدء التسجيل'},
 en:{title:'Peace and blessings upon the Messenger',play:'Play',pause:'Pause',mute:'Mute',unmute:'Unmute',volume:'Volume',source:'Full recording in Media',blocked:'Press play to start the recording'},
 fr:{title:'Paix et bénédictions sur le Messager',play:'Lecture',pause:'Pause',mute:'Couper le son',unmute:'Activer le son',volume:'Volume',source:'Enregistrement complet dans Médias',blocked:'Appuyez sur Lecture pour démarrer'}
};
const tr=T[lang]||T.ar;
function mount(){
 if(document.getElementById('siteLaunchAudio'))return;
 const wrap=document.createElement('section');wrap.id='siteLaunchAudio';wrap.setAttribute('aria-label',tr.title);
 wrap.innerHTML=`<div class="sla-head"><strong>${tr.title}</strong><button type="button" class="sla-collapse" aria-label="${tr.title}">−</button></div><div class="sla-body"><audio class="sla-audio" preload="auto" src="${AUDIO_SRC}"></audio><div class="sla-controls"><button type="button" class="sla-play">▶ <span>${tr.play}</span></button><button type="button" class="sla-mute" aria-pressed="false">🔊 <span>${tr.mute}</span></button><label><span>${tr.volume}</span><input class="sla-volume" type="range" min="0" max="100" step="1" value="35"></label></div><small class="sla-status" aria-live="polite">${tr.blocked}</small><a class="sla-source" href="media.html?v=yt-M64ELezZihw">${tr.source}</a></div>`;
 const style=document.createElement('style');
 style.textContent=`#siteLaunchAudio{position:fixed;z-index:2147483000;right:14px;bottom:14px;width:min(270px,calc(100vw - 28px));background:rgba(7,29,24,.96);color:#f7fbf8;border:1px solid rgba(219,193,138,.42);border-radius:16px;box-shadow:0 18px 55px rgba(0,0,0,.38);backdrop-filter:blur(16px);font-family:inherit;overflow:hidden}#siteLaunchAudio .sla-head{display:flex;align-items:center;justify-content:space-between;padding:9px 11px;background:rgba(255,255,255,.05)}#siteLaunchAudio .sla-head strong{font-size:12px}#siteLaunchAudio button{font:inherit;color:inherit;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.12);border-radius:10px;cursor:pointer}#siteLaunchAudio .sla-collapse{width:30px;height:30px}#siteLaunchAudio .sla-body{padding:10px}#siteLaunchAudio.collapsed .sla-body{display:none}#siteLaunchAudio .sla-controls{display:grid;grid-template-columns:1fr 1fr;gap:8px}#siteLaunchAudio .sla-play,#siteLaunchAudio .sla-mute{padding:9px 10px;display:flex;align-items:center;justify-content:center;gap:6px}#siteLaunchAudio label{grid-column:1/-1;display:grid;grid-template-columns:auto 1fr;align-items:center;gap:8px;font-size:11px}#siteLaunchAudio input[type=range]{width:100%;accent-color:#dbc18a}#siteLaunchAudio .sla-status{display:block;min-height:15px;margin-top:6px;color:#d7e8df;font-size:10px}#siteLaunchAudio .sla-source{display:block;margin-top:4px;color:#dbc18a;font-size:10px;text-decoration:none}@media(max-width:560px){#siteLaunchAudio{right:8px;bottom:8px;width:230px}}`;
 document.head.appendChild(style);document.body.appendChild(wrap);
 const audio=wrap.querySelector('.sla-audio'),play=wrap.querySelector('.sla-play'),mute=wrap.querySelector('.sla-mute'),vol=wrap.querySelector('.sla-volume'),status=wrap.querySelector('.sla-status');
 let desiredVolume=Number(localStorage.getItem('siteLaunchVolume')||35);if(!Number.isFinite(desiredVolume))desiredVolume=35;desiredVolume=Math.max(0,Math.min(100,desiredVolume));vol.value=String(desiredVolume);audio.volume=desiredVolume/100;
 const sync=()=>{play.innerHTML=audio.paused?`▶ <span>${tr.play}</span>`:`Ⅱ <span>${tr.pause}</span>`;mute.setAttribute('aria-pressed',String(audio.muted));mute.innerHTML=audio.muted?`🔇 <span>${tr.unmute}</span>`:`🔊 <span>${tr.mute}</span>`;if(!audio.paused)status.textContent='';};
 play.addEventListener('click',()=>{if(audio.paused){audio.currentTime=0;audio.play().catch(()=>{status.textContent=tr.blocked})}else audio.pause();sync()});
 mute.addEventListener('click',()=>{audio.muted=!audio.muted;sync()});
 vol.addEventListener('input',()=>{desiredVolume=Number(vol.value);localStorage.setItem('siteLaunchVolume',String(desiredVolume));audio.volume=desiredVolume/100;if(desiredVolume>0)audio.muted=false;sync()});
 audio.addEventListener('play',sync);audio.addEventListener('pause',sync);audio.addEventListener('ended',sync);
 const collapse=wrap.querySelector('.sla-collapse');collapse.addEventListener('click',()=>{wrap.classList.toggle('collapsed');collapse.textContent=wrap.classList.contains('collapsed')?'+':'−'});
 sync();
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',mount,{once:true});else mount();
})();
