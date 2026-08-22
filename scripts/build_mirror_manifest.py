#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json, time, urllib.request
from urllib.parse import urlparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; DATA=ROOT/'data'/'imported_media.json'; OUT=ROOT/'data'/'mirror_manifest.json'

def candidates(x):
 vals=[x.get('localUrl'),x.get('cachedUrl'),x.get('video'),x.get('audio'),x.get('url'),x.get('sourceUrl')]; vals+=list(x.get('sourceCandidates') or []); vals+=list(x.get('mirrors') or [])
 out=[]
 for v in vals:
  if isinstance(v,dict):v=v.get('url')
  if v and str(v) not in out:out.append(str(v))
 return out

def probe(url):
 if url.startswith('/'):
  p=ROOT/url.lstrip('/'); return {'url':url,'ok':p.exists(),'latencyMs':0,'origin':'local'}
 st=time.perf_counter()
 try:
  req=urllib.request.Request(url,method='HEAD',headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=6) as r:status=getattr(r,'status',200)
  return {'url':url,'ok':200<=status<500,'status':status,'latencyMs':round((time.perf_counter()-st)*1000),'origin':urlparse(url).netloc}
 except Exception as e:return {'url':url,'ok':False,'latencyMs':round((time.perf_counter()-st)*1000),'error':str(e)[:160]}

def main():
 data=json.loads(DATA.read_text(encoding='utf-8')); items=[]; shortage=[]
 for x in data.get('items',[]):
  mid=str(x.get('id') or ''); rows=[probe(u) for u in candidates(x)]; good=[r for r in rows if r.get('ok')]; good.sort(key=lambda r:r.get('latencyMs',999999)); origins={r.get('origin') for r in good if r.get('origin')}
  item={'id':mid,'verifiedMirrors':good,'verifiedCount':len(good),'independentOrigins':len(origins),'meetsFiveMirrorTarget':len(origins)>=5};items.append(item)
  if len(origins)<5:shortage.append({'id':mid,'independentOrigins':len(origins),'needed':5-len(origins)})
 out={'generatedAt':int(time.time()),'targetIndependentMirrors':5,'items':items,'shortage':shortage,'note':'Only responding, already configured origins are counted. This script never invents mirrors.'};OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'items':len(items),'meetingTarget':len(items)-len(shortage),'shortage':len(shortage)},ensure_ascii=False))
if __name__=='__main__':main()
