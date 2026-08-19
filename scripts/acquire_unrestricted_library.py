#!/usr/bin/env python3
"""Strict first-party acquisition engine for unrestricted/public-domain library assets.
Network acquisition is server-side only. Metadata never grants capabilities.
"""
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request,urlopen
import argparse,hashlib,json,mimetypes,re,time,uuid
ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'library'/'works'; STATE=ROOT/'private'/'acquisition_state.json'; CAND=ROOT/'private'/'acquisition_candidates.json'
ALLOW={'archive.org','www.archive.org','gutenberg.org','www.gutenberg.org','upload.wikimedia.org','commons.wikimedia.org','wikisource.org','en.wikisource.org','fr.wikisource.org','ar.wikisource.org'}
ACCEPT={'public domain','public domain mark','cc0','unrestricted'}

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def safe_url(u):
 x=urlparse(u); return x.scheme=='https' and x.hostname in ALLOW
def rights_ok(r): return any(x in str(r or '').lower() for x in ACCEPT)
def get(u,timeout=90):
 if not safe_url(u): raise RuntimeError('domain-not-allowlisted')
 with urlopen(Request(u,headers={'User-Agent':'ProphetBiographyLibrary/6.6'}),timeout=timeout) as r:
  b=r.read(); ct=(r.headers.get('content-type') or '').split(';')[0].lower(); return b,ct
def validate_bytes(b,kind):
 if len(b)<1024: return False,'too-small'
 if kind=='pdf' and not b.startswith(b'%PDF'): return False,'not-pdf'
 if kind=='epub' and not b.startswith(b'PK'): return False,'not-epub'
 if b[:100].lower().lstrip().startswith(b'<!doctype html') and kind in {'pdf','epub'}: return False,'html-error-page'
 return True,'ok'
def slug(s): return re.sub(r'[^a-z0-9\u0600-\u06ff]+','-',str(s).lower()).strip('-')[:90] or uuid.uuid4().hex[:12]
def save_state(d): STATE.parent.mkdir(parents=True,exist_ok=True); STATE.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--limit',type=int,default=25); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args()
 c=json.loads(CAND.read_text(encoding='utf8')) if CAND.exists() else {'items':[]}; state={'schema':'strict-acquisition-v1','updatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'items':[]}
 acquired=0
 for x in c.get('items',[]):
  row=dict(x); row['status']='UNLICENCED_CHECK'
  if not rights_ok(x.get('rightsEvidence')): row['status']='REJECTED'; row['error']='rights-not-unrestricted'; state['items'].append(row); continue
  row['status']='UNLICENCED_CONFIRMED'
  if not safe_url(x.get('downloadUrl','')): row['status']='REJECTED'; row['error']='download-domain-not-allowlisted'; state['items'].append(row); continue
  if a.dry_run: row['status']='DISCOVERED'; state['items'].append(row); continue
  try: b,ct=get(x['downloadUrl'])
  except Exception as e: row['status']='FAILED'; row['error']='download:'+type(e).__name__; state['items'].append(row); continue
  kind=x.get('format','txt').lower(); ok,why=validate_bytes(b,kind)
  if not ok: row['status']='FAILED'; row['error']=why; state['items'].append(row); continue
  wid=x.get('workId') or slug(x.get('titleOriginal')); eid=x.get('editionId') or 'ed-'+hashlib.sha256(b).hexdigest()[:12]
  ed=STORE/wid/'editions'/eid; ed.mkdir(parents=True,exist_ok=True); ext={'pdf':'pdf','epub':'epub','txt':'txt','html':'html'}.get(kind,kind); orig=ed/f'original.{ext}'; orig.write_bytes(b)
  digest=sha(orig); meta={k:x.get(k) for k in ['titleOriginal','titleAr','titleEn','titleFr','author','language','subjects','siteSections','sourceRepository','sourceIdentifier','sourceUrl']}; meta.update({'workId':wid,'editionId':eid,'format':kind,'mimeType':ct or mimetypes.guess_type(orig.name)[0],'size':len(b),'sha256':digest,'status':'DOWNLOADED','readable':True if kind in {'txt','html','pdf','epub'} else False,'searchable':True if kind in {'txt','html'} else False,'listenable':True if kind in {'txt','html'} else False,'watchable':False})
  (ed/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  (ed/'rights.json').write_text(json.dumps({'status':'UNLICENCED_CONFIRMED','evidence':x.get('rightsEvidence'),'evidenceUrl':x.get('rightsEvidenceUrl'),'checkedAt':state['updatedAt']},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  (ed/'provenance.json').write_text(json.dumps({'sourceRepository':x.get('sourceRepository'),'sourceIdentifier':x.get('sourceIdentifier'),'sourceUrl':x.get('sourceUrl'),'downloadUrl':x.get('downloadUrl'),'retrievalDate':state['updatedAt'],'originalFilename':orig.name,'sha256':digest,'size':len(b),'mimeType':meta['mimeType']},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  row.update({'status':'DOWNLOADED','localPath':str(orig.relative_to(ROOT)).replace('\\','/'),'sha256':digest}); state['items'].append(row); acquired+=1
  if acquired>=a.limit: break
 save_state(state); print(json.dumps({'acquired':acquired,'state':str(STATE.relative_to(ROOT))},ensure_ascii=False))
if __name__=='__main__': main()
