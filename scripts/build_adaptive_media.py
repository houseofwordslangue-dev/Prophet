#!/usr/bin/env python3
from __future__ import annotations
import json, shutil, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data'/'imported_media.json'
CACHE=ROOT/'media-cache'
OUT=ROOT/'media-adaptive'
OUT.mkdir(exist_ok=True)
PROFILES=[('360p',640,360,'700k','96k'),('480p',854,480,'1200k','128k'),('720p',1280,720,'2500k','128k'),('1080p',1920,1080,'5000k','160k')]
def safe(s:str)->str:
 import re
 return re.sub(r'[^A-Za-z0-9_.-]+','_',s)[:160]
def find_source(mid:str):
 stem=safe(mid)
 for p in CACHE.glob(stem+'.*'):
  if p.is_file() and p.suffix.lower() in {'.mp4','.mkv','.webm','.mov','.m4v'}: return p
 return None
def ffprobe_height(src:Path)->int:
 try:
  cp=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=height','-of','csv=p=0',str(src)],capture_output=True,text=True,check=True)
  return int(cp.stdout.strip() or 0)
 except Exception:return 0
def build(mid:str,src:Path):
 if not shutil.which('ffmpeg'): raise RuntimeError('ffmpeg not installed')
 h=ffprobe_height(src); d=OUT/safe(mid); d.mkdir(parents=True,exist_ok=True); variants=[]
 for label,w,hh,vb,ab in PROFILES:
  if h and hh>h: continue
  dest=d/label; dest.mkdir(exist_ok=True); playlist=dest/'index.m3u8'
  if not playlist.exists():
   subprocess.run(['ffmpeg','-y','-i',str(src),'-vf',f'scale=w={w}:h={hh}:force_original_aspect_ratio=decrease,pad={w}:{hh}:(ow-iw)/2:(oh-ih)/2','-c:v','libx264','-preset','veryfast','-b:v',vb,'-maxrate',vb,'-bufsize',str(int(vb[:-1])*2)+'k','-c:a','aac','-b:a',ab,'-hls_time','6','-hls_playlist_type','vod','-hls_segment_filename',str(dest/'seg-%05d.ts'),str(playlist)],check=True)
  variants.append({'label':label,'height':hh,'url':f'/media-adaptive/{safe(mid)}/{label}/index.m3u8','contentType':'video/mp4; codecs="avc1.64001f, mp4a.40.2"'})
 master=d/'variants.json'; master.write_text(json.dumps({'id':mid,'variants':variants},ensure_ascii=False,indent=2),encoding='utf-8'); return variants
def main():
 data=json.loads(CAT.read_text(encoding='utf-8')); report={'processed':0,'generated':0,'missing':[],'failed':[]}
 for item in data.get('items',[]):
  mid=str(item.get('id') or '');
  if not mid: continue
  report['processed']+=1; src=find_source(mid)
  if not src: report['missing'].append(mid); continue
  try: build(mid,src); report['generated']+=1
  except Exception as e: report['failed'].append({'id':mid,'error':str(e)})
 (OUT/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__': main()
