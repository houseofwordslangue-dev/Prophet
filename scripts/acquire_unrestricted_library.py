#!/usr/bin/env python3
"""Strict first-party acquisition engine for unrestricted/public-domain library assets.
Network acquisition is server-side only. Metadata never grants capabilities.
"""
from pathlib import Path
from urllib.parse import urlparse,urljoin,quote_plus
from urllib.request import Request,urlopen
import argparse,hashlib,json,mimetypes,os,re,time,uuid
ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'library'/'works'; STATE=ROOT/'private'/'acquisition_state.json'; CAND=ROOT/'private'/'acquisition_candidates.json'; INDEX=ROOT/'data'/'ingested_library.json'
ALLOW={'archive.org','www.archive.org','gutenberg.org','www.gutenberg.org','api.github.com','raw.githubusercontent.com','upload.wikimedia.org','commons.wikimedia.org','wikisource.org','en.wikisource.org','fr.wikisource.org','ar.wikisource.org'}
ACCEPT={'public domain','public domain mark','cc0','unrestricted'}
UA='ProphetBiographyLibrary/6.9'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''): h.update(b)
 return h.hexdigest()
def safe_url(u):
 x=urlparse(str(u or '')); return x.scheme=='https' and x.hostname in ALLOW
def rights_ok(r): return any(x in str(r or '').lower() for x in ACCEPT)
def request_headers():
 h={'User-Agent':UA,'Accept':'*/*'}
 token=os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
 if token: h['Authorization']='Bearer '+token
 return h
def get(u,timeout=90):
 if not safe_url(u): raise RuntimeError('domain-not-allowlisted')
 with urlopen(Request(u,headers=request_headers()),timeout=timeout) as r:
  b=r.read(); ct=(r.headers.get('content-type') or '').split(';')[0].lower(); return b,ct,str(r.geturl())
def validate_bytes(b,kind):
 if len(b)<1024: return False,'too-small'
 if kind=='pdf' and not b.startswith(b'%PDF'): return False,'not-pdf'
 if kind=='epub' and not b.startswith(b'PK'): return False,'not-epub'
 head=b[:300].lower().lstrip()
 if (head.startswith(b'<!doctype html') or head.startswith(b'<html')) and kind in {'pdf','epub','txt'}: return False,'html-error-page'
 return True,'ok'
def slug(s): return re.sub(r'[^a-z0-9\u0600-\u06ff]+','-',str(s).lower()).strip('-')[:90] or uuid.uuid4().hex[:12]
def read_json(path,default):
 try:return json.loads(path.read_text(encoding='utf8'))
 except Exception:return default
def save_state(d): STATE.parent.mkdir(parents=True,exist_ok=True); STATE.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def get_json_url(url):
 b,_,_=get(url,timeout=60); return json.loads(b.decode('utf-8','replace'))

def gutenberg_text_url(x):
 if str(x.get('sourceRepository') or '').lower()!='project gutenberg': return ''
 source=str(x.get('sourceUrl') or '').strip(); ident=str(x.get('sourceIdentifier') or '').strip()
 if not safe_url(source) or not ident.isdigit(): return ''
 try:
  page,_,final=get(source,timeout=60); html=page.decode('utf-8','replace')
 except Exception:return ''
 patterns=[r'href=["\']([^"\']*?/ebooks/'+re.escape(ident)+r'\.txt\.utf-8)["\']',r'href=["\']([^"\']*?/cache/epub/'+re.escape(ident)+r'/pg'+re.escape(ident)+r'\.txt)["\']',r'href=["\']([^"\']+\.txt(?:\?[^"\']*)?)["\']']
 for pat in patterns:
  m=re.search(pat,html,re.I)
  if m:
   u=urljoin(final,m.group(1).replace('&amp;','&'))
   if safe_url(u): return u
 return ''

def gitenberg_text_url(x):
 """Resolve the same Project Gutenberg text through the GITenberg GitHub mirror."""
 if str(x.get('sourceRepository') or '').lower()!='project gutenberg': return ''
 ident=str(x.get('sourceIdentifier') or '').strip()
 if not ident.isdigit(): return ''
 try:
  search=get_json_url('https://api.github.com/search/repositories?q='+quote_plus('org:GITenberg '+ident)+'&per_page=10')
  repos=search.get('items',[]) if isinstance(search,dict) else []
  repos=[r for r in repos if str(r.get('name') or '').endswith('_'+ident) and str((r.get('owner') or {}).get('login') or '').lower()=='gitenberg'] or repos
  for repo in repos:
   full=str(repo.get('full_name') or '')
   if not full.startswith('GITenberg/'): continue
   branch=str(repo.get('default_branch') or 'master')
   listing=get_json_url('https://api.github.com/repos/'+full+'/contents/?ref='+branch)
   if not isinstance(listing,list): continue
   txt=[f for f in listing if str(f.get('type'))=='file' and str(f.get('name') or '').lower().endswith('.txt') and f.get('download_url')]
   def rank(f):
    n=str(f.get('name') or '').lower()
    if n==ident+'.txt': return (0,n)
    if n in {ident+'-8.txt','pg'+ident+'.txt'}: return (1,n)
    if ident in n:return (2,n)
    return (3,n)
   for f in sorted(txt,key=rank):
    u=str(f.get('download_url') or '')
    if safe_url(u): return u
  return ''
 except Exception:return ''

def download_candidate(x,kind):
 urls=[]; first=str(x.get('downloadUrl') or '').strip()
 if first: urls.append(first)
 if kind=='txt':
  official=gutenberg_text_url(x)
  if official and official not in urls: urls.append(official)
  mirror=gitenberg_text_url(x)
  if mirror and mirror not in urls: urls.append(mirror)
 errors=[]
 for u in urls:
  if not safe_url(u): errors.append('domain-not-allowlisted'); continue
  try:b,ct,final=get(u)
  except Exception as e: errors.append('download:'+type(e).__name__); continue
  ok,why=validate_bytes(b,kind)
  if ok:return b,ct,final,''
  errors.append(why)
 return None,'','',errors[-1] if errors else 'no-download-url'

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--limit',type=int,default=25); ap.add_argument('--dry-run',action='store_true'); a=ap.parse_args()
 c=read_json(CAND,{'items':[]}); old=read_json(STATE,{'items':[]}); now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
 history={str(x.get('workId') or x.get('catalogueId') or x.get('sourceIdentifier') or i):x for i,x in enumerate(old.get('items',[]))}
 published=set(); idx=read_json(INDEX,{'items':[]})
 for x in idx.get('items',[]):
  wid=str(x.get('workId') or '').strip()
  if wid: published.add(wid)
 acquired=skipped=failed=rejected=0
 def keep(row):
  key=str(row.get('workId') or row.get('catalogueId') or row.get('sourceIdentifier') or len(history)); history[key]=row
 for x in c.get('items',[]):
  row=dict(x); wid=str(x.get('workId') or '').strip(); row['checkedAt']=now
  if wid and wid in published: row['status']='ALREADY_PUBLISHED'; row['error']=''; keep(row); skipped+=1; continue
  row['status']='UNLICENCED_CHECK'
  if not rights_ok(x.get('rightsEvidence')): row['status']='REJECTED'; row['error']='rights-not-unrestricted'; keep(row); rejected+=1; continue
  row['status']='UNLICENCED_CONFIRMED'
  pg=str(x.get('sourceRepository') or '').lower()=='project gutenberg'
  if not safe_url(x.get('downloadUrl','')) and not (pg and safe_url(x.get('sourceUrl',''))): row['status']='REJECTED'; row['error']='download-domain-not-allowlisted'; keep(row); rejected+=1; continue
  if a.dry_run: row['status']='DISCOVERED'; keep(row); continue
  kind=str(x.get('format') or 'txt').lower(); b,ct,downloaded_url,error=download_candidate(x,kind)
  if b is None: row['status']='FAILED'; row['error']=error; keep(row); failed+=1; continue
  wid=wid or slug(x.get('titleOriginal')); eid=x.get('editionId') or 'ed-'+hashlib.sha256(b).hexdigest()[:12]
  ed=STORE/wid/'editions'/eid; ed.mkdir(parents=True,exist_ok=True); ext={'pdf':'pdf','epub':'epub','txt':'txt','html':'html'}.get(kind,kind); orig=ed/f'original.{ext}'; orig.write_bytes(b)
  digest=sha(orig); meta={k:x.get(k) for k in ['titleOriginal','titleAr','titleEn','titleFr','author','language','subjects','siteSections','sourceRepository','sourceIdentifier','sourceUrl']}; meta.update({'workId':wid,'editionId':eid,'format':kind,'mimeType':ct or mimetypes.guess_type(orig.name)[0],'size':len(b),'sha256':digest,'status':'DOWNLOADED','readable':kind in {'txt','html','pdf','epub'},'searchable':kind in {'txt','html'},'listenable':kind in {'txt','html'},'watchable':False})
  (ed/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  (ed/'rights.json').write_text(json.dumps({'status':'UNLICENCED_CONFIRMED','evidence':x.get('rightsEvidence'),'evidenceUrl':x.get('rightsEvidenceUrl'),'checkedAt':now},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  mirror='GITenberg' if 'raw.githubusercontent.com/GITenberg/' in downloaded_url else ''
  (ed/'provenance.json').write_text(json.dumps({'sourceRepository':x.get('sourceRepository'),'sourceIdentifier':x.get('sourceIdentifier'),'sourceUrl':x.get('sourceUrl'),'requestedDownloadUrl':x.get('downloadUrl'),'downloadUrl':downloaded_url,'transportMirror':mirror,'retrievalDate':now,'originalFilename':orig.name,'sha256':digest,'size':len(b),'mimeType':meta['mimeType']},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  row.update({'status':'DOWNLOADED','resolvedDownloadUrl':downloaded_url,'transportMirror':mirror,'localPath':str(orig.relative_to(ROOT)).replace('\\','/'),'sha256':digest,'editionId':eid,'error':''}); keep(row); acquired+=1
  if acquired>=a.limit: break
 state={'schema':'strict-acquisition-v4','updatedAt':now,'publishedWorkIdsKnown':len(published),'items':list(history.values())}
 save_state(state); print(json.dumps({'acquired':acquired,'alreadyPublished':skipped,'failed':failed,'rejected':rejected,'stateItems':len(history),'state':str(STATE.relative_to(ROOT))},ensure_ascii=False))
if __name__=='__main__': main()
