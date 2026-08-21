#!/usr/bin/env python3
from __future__ import annotations
import json, mimetypes, os, re, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'replication_manifest.json'

def safe(s):return re.sub(r'[^A-Za-z0-9_.-]+','_',str(s))[:180]
def origins():
 out=[]
 for i in range(1,6):
  raw=os.getenv(f'PM_MIRROR_{i}_JSON','').strip()
  if not raw:continue
  try:
   x=json.loads(raw);x['slot']=i
   if all(x.get(k) for k in ('bucket','public_base')):out.append(x)
  except Exception as e:print(f'PM_MIRROR_{i}_JSON invalid:',e)
 return out

def local_assets():
 seen={}
 # media cache
 for p in (ROOT/'media-cache').glob('*') if (ROOT/'media-cache').exists() else []:
  if p.is_file() and not p.name.endswith(('.part','.ytdl')):seen['media/'+p.name]=p
 # locally published books/epubs
 for index in (ROOT/'data'/'published_user_books.json',ROOT/'data'/'generated_epubs.json'):
  if not index.exists():continue
  try:j=json.loads(index.read_text(encoding='utf-8'))
  except:continue
  for x in j.get('items',[]):
   for k in ('localUrl','readerUrl','publicUrl','downloadUrl'):
    v=x.get(k)
    if isinstance(v,str) and (v.startswith('/') or not v.startswith('http')):
     p=ROOT/v.lstrip('/')
     if p.is_file():seen['books/'+p.name]=p
 return seen

def client(cfg):
 import boto3
 kw={'service_name':'s3','region_name':cfg.get('region') or 'auto','aws_access_key_id':cfg.get('access_key') or os.getenv(cfg.get('access_key_env','')),'aws_secret_access_key':cfg.get('secret_key') or os.getenv(cfg.get('secret_key_env',''))}
 if cfg.get('endpoint_url'):kw['endpoint_url']=cfg['endpoint_url']
 return boto3.client(**kw)

def main():
 ospec=origins();assets=local_assets();report={'generatedAt':int(time.time()),'configuredOrigins':len(ospec),'assets':{},'shortage':[],'note':'URLs are recorded only after successful upload. No synthetic mirrors are emitted.'}
 if not ospec:print('No PM_MIRROR_1_JSON..PM_MIRROR_5_JSON configured; manifest will record shortage only.')
 for key,p in assets.items():
  copies=[]
  for cfg in ospec:
   try:
    c=client(cfg);obj=(cfg.get('prefix','').strip('/')+'/'+key).lstrip('/');ctype=mimetypes.guess_type(p.name)[0] or 'application/octet-stream';extra={'ContentType':ctype,'CacheControl':'public,max-age=31536000,immutable'};c.upload_file(str(p),cfg['bucket'],obj,ExtraArgs=extra);url=cfg['public_base'].rstrip('/')+'/'+obj;copies.append({'slot':cfg['slot'],'url':url,'bucket':cfg['bucket'],'object':obj})
   except Exception as e:copies.append({'slot':cfg.get('slot'),'ok':False,'error':str(e)[:300]})
  good=[x for x in copies if x.get('url')];report['assets'][key]={'bytes':p.stat().st_size,'mirrors':good,'failures':[x for x in copies if not x.get('url')],'meetsFiveMirrorTarget':len(good)>=5}
  if len(good)<5:report['shortage'].append({'asset':key,'verifiedCopies':len(good),'needed':5-len(good)})
 OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'assets':len(assets),'configuredOrigins':len(ospec),'meetingFive':len(assets)-len(report['shortage']),'shortage':len(report['shortage'])},ensure_ascii=False))
if __name__=='__main__':main()
