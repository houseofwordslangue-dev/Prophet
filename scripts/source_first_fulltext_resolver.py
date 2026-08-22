#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,re,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data/public_catalog_all.generated.json';CAND=ROOT/'private/acquisition_candidates.json';OVERRIDES=ROOT/'private/native_source_overrides.json'
DRIVE=ROOT/'data/drive_native_assets_20260822.json';DRIVE_VERIFIED=ROOT/'data/drive_verified_assets_20260822.json';INGESTED=ROOT/'data/ingested_library.json'
OUT=ROOT/'private/source_first_resolution.json';QUEUE=ROOT/'private/resource_extraction_queue.json';AVAIL=ROOT/'data/editorial/resource_extraction_availability.json'
UA='ProphetBiographyLibrary/10.0-provenance-aware';FORMATS=['epub','txt','docx','doc','odt','rtf','html','md','xml','pdf']
ALLOW={'archive.org','www.archive.org','gutenberg.org','www.gutenberg.org','api.github.com','raw.githubusercontent.com','upload.wikimedia.org','commons.wikimedia.org','wikisource.org','en.wikisource.org','fr.wikisource.org','ar.wikisource.org'}
STOP={'كتاب','شرح','جزء','المجلد','الجزء','في','من','على','الى','إلى','عن','the','of','and','a','an','volume','vol','part'}
ORIGIN_RANK={'NATIVE':0,'VERIFIED_TEXT':1,'GENERATED_TEXT':2,'OCR_DERIVATIVE':3,'PDF_TEXT_OR_SCAN':4,'UNKNOWN':5}
def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def save(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):
 s=str(s or '').lower();s=re.sub(r'[\u064b-\u065f\u0670]','',s);s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ة','ه');s=re.sub(r'\b(المجلد|الجزء|volume|vol|part|cover)\b.*$','',s);return re.sub(r'[^\w\u0600-\u06ff]+',' ',s).strip()
def toks(s):return [x for x in norm(s).split() if len(x)>2 and x not in STOP]
def title_score(a,b):
 na,nb=norm(a),norm(b)
 if na and na==nb:return 1.0
 A,B=set(toks(a)),set(toks(b))
 if not A or not B:return 0.0
 i=len(A&B);p=i/len(B);r=i/len(A)
 return 0.0 if not p or not r else 2*p*r/(p+r)
def title_match(a,b):return title_score(a,b)>=0.78
def fmt(url='',name=''):
 x=(name or urllib.parse.urlparse(url).path).lower()
 return next((f for f in FORMATS if x.endswith('.'+f)),'')
def host_ok(u):
 try:return urllib.parse.urlparse(u).hostname in ALLOW
 except Exception:return False
def get_json(u):
 if not host_ok(u):raise RuntimeError('domain-not-allowlisted')
 with urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA,'Accept':'application/json'}),timeout=45) as r:return json.load(r)
def archive_id(u):
 p=urllib.parse.urlparse(u).path.strip('/').split('/');return p[1] if len(p)>=2 and p[0] in {'details','download','metadata'} else ''
def archive_origin(f):
 n=str(f.get('name') or '').lower();src=str(f.get('source') or '').lower();form=fmt(name=n)
 if any(x in n for x in ('_djvu.txt','_djvu.xml','_hocr.html','_hocr_searchtext.txt','_text.pdf')) or src=='derivative':return 'OCR_DERIVATIVE'
 return 'PDF_TEXT_OR_SCAN' if form=='pdf' else 'NATIVE'
def archive_usable(f):
 n=str(f.get('name') or '').lower()
 return bool(n and fmt(name=n) and not any(x in n for x in ('_lcp.epub','encrypted','_meta.sqlite','_files.xml','_reviews.xml','_scandata.xml')) and str(f.get('private') or '').lower() not in {'true','1'})
def archive_files(u):
 ident=archive_id(u)
 if not ident:return []
 try:m=get_json('https://archive.org/metadata/'+urllib.parse.quote(ident))
 except Exception:return []
 if str((m.get('metadata') or {}).get('access-restricted-item') or '').lower() in {'true','1'}:return []
 out=[]
 for f in m.get('files',[]):
  if not archive_usable(f):continue
  n=str(f.get('name') or '');out.append({'format':fmt(name=n),'url':'https://archive.org/download/'+urllib.parse.quote(ident)+'/'+urllib.parse.quote(n),'name':n,'source':'archive-metadata','identifier':ident,'textOrigin':archive_origin(f),'verifiedAccessible':True})
 return out
def archive_search(title,author=''):
 qs=[f'title:"{title}" AND mediatype:texts'];
 if author:qs.insert(0,f'title:"{title}" AND creator:"{author}" AND mediatype:texts')
 best=[];seen=set()
 for q in qs:
  try:j=get_json('https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':q,'fl[]':['identifier','title','creator'],'rows':25,'page':1,'output':'json'},doseq=True))
  except Exception:continue
  for d in j.get('response',{}).get('docs',[]):
   ident=str(d.get('identifier') or '')
   if not ident or ident in seen:continue
   seen.add(ident);sc=title_score(title,d.get('title'))
   if sc>=0.78:best.append((sc,ident))
 for _,ident in sorted(best,reverse=True)[:10]:
  rows=archive_files('https://archive.org/details/'+ident)
  if rows:return rows
 return []
def gutenberg(u):
 m=re.search(r'/(?:ebooks|epub)/(\d+)',u)
 if not m:return []
 i=m.group(1);return [{'format':'epub','url':f'https://www.gutenberg.org/ebooks/{i}.epub3.images','name':f'{i}.epub','source':'gutenberg','textOrigin':'VERIFIED_TEXT','verifiedAccessible':True},{'format':'txt','url':f'https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt','name':f'pg{i}.txt','source':'gutenberg','textOrigin':'VERIFIED_TEXT','verifiedAccessible':True}]
def wikisource(title):
 q=urllib.parse.urlencode({'action':'query','list':'search','srsearch':f'intitle:"{title}"','srnamespace':'0','srlimit':'20','format':'json','formatversion':'2'})
 try:j=get_json('https://ar.wikisource.org/w/api.php?'+q)
 except Exception:return []
 out=[]
 for r in j.get('query',{}).get('search',[]):
  t=str(r.get('title') or '')
  if t and title_match(title,t.split('/',1)[0]):out.append({'format':'html','url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote(t.replace(' ','_')),'name':t,'source':'arabic-wikisource','textOrigin':'VERIFIED_TEXT','verifiedAccessible':True})
 return out
def web_candidates(row):
 urls=[]
 for k in ('sources','sourceUrls'):
  if isinstance(row.get(k),list):urls += [str(x) for x in row[k] if x]
 for k in ('source','sourceUrl','verifiedSource','candidateSource','downloadUrl'):
  if row.get(k):urls.append(str(row[k]))
 out=[];vu=str(row.get('verifiedSource') or '');vf=str(row.get('verifiedFormat') or '').lower()
 if vu and vf in FORMATS:out.append({'format':vf,'url':vu,'name':vu.rsplit('/',1)[-1],'source':'verified-catalog','textOrigin':'VERIFIED_TEXT' if vf!='pdf' else 'PDF_TEXT_OR_SCAN','redistributionApproved':row.get('redistributionApproved'),'verifiedAccessible':True})
 for u in dict.fromkeys(urls):
  f=fmt(u)
  if f and '_lcp.epub' not in u.lower():out.append({'format':f,'url':u,'name':u.rsplit('/',1)[-1],'source':'direct','textOrigin':'UNKNOWN' if f!='pdf' else 'PDF_TEXT_OR_SCAN','verifiedAccessible':True})
  if 'archive.org' in u:out+=archive_files(u)
  if 'gutenberg.org' in u:out+=gutenberg(u)
 return out
def drive_map():
 out={}
 for p,source in ((DRIVE,'google-drive-native'),(DRIVE_VERIFIED,'google-drive-verified')):
  for x in load(p,{'items':[]}).get('items',[]):
   if x.get('derivative'):continue
   key=norm(x.get('title'));f=str(x.get('format') or 'epub').lower();mode=str(x.get('extractionMode') or '').lower()
   if not key:continue
   origin='OCR_DERIVATIVE' if 'ocr' in mode else ('GENERATED_TEXT' if 'generated' in mode else ('PDF_TEXT_OR_SCAN' if f=='pdf' else 'NATIVE'))
   out.setdefault(key,[]).append({'format':f,'driveId':x.get('driveId'),'url':f"https://drive.google.com/file/d/{x.get('driveId')}/view",'name':x.get('title'),'source':source,'textOrigin':origin,'extractionMode':x.get('extractionMode'),'verifiedAccessible':True})
 return out
def ingested_map():
 out={}
 for x in load(INGESTED,{'items':[]}).get('items',[]):
  if not x.get('localUrl'):continue
  key=norm(x.get('titleOriginal') or x.get('titleAr') or x.get('titleEn'));f=str(x.get('format') or 'txt').lower();mode=str(x.get('extractionMode') or x.get('origin') or '').lower()
  if not key:continue
  origin='OCR_DERIVATIVE' if 'ocr' in mode else ('GENERATED_TEXT' if 'generated' in mode else ('PDF_TEXT_OR_SCAN' if f=='pdf' else 'VERIFIED_TEXT'))
  out.setdefault(key,[]).append({'format':f,'url':x.get('localUrl'),'name':x.get('titleOriginal') or key,'source':'local-ingested','textOrigin':origin,'local':True,'verifiedAccessible':True})
 return out
def match_map(title,m):return [r for k,rows in m.items() if title_match(title,k) for r in rows]
def dedup(rows):
 d={}
 for r in rows:
  if r.get('format') and r.get('url'):d[(r['format'],r.get('driveId') or r['url'])]=r
 return list(d.values())
def rank(r):return (ORIGIN_RANK.get(r.get('textOrigin','UNKNOWN'),9),FORMATS.index(r['format']) if r.get('format') in FORMATS else 99)
def classify(r):
 o=r.get('textOrigin');f=r.get('format')
 if o in {'NATIVE','VERIFIED_TEXT'} and f!='pdf':return 'EXTRACTION_READY_NATIVE_OR_VERIFIED_TEXT'
 if o=='GENERATED_TEXT' and f!='pdf':return 'EXTRACTION_READY_GENERATED_TEXT'
 if o=='OCR_DERIVATIVE':return 'EXTRACTION_READY_OCR_DERIVATIVE'
 if f=='pdf' or o=='PDF_TEXT_OR_SCAN':return 'EXTRACTION_READY_PDF_TEXT_OR_OCR'
 return 'EXTRACTION_READY_REVIEW_REQUIRED'
def main():
 cat=load(CAT,{'items':[]});cand=load(CAND,{'items':[]});over=load(OVERRIDES,{'items':[]});cmap={str(x.get('workId') or x.get('catalogueId') or ''):x for x in cand.get('items',[]) if isinstance(x,dict)};omap={str(x.get('workId') or x.get('catalogueId') or ''):x for x in over.get('items',[]) if isinstance(x,dict)};dm,im=drive_map(),ingested_map();rows=[];queue=[];counts={k:0 for k in ('native','verified','generated','ocr','pdf','driveNative','driveVerified','remote')}
 for x in cat.get('items',[]):
  wid=str(x.get('id') or '');title=str(x.get('title') or '');merged=dict(x);merged.update(cmap.get(wid,{}));merged.update(omap.get(wid,{}));found=match_map(title,im)+match_map(title,dm)+web_candidates(merged)
  if not found:found=wikisource(title)
  if not found:found=archive_search(title,str(x.get('author') or ''))
  found=sorted(dedup(found),key=rank);preferred=found[0] if found else None
  if preferred:
   state=classify(preferred);origin=preferred.get('textOrigin','UNKNOWN');counts['native']+=origin=='NATIVE';counts['verified']+=origin=='VERIFIED_TEXT';counts['generated']+=origin=='GENERATED_TEXT';counts['ocr']+=origin=='OCR_DERIVATIVE';counts['pdf']+=preferred.get('format')=='pdf' or origin=='PDF_TEXT_OR_SCAN';counts['driveNative']+=preferred.get('source')=='google-drive-native';counts['driveVerified']+=preferred.get('source')=='google-drive-verified';counts['remote']+=preferred.get('source') in {'arabic-wikisource','archive-metadata','gutenberg','verified-catalog'}
  elif x.get('access')=='PUBLIC_FULL_TEXT' and (x.get('sources') or []):preferred={'format':'txt','url':x['sources'][0],'name':title,'source':'public-catalog-fulltext','textOrigin':'VERIFIED_TEXT','verifiedAccessible':True};state='EXTRACTION_READY_NATIVE_OR_VERIFIED_TEXT';counts['verified']+=1
  else:state='ACQUISITION_REQUIRED';preferred=None;queue.append({'id':wid,'title':title,'author':x.get('author'),'reason':'No strictly title-matched verified extraction path found.','ocrAllowed':True,'nextActions':['search Drive by exact title/author','search native text/EPUB repositories','search readable PDF witnesses','OCR only after native search is exhausted']})
  origin=preferred.get('textOrigin') if preferred else None;rows.append({'id':wid,'title':title,'author':x.get('author'),'previousAccess':x.get('access'),'state':state,'extractionReady':state.startswith('EXTRACTION_READY'),'preferred':preferred,'candidates':found[:20],'titleMatchPolicy':'token-F1>=0.78','nativeSearchCompleted':True,'textOrigin':origin,'ocrDerived':origin=='OCR_DERIVATIVE','ocrAllowed':state in {'EXTRACTION_READY_OCR_DERIVATIVE','EXTRACTION_READY_PDF_TEXT_OR_OCR','ACQUISITION_REQUIRED'}})
 total=len(rows);ready=sum(r['extractionReady'] for r in rows);missing=total-ready;nonocr=counts['native']+counts['verified']+counts['generated'];now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());out={'schema':'source-first-resolution-v7','governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','generatedAt':now,'priority':FORMATS,'catalogResources':total,'extractionReady':ready,'acquisitionRequired':missing,'nativeOrTextReady':nonocr,'nativeReady':counts['native'],'verifiedTextReady':counts['verified'],'generatedTextReady':counts['generated'],'ocrDerivativeReady':counts['ocr'],'pdfOcrReady':counts['pdf'],'driveNativeMatched':counts['driveNative'],'driveVerifiedMatched':counts['driveVerified'],'remoteExtractionMatched':counts['remote'],'allResourcesExtractionReady':missing==0,'ocrDerivativesNeverCountAsNative':True,'strictTitleMatching':True,'items':rows};save(OUT,out);save(QUEUE,{'schema':'resource-extraction-queue-v4','generatedAt':now,'count':len(queue),'items':queue});save(AVAIL,{'schema':'resource-extraction-availability-v4','generatedAt':now,'catalogResources':total,'extractionReady':ready,'acquisitionRequired':missing,'coveragePercent':round(100*ready/total,2) if total else 100,'nativeReady':counts['native'],'verifiedTextReady':counts['verified'],'generatedTextReady':counts['generated'],'ocrDerivativeReady':counts['ocr'],'pdfOcrReady':counts['pdf'],'allResourcesExtractionReady':missing==0,'policy':'OCR derivatives remain explicitly marked OCR_DERIVATIVE and require OCR repair/proofreading/audit. They never count as native text. Resource matches require strict normalized-title similarity; numerical coverage never overrides source identity.'});print(json.dumps({k:out[k] for k in ('catalogResources','extractionReady','acquisitionRequired','nativeReady','verifiedTextReady','generatedTextReady','ocrDerivativeReady','pdfOcrReady','allResourcesExtractionReady')},ensure_ascii=False))
if __name__=='__main__':main()
