#!/usr/bin/env python3
"""Comprehensive metadata-only media repertory synchronizer.

Indexes official configured channels, playlists, public web archives, and carefully-scoped YouTube
searches. It NEVER downloads audio/video. Public entries keep direct source URLs and privacy-enhanced
YouTube embeds. Transcripts used for editorial grounding are handled separately by scholar_material_sync.py.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urljoin,urlparse
from html.parser import HTMLParser
import json,hashlib,datetime,os,re,threading,time
ROOT=Path(__file__).resolve().parent
CONFIG=ROOT/'private'/'media_sources.json'; EXTRA_CONFIG=ROOT/'private'/'media_sources_extra.json'; OUT=ROOT/'data'/'imported_media.json'; STATE=ROOT/'private'/'media_sync_state.json'
UA='Mozilla/5.0 (compatible; PropheticBiographyMediaIndexer/3.0)';LOCK=threading.Lock();STOP=threading.Event()

def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load_config():
 base=load(CONFIG,{'sources':[],'taxonomy':[]});extra=load(EXTRA_CONFIG,{'sources':[],'taxonomy':[]})
 merged=dict(base);tax=[*(base.get('taxonomy') or [])];seen_tax={str(x.get('key')) for x in tax if isinstance(x,dict)}
 for x in extra.get('taxonomy') or []:
  if isinstance(x,dict) and str(x.get('key')) not in seen_tax:tax.append(x);seen_tax.add(str(x.get('key')))
 by={}
 for src in [*(base.get('sources') or []),*(extra.get('sources') or [])]:
  if isinstance(src,dict) and src.get('id'):by[str(src['id'])]=src
 merged['taxonomy']=tax;merged['sources']=list(by.values());return merged
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
def yt_embed(vid):return f'https://www.youtube-nocookie.com/embed/{vid}' if vid else ''
def ytid(url):
 m=re.search(r'(?:v=|youtu\.be/|embed/)([A-Za-z0-9_-]{11})',url or '');return m.group(1) if m else ''

def category(src,e=None):
 return str(src.get('category') or (src.get('topics') or ['lecture'])[0] or 'lecture')

def normalize_entry(e,src):
 vid=str(e.get('id') or e.get('video_id') or '')
 if len(vid)!=11:vid=ytid(str(e.get('url') or e.get('webpage_url') or ''))
 if not vid:return None
 title=str(e.get('title') or 'Video')[:500];thumb=str(e.get('thumbnail') or '') or f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
 creator=str(e.get('channel') or e.get('uploader') or src.get('label') or '')[:240]
 cats=[category(src,e),*(src.get('topics') or [])];cats=list(dict.fromkeys([x for x in cats if x]))
 return {'id':'yt-'+vid,'kind':'video','category':category(src,e),'titleEn':title,'titleAr':title,'titleFr':title,
 'summaryEn':'','summaryAr':'','summaryFr':'',
 'url':f'https://www.youtube.com/watch?v={vid}','embed':yt_embed(vid),'language':src.get('language','ar'),'topics':cats,
 'transcriptStatus':'external','duration':str(e.get('duration_string') or e.get('duration') or 'video'),'chapters':[],
 'thumbnail':thumb,'published':e.get('upload_date') or e.get('release_date') or '', 'creator':creator,
 'series':str(src.get('series') or src.get('label') or '')[:240],'venue':str(src.get('venue') or '')[:240],
 'sourceType':src.get('kind',''),'catalogSourceId':src.get('id',''),'catalogTier':'official' if src.get('kind') in {'youtube','youtube-single','web-media'} else 'repertory-search','viewCount':int(e.get('view_count') or 0) if str(e.get('view_count') or '').isdigit() else 0}

def _ydl_extract(target,src,max_entries=0,flat=True):
 try:import yt_dlp
 except Exception as exc:return [],'yt-dlp not installed: '+str(exc)
 opts={'quiet':True,'skip_download':True,'extract_flat':'in_playlist' if flat else False,'ignoreerrors':True,'playlistend':max_entries or None,'socket_timeout':30,'noplaylist':False}
 rows=[]
 try:
  with yt_dlp.YoutubeDL(opts) as ydl:info=ydl.extract_info(target,download=False)
  entries=(info or {}).get('entries') or [info]
  for e in entries:
   if not e:continue
   n=normalize_entry(e,src)
   if n:rows.append(n)
  return rows,''
 except Exception as exc:return rows,str(exc)[:400]

def sync_youtube(src,max_entries=0):return _ydl_extract(src['url'],src,max_entries,True)
def sync_search(src,max_entries=0):
 n=max_entries or int(src.get('maxResults') or 80);q=str(src.get('query') or '').strip()
 return _ydl_extract(f'ytsearch{n}:{q}',src,n,False) if q else ([], 'search query missing')

class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[]
 def handle_starttag(self,t,a):
  d=dict(a)
  for k in ('href','src'):
   if d.get(k):self.links.append(d[k])
def fetch(url):
 r=Request(url,headers={'User-Agent':UA,'Accept-Language':'ar,en;q=.8'})
 with urlopen(r,timeout=30) as f:return f.read(4_000_000).decode(f.headers.get_content_charset() or 'utf-8','replace')

def sync_web(src):
 base=src['url'];host=urlparse(base).netloc;todo=[base];seen=set();rows=[];cap=max(50,int(src.get('crawlPageCap') or 500))
 while todo and len(seen)<cap:
  u=todo.pop(0)
  if u in seen:continue
  seen.add(u)
  try:html=fetch(u)
  except Exception:continue
  p=Links();p.feed(html)
  for raw in p.links:
   v=urljoin(u,raw);pv=urlparse(v)
   if pv.netloc and pv.netloc!=host and 'youtube.com' not in pv.netloc and 'youtu.be' not in pv.netloc:continue
   if v.lower().split('?')[0].endswith(('.mp3','.m4a','.ogg','.wav')):
    mid='audio-'+hashlib.sha256(v.encode()).hexdigest()[:16];title=v.rsplit('/',1)[-1].rsplit('.',1)[0].replace('-',' ').replace('_',' ')[:240]
    rows.append({'id':mid,'kind':'audio','category':category(src),'titleEn':title,'titleAr':title,'titleFr':title,'summaryEn':'','summaryAr':'','summaryFr':'','url':v,'audio':v,'embed':'','language':src.get('language','ar'),'topics':list(dict.fromkeys([category(src),*(src.get('topics') or [])])),'transcriptStatus':'external','duration':'audio','chapters':[],'thumbnail':'','published':'','creator':src.get('label',''),'series':src.get('series',src.get('label','')),'venue':'','sourceType':'web-media','catalogSourceId':src.get('id',''),'catalogTier':'official','viewCount':0})
   elif 'youtube.com/watch' in v or 'youtu.be/' in v:
    n=normalize_entry({'url':v,'title':'Video'},src)
    if n:rows.append(n)
   elif pv.netloc==host and v not in seen and len(todo)<cap and not re.search(r'\.(jpg|png|gif|pdf|zip)(?:\?|$)',v,re.I):todo.append(v.split('#')[0])
 return rows,''

def sync_all(max_entries=0):
 with LOCK:
  cfg=load_config();prev=load(OUT,{'items':[]});by={x['id']:x for x in prev.get('items',[]) if x.get('id')}
  rep={'ok':True,'started':now(),'sources':0,'addedOrUpdated':0,'total':0,'categories':{},'errors':[]}
  for src in cfg.get('sources',[]):
   if src.get('enabled',True) is False:continue
   rep['sources']+=1;kind=src.get('kind')
   if kind=='web-media':rows,err=sync_web(src)
   elif kind in {'youtube','youtube-single'}:rows,err=sync_youtube(src,max_entries or int(src.get('maxResults') or 0))
   elif kind=='youtube-search':rows,err=sync_search(src,max_entries)
   else:rows,err=[],'unsupported source kind'
   if err:rep['errors'].append({'source':src.get('id'),'error':err})
   for x in rows:by[x['id']]=x;rep['addedOrUpdated']+=1
  items=list(by.values());items.sort(key=lambda x:(str(x.get('category','')),1 if x.get('catalogTier')=='official' else 0,str(x.get('published','')),int(x.get('viewCount') or 0),str(x.get('titleEn',''))),reverse=True)
  for x in items:rep['categories'][x.get('category','other')]=rep['categories'].get(x.get('category','other'),0)+1
  out={'version':'6.0.0','generated':now(),'taxonomy':cfg.get('taxonomy',[]),'items':items};dump(OUT,out);rep['total']=len(items);rep['finished']=now();dump(STATE,rep);return rep

def status():
 x=load(STATE,{});x.setdefault('ok',True);x.setdefault('total',len(load(OUT,{'items':[]}).get('items',[])));return x

def worker():
 interval=max(3600,int(os.getenv('PM_MEDIA_SYNC_INTERVAL_SECONDS','21600')))
 while not STOP.is_set():
  try:sync_all(int(os.getenv('PM_MEDIA_MAX_PER_SOURCE','0')))
  except Exception:pass
  STOP.wait(interval)
def start_worker():
 if os.getenv('PM_AUTO_MEDIA_SYNC','1')!='1':return None
 t=threading.Thread(target=worker,daemon=True,name='pm-media-sync');t.start();return t
if __name__=='__main__':print(json.dumps(sync_all(),ensure_ascii=False,indent=2))
