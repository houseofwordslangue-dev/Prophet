#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, mimetypes, os, re, subprocess, sys, threading, time
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'/'imported_media.json'; EPUB_INDEX=ROOT/'data'/'generated_epubs.json'; CACHE=ROOT/'media-cache'; TELEMETRY=ROOT/'data'/'runtime_telemetry.ndjson'
CACHE.mkdir(parents=True,exist_ok=True)
HOST=os.getenv('PM_HOST','127.0.0.1'); PORT=int(os.getenv('PM_PORT','8080')); SYNC_ON_START=os.getenv('PM_MEDIA_SYNC_ON_START','1')=='1'; EPUB_ON_START=os.getenv('PM_EPUB_CONVERT_ON_START','1')=='1'; MAX_SYNC=int(os.getenv('PM_MEDIA_MAX_PER_SOURCE','350')); CACHE_ENABLED=os.getenv('PM_MEDIA_CACHE','1')=='1'; CACHE_MAX_HEIGHT=int(os.getenv('PM_MEDIA_CACHE_MAX_HEIGHT','2160'))
_MEDIA_LOCK=threading.Lock(); _MEDIA_BY_ID={}; _CACHE_JOBS=set()

def _load_catalogue():
 global _MEDIA_BY_ID
 try:items=json.loads(DATA.read_text(encoding='utf-8')).get('items',[])
 except Exception:items=[]
 with _MEDIA_LOCK:_MEDIA_BY_ID={str(x.get('id')):x for x in items if x.get('id')}

def _sync_catalogue():
 if not SYNC_ON_START:return _load_catalogue()
 try:
  from scripts.sync_media import run_expanded_sync; run_expanded_sync(MAX_SYNC)
 except Exception as exc:print('media sync warning:',exc)
 _load_catalogue()

def _publish_epubs():
 if not EPUB_ON_START:return
 script=ROOT/'scripts'/'convert_all_epub.py'
 if not script.exists():return
 try:
  cp=subprocess.run([sys.executable,str(script)],cwd=str(ROOT),text=True,capture_output=True,timeout=3600)
  if cp.stdout:print(cp.stdout[-20000:])
  if cp.returncode and cp.stderr:print('EPUB publication warning:',cp.stderr[-12000:])
 except Exception as exc:print('EPUB publication warning:',exc)

def _epub_status():
 try:
  d=json.loads(EPUB_INDEX.read_text(encoding='utf-8')); return {'ok':True,'count':int(d.get('count') or 0),'processedThisRun':int(d.get('processedThisRun') or 0),'failedThisRun':d.get('failedThisRun') or [],'generatedAt':d.get('generatedAt')}
 except Exception as exc:return {'ok':False,'count':0,'error':str(exc)}

def _safe_id(v):return re.sub(r'[^A-Za-z0-9_.-]+','_',str(v))[:180]
def _cached_file(item_id):
 stem=_safe_id(item_id)
 for p in CACHE.glob(stem+'.*'):
  if p.is_file() and not p.name.endswith(('.part','.ytdl')):return p
 return None

def _medium(item):
 m=str(item.get('medium') or '').strip().lower()
 if m:return m
 if item.get('kind')=='audio':return'audio'
 c=str(item.get('category') or '').lower(); return c if c in {'podcast','research','documentary','audio','video','lecture'} else ('lecture' if c else 'video')

def _yt_info(item):
 import yt_dlp
 url=str(item.get('url') or item.get('embed') or '')
 if not url:raise RuntimeError('media source URL missing')
 fmt='bestaudio/best' if _medium(item) in {'audio','podcast'} else 'best[ext=mp4][protocol^=http]/best[protocol^=http]/best'
 with yt_dlp.YoutubeDL({'quiet':True,'skip_download':True,'noplaylist':True,'format':fmt,'socket_timeout':30}) as ydl:info=ydl.extract_info(url,download=False)
 if not info:raise RuntimeError('media metadata unavailable')
 return info

def _remote_url(item):
 direct=str(item.get('audio') or item.get('video') or '')
 if direct and not any(h in direct for h in ('youtube.com','youtu.be','youtube-nocookie.com')):return direct,''
 info=_yt_info(item); url=str(info.get('url') or '')
 if not url:raise RuntimeError('stream URL unavailable')
 return url,str(info.get('http_headers',{}).get('User-Agent') or '')

def _cache_item(item):
 if not CACHE_ENABLED:return
 item_id=str(item.get('id') or '')
 if not item_id or _cached_file(item_id):return
 with _MEDIA_LOCK:
  if item_id in _CACHE_JOBS:return
  _CACHE_JOBS.add(item_id)
 try:
  import yt_dlp
  audio=_medium(item) in {'audio','podcast'}; stem=str(CACHE/_safe_id(item_id))
  video_fmt=f'bestvideo[height<={CACHE_MAX_HEIGHT}]+bestaudio/best[height<={CACHE_MAX_HEIGHT}]/best'
  opts={'quiet':True,'noplaylist':True,'outtmpl':stem+'.%(ext)s','socket_timeout':30,'retries':3,'fragment_retries':3,'format':'bestaudio/best' if audio else video_fmt,'merge_output_format':None if audio else 'mp4'}
  with yt_dlp.YoutubeDL(opts) as ydl:ydl.download([str(item.get('url') or item.get('embed') or '')])
 except Exception as exc:print('cache warning',item_id,exc)
 finally:
  with _MEDIA_LOCK:_CACHE_JOBS.discard(item_id)

def _start_cache(item):threading.Thread(target=_cache_item,args=(item,),daemon=True,name='media-cache').start()
def _mirror_candidates(item):
 vals=[item.get('localUrl'),item.get('cachedUrl'),item.get('video'),item.get('audio'),item.get('url'),item.get('sourceUrl')]; vals.extend(item.get('sourceCandidates') or []); vals.extend(item.get('mirrors') or [])
 out=[]
 for v in vals:
  if isinstance(v,dict):v=v.get('url')
  if v and str(v) not in out:out.append(str(v))
 return out

def _probe(url):
 if url.startswith('/'):
  p=ROOT/url.lstrip('/'); return {'url':url,'ok':p.exists(),'latencyMs':0,'local':True}
 started=time.perf_counter()
 try:
  req=Request(url,method='HEAD',headers={'User-Agent':'Mozilla/5.0'})
  with urlopen(req,timeout=4) as r:ok=200<=getattr(r,'status',200)<500
  return {'url':url,'ok':ok,'latencyMs':round((time.perf_counter()-started)*1000)}
 except Exception as exc:return {'url':url,'ok':False,'latencyMs':round((time.perf_counter()-started)*1000),'error':str(exc)[:180]}

def _sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
 return h.hexdigest()

class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def end_headers(self):self.send_header('Cache-Control','no-store' if self.path.startswith('/api/') else 'public, max-age=300'); super().end_headers()
 def do_GET(self):
  parsed=urlparse(self.path)
  if parsed.path=='/api/ready':return self._json({'ok':True,'mediaItems':len(_MEDIA_BY_ID),'epubs':_epub_status().get('count',0),'cacheMaxHeight':CACHE_MAX_HEIGHT})
  if parsed.path=='/api/epub/status':return self._json(_epub_status())
  if parsed.path=='/api/media/status':
   counts={k:0 for k in ('video','lecture','podcast','research','documentary','audio')}
   with _MEDIA_LOCK:items=list(_MEDIA_BY_ID.values())
   for item in items:
    m=_medium(item)
    if m in counts:counts[m]+=1
   return self._json({'ok':True,'total':len(items),'categories':counts})
  if parsed.path=='/api/media/mirrors':
   item_id=(parse_qs(parsed.query).get('id') or [''])[0]
   with _MEDIA_LOCK:item=_MEDIA_BY_ID.get(item_id)
   if not item:return self._json({'ok':False,'error':'unknown media id'},404)
   rows=[_probe(u) for u in _mirror_candidates(item)[:12]]; rows.sort(key=lambda x:(not x.get('ok'),x.get('latencyMs',999999))); return self._json({'ok':True,'mirrors':rows})
  if parsed.path=='/api/media/integrity':
   item_id=(parse_qs(parsed.query).get('id') or [''])[0]; cached=_cached_file(item_id)
   if not cached:return self._json({'ok':False,'error':'cached asset unavailable'},404)
   return self._json({'ok':True,'id':item_id,'file':cached.name,'sha256':_sha256(cached),'bytes':cached.stat().st_size})
  if parsed.path=='/api/media/stream':return self._media_stream((parse_qs(parsed.query).get('id') or [''])[0])
  return super().do_GET()
 def do_POST(self):
  parsed=urlparse(self.path)
  if parsed.path=='/api/telemetry':
   try:
    n=min(int(self.headers.get('Content-Length') or 0),65536); data=json.loads(self.rfile.read(n).decode('utf-8','replace') or '{}'); data['serverTs']=int(time.time()*1000); TELEMETRY.parent.mkdir(parents=True,exist_ok=True)
    with TELEMETRY.open('a',encoding='utf-8') as f:f.write(json.dumps(data,ensure_ascii=False)+'\n')
    return self._json({'ok':True})
   except Exception as exc:return self._json({'ok':False,'error':str(exc)},400)
  return self._json({'ok':False,'error':'unknown endpoint'},404)
 def _json(self,data,status=200):
  payload=json.dumps(data,ensure_ascii=False).encode('utf-8'); self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
 def _media_stream(self,item_id):
  with _MEDIA_LOCK:item=_MEDIA_BY_ID.get(item_id)
  if not item:return self._json({'ok':False,'error':'unknown media id'},404)
  cached=_cached_file(item_id)
  if cached:return self._serve_local_file(cached)
  _start_cache(item)
  try:
   remote,ua=_remote_url(item); headers={'User-Agent':ua or 'Mozilla/5.0'}
   if self.headers.get('Range'):headers['Range']=self.headers['Range']
   upstream=urlopen(Request(remote,headers=headers),timeout=45); self.send_response(getattr(upstream,'status',200))
   for h in ('Content-Type','Content-Length','Content-Range','Accept-Ranges','ETag','Last-Modified'):
    v=upstream.headers.get(h)
    if v:self.send_header(h,v)
   self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
   while True:
    chunk=upstream.read(256*1024)
    if not chunk:break
    self.wfile.write(chunk)
  except BrokenPipeError:return
  except Exception as exc:return self._json({'ok':False,'error':str(exc)},502)
 def _serve_local_file(self,path):
  total=path.stat().st_size; ctype=mimetypes.guess_type(path.name)[0] or 'application/octet-stream'; start,end=0,total-1; rh=self.headers.get('Range')
  if rh:
   m=re.match(r'bytes=(\d*)-(\d*)',rh)
   if m:
    if m.group(1):start=int(m.group(1))
    if m.group(2):end=min(int(m.group(2)),total-1)
    self.send_response(HTTPStatus.PARTIAL_CONTENT); self.send_header('Content-Range',f'bytes {start}-{end}/{total}')
   else:self.send_response(HTTPStatus.OK)
  else:self.send_response(HTTPStatus.OK)
  length=max(0,end-start+1); self.send_header('Content-Type',ctype); self.send_header('Content-Length',str(length)); self.send_header('Accept-Ranges','bytes'); self.send_header('Access-Control-Allow-Origin','*'); self.end_headers()
  with path.open('rb') as f:
   f.seek(start); remain=length
   while remain>0:
    chunk=f.read(min(256*1024,remain))
    if not chunk:break
    self.wfile.write(chunk); remain-=len(chunk)

try:
 from platform_services import install as _install_platform_services
 _install_platform_services(Handler,ROOT)
except Exception as exc:print('platform services warning:',exc)
try:
 from ops_services import install as _install_ops_services
 _install_ops_services(Handler)
except Exception as exc:print('ops services warning:',exc)
try:
 from chat_services import install as _install_children_chat_services
 _install_children_chat_services(Handler)
except Exception as exc:print('children chat services warning:',exc)
try:
 from site_chat_services import install as _install_site_chat_services
 _install_site_chat_services(Handler)
except Exception as exc:print('site chat services warning:',exc)

def main():
 _sync_catalogue()
 try:
  from platform_services import build_search_index
  build_search_index(True)
 except Exception as exc:print('search rebuild warning:',exc)
 if EPUB_ON_START:threading.Thread(target=_publish_epubs,daemon=True,name='epub-publisher').start()
 print(f'Prophet site: http://{HOST}:{PORT}/'); print(f'Media player: http://{HOST}:{PORT}/media.html'); print('Platform search/sync/telemetry: enabled'); print('Main and children source-grounded assistants: enabled'); print('Admin operations center: /ops.html')
 ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

if __name__=='__main__':main()
