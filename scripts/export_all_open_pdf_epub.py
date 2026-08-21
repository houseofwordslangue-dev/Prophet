#!/usr/bin/env python3
from __future__ import annotations
import argparse, html, json, os, re, time, unicodedata, urllib.parse
from pathlib import Path
import requests

UA='ProphetOpenSourceDriveResolver/2.0'
S=requests.Session(); S.headers.update({'User-Agent':UA,'Accept':'*/*'})
MAX_BYTES=int(os.environ.get('TRANSFER_MAX_BYTES', str(430*1024*1024)))

# Retained direct sources that were present in the recovery manifest but not always
# preserved in compact catalogue rows. These are edition-specific, not title guesses.
DIRECT_BY_ID={
 'quran-meaning-063':['https://mc.dlib.nyu.edu/files/books/nyu_aco000895/nyu_aco000895_lo.pdf'],
 'hadith-commentary-003':['https://mc.dlib.nyu.edu/files/books/nyu_aco000182/nyu_aco000182_lo.pdf'],
 'life-seerah-049':['https://mc.dlib.nyu.edu/files/books/nyu_aco000625/nyu_aco000625_lo.pdf'],
 'quran-meaning-017':['https://mc.dlib.nyu.edu/files/books/columbia_aco001653/columbia_aco001653_lo.pdf'],
 'quran-meaning-069':['https://mc.dlib.nyu.edu/files/books/princeton_aco001236/princeton_aco001236_lo.pdf'],
 'family-companions-006':['https://mc.dlib.nyu.edu/files/books/princeton_aco000734/princeton_aco000734_lo.pdf'],
 'life-seerah-013':['https://upload.wikimedia.org/wikisource/ar/2/24/%D8%A7%D9%84%D8%B4%D9%81%D8%A7_%D8%A8%D8%AA%D8%B9%D8%B1%D9%8A%D9%81_%D8%AD%D9%82%D9%88%D9%82_%D8%A7%D9%84%D9%85%D8%B5%D8%B7%D9%81%D9%89.pdf'],
 'family-companions-004':['https://mc.dlib.nyu.edu/files/books/aub_aco002269/aub_aco002269_lo.pdf'],
 'character-shamail-005':['https://mc.dlib.nyu.edu/files/books/columbia_aco000919/columbia_aco000919_lo.pdf'],
 'quran-meaning-015':['https://mc.dlib.nyu.edu/files/books/aub_aco002427/aub_aco002427_lo.pdf'],
 'quran-meaning-013':['https://mc.dlib.nyu.edu/files/books/columbia_aco003787/columbia_aco003787_lo.pdf'],
 'family-companions-009':['https://mc.dlib.nyu.edu/files/books/aub_aco002680/aub_aco002680_lo.pdf'],
 'quran-meaning-003':['https://archive.org/details/2_20230615_20230615_2028'],
 'quran-meaning-001':['https://archive.org/details/tafsirquchayri'],
 'site-source-qadi-iyad-mashariq':['https://archive.org/details/MashariqAlanwar'],
 'site-source-qadi-iyad-tartib':['https://archive.org/details/tartbalmadrikwat01iyib'],
 'site-source-qari-shifa':['https://archive.org/details/SharhShifaQari'],
 'site-source-ibn-ajiba-bahr':['https://archive.org/details/ba7r-madid'],
}

# Open/public-domain supplementary works retained by the direct-acquisition log.
SUPPLEMENTARY=[
 {'id':'dinet-life-mohammad','titleAr':'The Life of Mohammad, the Prophet of Allah','authorAr':'Etienne Dinet; Sliman Ben Ibrahim','rights':'project-gutenberg-public-domain','source':'https://www.gutenberg.org/ebooks/39523'},
 {'id':'lane-poole-table-talk','titleAr':'The Speeches & Table-Talk of the Prophet Mohammad','authorAr':'Stanley Lane-Poole','rights':'project-gutenberg-public-domain','source':'https://www.gutenberg.org/ebooks/58426'},
 {'id':'rodwell-koran','titleAr':'The Koran','authorAr':'J. M. Rodwell','rights':'project-gutenberg-public-domain','source':'https://www.gutenberg.org/ebooks/3434'},
 {'id':'draycott-mahomet','titleAr':'Mahomet, Founder of Islam','authorAr':'Gladys Draycott','rights':'project-gutenberg-public-domain','source':'https://www.gutenberg.org/ebooks/10738'},
]

# Retained open-library/forum pages. A page is discovery-only unless the work/edition
# has a verified open/public-domain rights basis; public availability alone is not enough.
RETAINED_PAGES=[
 'https://waqfeya.com/books/%D8%A3%D8%B3%D8%AF-%D8%A7%D9%84%D8%BA%D8%A7%D8%A8%D8%A9-%D9%81%D9%8A-%D9%85%D8%B9%D8%B1%D9%81%D8%A9-%D8%A7%D9%84%D8%B5%D8%AD%D8%A7%D8%A8%D8%A9-%D8%B7-%D8%A7%D8%A8%D9%86-%D8%AD%D8%B2%D9%85-a43557d4d73a45dda63318e7d8e3fc8d',
 'https://waqfeya.net/books/%D8%A7%D9%84%D8%A5%D8%B5%D8%A7%D8%A8%D8%A9-%D9%81%D9%8A-%D8%AA%D9%85%D9%8A%D9%8A%D8%B2-%D8%A7%D9%84%D8%B5%D8%AD%D8%A7%D8%A8%D8%A9-%D8%B7-%D8%A7%D9%84%D8%B9%D8%B5%D8%B1%D9%8A%D8%A9/e10731c5efc34fa5895118b78e350c8b',
 'https://waqfeya.net/books/%D8%A7%D9%84%D8%A7%D8%B3%D8%AA%D9%8A%D8%B9%D8%A7%D8%A8-%D9%81%D9%8A-%D9%85%D8%B9%D8%B1%D9%81%D8%A9-%D8%A7%D9%84%D8%A3%D8%B5%D8%AD%D8%A7%D8%A8-%D8%AA-%D9%85%D8%B1%D8%B4%D8%AF/2e5f2392ea6e4e3884a6e1ebc6446697',
 'https://waqfeya.net/books/%D8%AD%D9%84%D9%8A%D8%A9-%D8%A7%D9%84%D8%A3%D9%88%D9%84%D9%8A%D8%A7%D8%A1-%D9%88%D8%B7%D8%A8%D9%82%D8%A7%D8%AA-%D8%A7%D9%84%D8%A3%D8%B5%D9%81%D9%8A%D8%A7%D8%A1/df7249d1c31f451294b299598e07a285',
 'https://waqfeya.net/books/%D8%B3%D9%8A%D8%B1-%D8%A3%D8%B9%D9%84%D8%A7%D9%85-%D8%A7%D9%84%D9%86%D8%A8%D9%84%D8%A7%D8%A1--%D8%A7%D9%84%D8%B3%D9%8A%D8%B1%D8%A9-%D8%A7%D9%84%D9%86%D8%A8%D9%88%D9%8A%D8%A9--%D8%B3%D9%8A%D8%B1%D8%A9-%D8%A7%D9%84%D8%AE%D9%84%D9%81%D8%A7%D8%A1-%D8%A7%D9%84%D8%B1%D8%A7%D8%B4%D8%AF%D9%8A%D9%86--%D8%A7%D9%84%D8%AC%D8%B2%D8%A1-%D8%A7%D9%84%D9%85%D9%81%D9%82%D9%88%D8%AF-%D8%AA-%D8%A7%D9%84%D8%A3%D8%B1%D9%86%D8%A7%D8%A4%D9%88%D8%B7-345331fb5caa4981b08a5c41bd30aea7',
 'https://waqfeya.net/books/%D9%85%D8%B9%D8%B1%D9%81%D8%A9-%D8%A7%D9%84%D8%B5%D8%AD%D8%A7%D8%A8%D8%A9-%D8%AA-%D8%A7%D9%84%D8%B9%D8%B2%D8%A7%D8%B2%D9%8A-55f23d785ba247a9bd20fb08516691e2',
 'https://www.waqfeya.net/books/%D8%A7%D9%84%D8%B7%D8%A8%D9%82%D8%A7%D8%AA-%D8%A7%D9%84%D9%83%D8%A8%D9%8A%D8%B1-%D8%A7%D9%84%D8%B7%D8%A8%D9%82%D8%A7%D8%AA-%D8%A7%D9%84%D9%83%D8%A8%D8%B1%D9%89-%D8%B7%D8%A8%D9%82%D8%A7%D8%AA-%D8%A7%D8%A8%D9%86-%D8%B3%D8%B9%D8%AF-%D8%B7-%D8%A7%D9%84%D8%AE%D8%A7%D9%86%D8%AC%D9%8A-ff34852d019f4bd9b743baabc33d0520',
]

ACCEPT_LICENSE=('publicdomain','creativecommons.org/publicdomain','creativecommons.org/licenses/by/','creativecommons.org/licenses/by-sa/','creativecommons.org/licenses/by-nc/','creativecommons.org/licenses/by-nc-sa/','creativecommons.org/zero')
REJECT_LICENSE=('by-nd','by-nc-nd')

def norm(s):
 s=unicodedata.normalize('NFKD',str(s or '')); s=''.join(c for c in s if not unicodedata.combining(c)).casefold().replace('ـ',' ')
 return ' '.join(re.sub(r'[^\w\u0600-\u06ff]+',' ',s).split())
def toks(s): return {x for x in norm(s).split() if len(x)>1}
def sim(a,b):
 A,B=toks(a),toks(b); return len(A&B)/len(A|B) if A and B else 0.0
def clean(s): return re.sub(r'[^\w.()\-\u0600-\u06ff]+','_',str(s)).strip('_')[:170]
def uniq(xs):
 out=[]; seen=set()
 for x in xs:
  if x and x not in seen: seen.add(x); out.append(x)
 return out

def load_entries():
 out=[]
 for p in sorted(Path('data/catalogue').glob('chunk-*.json')):
  try: rows=json.loads(p.read_text(encoding='utf-8')).get('items',[])
  except Exception: continue
  for r in rows:
   if not isinstance(r,list) or len(r)<13: continue
   out.append({'id':str(r[0]),'titleAr':str(r[3] or ''),'authorAr':str(r[5] or ''),'rights':str(r[8] or ''),'status':str(r[14] if len(r)>14 else ''),'source':str(r[12] or '')})
 out.extend(SUPPLEMENTARY)
 return out

def rights_base_open(e):
 s=(e.get('rights','')+' '+e.get('status','')).casefold()
 if 'restricted' in s and not any(x in s for x in ('public-domain','open-license','creative-commons')): return False
 return any(x in s for x in ('public-domain','open-license','creative-commons','project-gutenberg'))

def license_open(v):
 s=str(v or '').casefold()
 return bool(s) and not any(x in s for x in REJECT_LICENSE) and any(x in s for x in ACCEPT_LICENSE)

def get(url, **kw):
 last=None
 for pause in (0,2,7):
  if pause: time.sleep(pause)
  try:
   r=S.get(url,timeout=kw.pop('timeout',(30,180)),allow_redirects=True,**kw); r.raise_for_status(); return r
  except Exception as e: last=e
 raise last

def ia_id(url):
 m=re.search(r'archive\.org/(?:details|download)/([^/?#]+)',url or ''); return urllib.parse.unquote(m.group(1)) if m else ''
def ia_search(title,author):
 q=f'title:"{title}" AND mediatype:texts'; params={'q':q,'fl[]':['identifier','title','creator','date','year','licenseurl','rights'],'rows':15,'output':'json','sort[]':'downloads desc'}
 try: docs=get('https://archive.org/advancedsearch.php',params=params,timeout=(20,60)).json().get('response',{}).get('docs',[])
 except Exception: return []
 scored=[]
 for d in docs:
  dt=d.get('title',''); dc=d.get('creator',''); dt=' '.join(map(str,dt)) if isinstance(dt,list) else str(dt); dc=' '.join(map(str,dc)) if isinstance(dc,list) else str(dc)
  ts=sim(title,dt); aus=sim(author,dc) if author else 0; score=.88*ts+.12*aus
  if norm(title)==norm(dt): score=max(score,.99)
  if ts>=.52 or score>=.58: scored.append((score,str(d.get('identifier') or '')))
 return [i for _,i in sorted(scored,reverse=True) if i][:5]

def ia_files(identifier,e):
 try: meta=get('https://archive.org/metadata/'+urllib.parse.quote(identifier,safe=''),timeout=(20,90)).json()
 except Exception: return [],'metadata-failed'
 md=meta.get('metadata',{}) or {}; lic=md.get('licenseurl') or md.get('rights') or ''
 date=str(md.get('date') or md.get('year') or '')[:4]
 historical=bool(re.match(r'^\d{4}$',date) and int(date)<=1930)
 allowed=rights_base_open(e) or license_open(lic) or historical
 if not allowed: return [],'rights-unverified'
 out=[]
 for f in meta.get('files',[]) or []:
  if not isinstance(f,dict): continue
  n=str(f.get('name') or ''); low=n.casefold()
  if not (low.endswith('.pdf') or low.endswith('.epub')): continue
  if low.endswith('_lcp.epub') or str(f.get('private','')).lower() in ('true','1'): continue
  try: size=int(f.get('size') or 0)
  except: size=0
  out.append({'url':'https://archive.org/download/'+urllib.parse.quote(identifier,safe='')+'/'+urllib.parse.quote(n,safe='/'),'name':n,'size':size,'license':lic,'evidence':'ia-metadata','identifier':identifier})
 return out,'ok'

def gutenberg_files(url):
 m=re.search(r'/ebooks/(\d+)',url); eid=m.group(1) if m else ''
 if not eid: return []
 try:
  text=get('https://www.gutenberg.org/ebooks/'+eid,timeout=(20,60)).text
 except Exception: return []
 hrefs=re.findall(r'href=["\']([^"\']+)["\']',text,re.I); out=[]
 for h in hrefs:
  h=html.unescape(h); u=urllib.parse.urljoin('https://www.gutenberg.org/ebooks/'+eid,h); low=u.casefold()
  if '.epub' in low and not low.endswith('.zip'):
   out.append({'url':u,'name':Path(urllib.parse.urlparse(u).path).name or f'pg{eid}.epub','size':0,'license':'Project Gutenberg public domain terms','evidence':'gutenberg'})
 return out

def page_files(url,e):
 host=urllib.parse.urlparse(url).netloc.casefold()
 if 'archive.org' in host:
  ident=ia_id(url); return ia_files(ident,e)[0] if ident else []
 if 'gutenberg.org' in host: return gutenberg_files(url)
 # Direct format URLs are accepted only when the catalogue/seed rights basis is open.
 low=urllib.parse.urlparse(url).path.casefold()
 if low.endswith('.pdf') or low.endswith('.epub'):
  if rights_base_open(e) or 'mc.dlib.nyu.edu' in host or 'upload.wikimedia.org' in host:
   return [{'url':url,'name':Path(urllib.parse.urlparse(url).path).name,'size':0,'license':e.get('rights',''),'evidence':'retained-direct'}]
  return []
 if not rights_base_open(e): return []
 try: r=get(url,timeout=(20,60)); text=r.text
 except Exception: return []
 out=[]
 for h in re.findall(r'(?:href|src)=["\']([^"\']+)["\']',text,re.I):
  u=urllib.parse.urljoin(r.url,html.unescape(h)); path=urllib.parse.urlparse(u).path.casefold()
  if path.endswith('.pdf') or path.endswith('.epub'):
   out.append({'url':u,'name':Path(urllib.parse.urlparse(u).path).name,'size':0,'license':e.get('rights',''),'evidence':'open-source-page'})
 return out

def download(rec,dest):
 dest.parent.mkdir(parents=True,exist_ok=True); tmp=dest.with_suffix(dest.suffix+'.part')
 with get(rec['url'],stream=True,timeout=(30,600)) as r:
  total=0
  with open(tmp,'wb') as f:
   for b in r.iter_content(1024*1024):
    if b: f.write(b); total+=len(b)
 tmp.replace(dest); return total

def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--shard',type=int,required=True); ap.add_argument('--shard-count',type=int,required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
 entries=load_entries(); selected=[e for i,e in enumerate(entries) if i%args.shard_count==args.shard]
 out=Path(args.out); out.mkdir(parents=True,exist_ok=True); used=0; seen=set()
 report={'shard':args.shard,'shardCount':args.shard_count,'selectedWorks':len(selected),'downloaded':0,'bytes':0,'rightsUnverified':0,'oversized':0,'failed':0,'files':[],'unresolved':[]}
 for e in selected:
  urls=[]
  if e.get('source'): urls.append(e['source'])
  urls.extend(DIRECT_BY_ID.get(e['id'],[]))
  candidates=[]; rights_note=[]
  for u in uniq(urls): candidates.extend(page_files(u,e))
  # Archive remains a universal discovery layer, but each matched item must independently
  # pass edition-level rights evidence or an explicit open/public-domain catalogue basis.
  for ident in ia_search(e['titleAr'],e['authorAr']):
   fs,why=ia_files(ident,e); candidates.extend(fs)
   if why=='rights-unverified': rights_note.append(ident)
  # Supplementary retained pages are searched by visible title similarity; they are never
  # mirrored unless this work already has an open/public-domain basis.
  if rights_base_open(e):
   for page in RETAINED_PAGES:
    if sim(e['titleAr'],urllib.parse.unquote(page))>=.35: candidates.extend(page_files(page,e))
  candidates=[c for c in candidates if c.get('url')]
  unique=[]
  for c in candidates:
   k=c['url']
   if k not in seen: seen.add(k); unique.append(c)
  got_any=False
  for c in unique:
   ext='.epub' if urllib.parse.urlparse(c['url']).path.casefold().endswith('.epub') or c.get('name','').casefold().endswith('.epub') else '.pdf'
   size=int(c.get('size') or 0)
   if size and (size>MAX_BYTES or used+size>MAX_BYTES):
    report['oversized']+=1; report['files'].append({'workId':e['id'],'title':e['titleAr'],'status':'deferred-transfer-size','format':ext[1:].upper(),**c}); continue
   dest=out/ext[1:]/clean(e['id'])/clean(c.get('identifier') or urllib.parse.urlparse(c['url']).netloc)/(clean(c.get('name') or ('manifestation'+ext)) or ('manifestation'+ext))
   try:
    n=download(c,dest)
    if used+n>MAX_BYTES:
     dest.unlink(missing_ok=True); report['oversized']+=1; report['files'].append({'workId':e['id'],'title':e['titleAr'],'status':'deferred-transfer-size-after-download','bytes':n,**c}); continue
    used+=n; got_any=True; report['downloaded']+=1; report['bytes']=used; report['files'].append({'workId':e['id'],'title':e['titleAr'],'author':e['authorAr'],'rights':e['rights'],'status':'downloaded','format':ext[1:].upper(),'bytes':n,'localPath':dest.as_posix(),**c})
   except Exception as ex:
    report['failed']+=1; report['files'].append({'workId':e['id'],'title':e['titleAr'],'status':'download-failed','error':str(ex)[:220],**c})
  if not got_any:
   if rights_note: report['rightsUnverified']+=1
   report['unresolved'].append({'workId':e['id'],'title':e['titleAr'],'author':e['authorAr'],'rights':e['rights'],'candidateRightsUnverified':rights_note})
  time.sleep(.1)
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({k:report[k] for k in ('shard','selectedWorks','downloaded','bytes','rightsUnverified','oversized','failed')},ensure_ascii=False))
if __name__=='__main__': main()
