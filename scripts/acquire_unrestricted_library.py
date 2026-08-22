#!/usr/bin/env python3
"""Strict acquisition engine for unrestricted/public-domain assets.
MASTER RULE: EPUB/text/Word/native formats are tried before PDF/OCR.
"""
from pathlib import Path
from urllib.parse import urlparse,urljoin,quote_plus
from urllib.request import Request,urlopen
import argparse,hashlib,json,mimetypes,os,re,time,uuid
ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'library'/'works';STATE=ROOT/'private'/'acquisition_state.json';CAND=ROOT/'private'/'acquisition_candidates.json';INDEX=ROOT/'data'/'ingested_library.json'
ALLOW={'archive.org','www.archive.org','gutenberg.org','www.gutenberg.org','api.github.com','raw.githubusercontent.com','upload.wikimedia.org','commons.wikimedia.org','wikisource.org','en.wikisource.org','fr.wikisource.org','ar.wikisource.org'}
ACCEPT={'public domain','public domain mark','cc0','unrestricted'}
PRIORITY=['epub','txt','docx','doc','odt','rtf','html','htm','md','xml','pdf']
UA='ProphetBiographyLibrary/7.1-source-first'

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def safe_url(u):
 x=urlparse(str(u or ''));return x.scheme=='https' and x.hostname in ALLOW
def rights_ok(r):return any(x in str(r or '').lower() for x in ACCEPT)
def request_headers():
 h={'User-Agent':UA,'Accept':'*/*'};token=os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
 if token:h['Authorization']='Bearer '+token
 return h
def get(u,timeout=120):
 if not safe_url(u):raise RuntimeError('domain-not-allowlisted')
 with urlopen(Request(u,headers=request_headers()),timeout=timeout) as r:
  b=r.read();ct=(r.headers.get('content-type') or '').split(';')[0].lower();return b,ct,str(r.geturl())
def validate_bytes(b,kind):
 if len(b)<1024:return False,'too-small'
 head=b[:512].lower().lstrip()
 if kind=='pdf' and not b.startswith(b'%PDF'):return False,'not-pdf'
 if kind in {'epub','docx','odt'} and not b.startswith(b'PK'):return False,'not-zip-container'
 if kind=='doc' and not b.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):return False,'not-ole-doc'
 if kind in {'txt','md','xml','html','htm','rtf'} and b'\x00' in b[:4096]:return False,'binary-not-text'
 if (head.startswith(b'<!doctype html') or head.startswith(b'<html')) and kind not in {'html','htm'}:return False,'html-error-page'
 return True,'ok'
def slug(s):return re.sub(r'[^a-z0-9\u0600-\u06ff]+','-',str(s).lower()).strip('-')[:90] or uuid.uuid4().hex[:12]
def read_json(path,default):
 try:return json.loads(path.read_text(encoding='utf8'))
 except Exception:return default
def save_state(d):STATE.parent.mkdir(parents=True,exist_ok=True);STATE.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def get_json_url(url):
 b,_,_=get(url,timeout=60);return json.loads(b.decode('utf-8','replace'))
def infer_kind(url,default='txt'):
 p=urlparse(str(url or '')).path.lower()
 for k in PRIORITY:
  if p.endswith('.'+k) or (k=='htm' and p.endswith('.html')):return k
 return default

def gutenberg_text_url(x):
 if str(x.get('sourceRepository') or '').lower()!='project gutenberg':return ''
 source=str(x.get('sourceUrl') or '').strip();ident=str(x.get('sourceIdentifier') or '').strip()
 if not safe_url(source) or not ident.isdigit():return ''
 try:page,_,final=get(source,timeout=60);html=page.decode('utf-8','replace')
 except Exception:return ''
 pats=[r'href=["\']([^"\']*?/ebooks/'+re.escape(ident)+r'\.txt\.utf-8)["\']',r'href=["\']([^"\']*?/cache/epub/'+re.escape(ident)+r'/pg'+re.escape(ident)+r'\.txt)["\']',r'href=["\']([^"\']+\.txt(?:\?[^"\']*)?)["\']']
 for pat in pats:
  m=re.search(pat,html,re.I)
  if m:
   u=urljoin(final,m.group(1).replace('&amp;','&'))
   if safe_url(u):return u
 return ''
def gitenberg_text_url(x):
 if str(x.get('sourceRepository') or '').lower()!='project gutenberg':return ''
 ident=str(x.get('sourceIdentifier') or '').strip()
 if not ident.isdigit():return ''
 try:
  search=get_json_url('https://api.github.com/search/repositories?q='+quote_plus('org:GITenberg '+ident)+'&per_page=10');repos=search.get('items',[]) if isinstance(search,dict) else []
  repos=[r for r in repos if str(r.get('name') or '').endswith('_'+ident) and str((r.get('owner') or {}).get('login') or '').lower()=='gitenberg'] or repos
  for repo in repos:
   full=str(repo.get('full_name') or '');branch=str(repo.get('default_branch') or 'master')
   if not full.startswith('GITenberg/'):continue
   listing=get_json_url('https://api.github.com/repos/'+full+'/contents/?ref='+branch)
   if not isinstance(listing,list):continue
   for f in sorted([f for f in listing if str(f.get('type'))=='file' and str(f.get('name') or '').lower().endswith('.txt') and f.get('download_url')],key=lambda f:(0 if str(f.get('name') or '').lower() in {ident+'.txt',ident+'-8.txt','pg'+ident+'.txt'} else 1,str(f.get('name') or ''))):
    u=str(f.get('download_url') or '')
    if safe_url(u):return u
 except Exception:return ''
 return ''
def candidate_urls(x):
 requested=str(x.get('format') or 'txt').lower();out=[]
 def add(u,k=None,label='candidate'):
  u=str(u or '').strip()
  if u and safe_url(u) and not any(z[0]==u for z in out):out.append((u,k or infer_kind(u,requested),label))
 add(x.get('downloadUrl'),requested,'primary')
 add(x.get('fallbackDownloadUrl'),infer_kind(x.get('fallbackDownloadUrl'),'txt'),'fallback')
 for row in x.get('alternateDownloads') or []:
  if isinstance(row,dict):add(row.get('url'),str(row.get('format') or infer_kind(row.get('url'),requested)).lower(),'alternate')
  else:add(row,None,'alternate')
 if str(x.get('sourceRepository') or '').lower()=='project gutenberg':
  ident=str(x.get('sourceIdentifier') or '').strip()
  if ident.isdigit():
   add(f'https://www.gutenberg.org/ebooks/{ident}.epub3.images','epub','gutenberg-epub')
   add(gutenberg_text_url(x),'txt','gutenberg-text')
   add(gitenberg_text_url(x),'txt','gitenberg-text')
 return sorted(out,key=lambda z:PRIORITY.index(z[1]) if z[1] in PRIORITY else 99)
def download_candidate(x):
 errors=[]
 for u,kind,label in candidate_urls(x):
  try:b,ct,final=get(u)
  except Exception as e:errors.append(f'{label}:download:{type(e).__name__}');continue
  ok,why=validate_bytes(b,kind)
  if ok:return b,ct,final,'',kind,label
  errors.append(f'{label}:{why}')
 return None,'','','',str(x.get('format') or 'txt').lower(),errors[-1] if errors else 'no-download-url'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=25);ap.add_argument('--dry-run',action='store_true');a=ap.parse_args()
 c=read_json(CAND,{'items':[]});old=read_json(STATE,{'items':[]});now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());history={str(x.get('workId') or x.get('catalogueId') or x.get('sourceIdentifier') or i):x for i,x in enumerate(old.get('items',[]))};idx=read_json(INDEX,{'items':[]});published={str(x.get('workId') or '') for x in idx.get('items',[]) if x.get('workId')};acquired=skipped=failed=rejected=0
 def keep(row):history[str(row.get('workId') or row.get('catalogueId') or row.get('sourceIdentifier') or len(history))]=row
 for x in c.get('items',[]):
  row=dict(x);wid=str(x.get('workId') or '').strip();row['checkedAt']=now
  if wid and wid in published:row['status']='ALREADY_PUBLISHED';row['error']='';keep(row);skipped+=1;continue
  row['status']='UNLICENCED_CHECK'
  if not rights_ok(x.get('rightsEvidence')):row['status']='REJECTED';row['error']='rights-not-unrestricted';keep(row);rejected+=1;continue
  if not x.get('nativeSearchCompleted') and str(x.get('format') or '').lower()=='pdf':row['status']='REJECTED';row['error']='native-search-required-before-pdf-ocr';keep(row);rejected+=1;continue
  row['status']='UNLICENCED_CONFIRMED'
  if not any(safe_url(u) for u,_,_ in candidate_urls(x)):row['status']='REJECTED';row['error']='download-domain-not-allowlisted';keep(row);rejected+=1;continue
  if a.dry_run:row['status']='DISCOVERED';keep(row);continue
  b,ct,downloaded_url,error,kind,selected=download_candidate(x)
  if b is None:row['status']='FAILED';row['error']=selected;keep(row);failed+=1;continue
  wid=wid or slug(x.get('titleOriginal'));eid=x.get('editionId') or 'ed-'+hashlib.sha256(b).hexdigest()[:12];ed=STORE/wid/'editions'/eid;ed.mkdir(parents=True,exist_ok=True);ext='html' if kind=='htm' else kind;orig=ed/f'original.{ext}';orig.write_bytes(b);digest=sha(orig)
  textlike=kind in {'txt','html','htm','md','xml','rtf'};meta={k:x.get(k) for k in ['titleOriginal','titleAr','titleEn','titleFr','author','language','subjects','siteSections','sourceRepository','sourceIdentifier','sourceUrl']};meta.update({'workId':wid,'editionId':eid,'format':kind,'mimeType':ct or mimetypes.guess_type(orig.name)[0],'size':len(b),'sha256':digest,'status':'DOWNLOADED','readable':kind in {'txt','html','htm','md','xml','rtf','doc','docx','odt','pdf','epub'},'searchable':textlike,'listenable':textlike,'watchable':False,'nativeSearchCompleted':True,'selectedByPriority':selected})
  (ed/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n',encoding='utf8');(ed/'rights.json').write_text(json.dumps({'status':'UNLICENCED_CONFIRMED','evidence':x.get('rightsEvidence'),'evidenceUrl':x.get('rightsEvidenceUrl'),'checkedAt':now},ensure_ascii=False,indent=2)+'\n',encoding='utf8');mirror='GITenberg' if 'raw.githubusercontent.com/GITenberg/' in downloaded_url else '';(ed/'provenance.json').write_text(json.dumps({'sourceRepository':x.get('sourceRepository'),'sourceIdentifier':x.get('sourceIdentifier'),'sourceUrl':x.get('sourceUrl'),'requestedDownloadUrl':x.get('downloadUrl'),'downloadUrl':downloaded_url,'transportMirror':mirror,'retrievalDate':now,'originalFilename':orig.name,'sha256':digest,'size':len(b),'mimeType':meta['mimeType'],'nativeSearchCompleted':True,'selectedByPriority':selected},ensure_ascii=False,indent=2)+'\n',encoding='utf8');row.update({'status':'DOWNLOADED','resolvedDownloadUrl':downloaded_url,'resolvedFormat':kind,'selectedByPriority':selected,'nativeSearchCompleted':True,'transportMirror':mirror,'localPath':str(orig.relative_to(ROOT)).replace('\\','/'),'sha256':digest,'editionId':eid,'error':''});keep(row);acquired+=1
  if acquired>=a.limit:break
 state={'schema':'strict-acquisition-v5-source-first','updatedAt':now,'publishedWorkIdsKnown':len(published),'formatPriority':PRIORITY,'items':list(history.values())};save_state(state);print(json.dumps({'acquired':acquired,'alreadyPublished':skipped,'failed':failed,'rejected':rejected,'stateItems':len(history),'state':str(STATE.relative_to(ROOT)),'priority':PRIORITY},ensure_ascii=False))
if __name__=='__main__':main()
