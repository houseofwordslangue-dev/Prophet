#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
"""Promote rights-cleared exact catalogue sources into the acquisition queue.

MASTER RULE: native digital text is always searched and preferred before OCR.
Priority: EPUB -> TXT -> DOCX/DOC -> ODT/RTF -> HTML/MD/XML -> text PDF -> PDF.
"""
from __future__ import annotations
from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import argparse,base64,gzip,json

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'data'/'catalogue'/'manifest.json';QUEUE=ROOT/'private'/'acquisition_candidates.json'
UA='ProphetBiographyLibrary/7.1 catalogue-promoter-source-first';MAX_BYTES=400*1024*1024
PRIORITY={'epub':0,'txt':1,'docx':2,'doc':3,'odt':4,'rtf':5,'html':6,'htm':6,'md':7,'xml':8,'textpdf':9,'pdf':10}
LEGACY_SCHEMA=['id','entryNumber','category','titleAr','title','authorAr','author','kind','rightsStatus','verificationStatus','availabilityStatus','modesCsv','verifiedSource','editionNoteAr','ingestionStatus','century','language','publicationYear']

def read_json(path,default):
 try:return json.loads(path.read_text(encoding='utf-8'))
 except Exception:return default

def truthy(v):return isinstance(v,bool) and v or str(v or '').strip().lower() in {'1','true','yes','y','eligible','allowed'}
def explicit_public_domain(row):
 if 'eligibleForFullTextCopy' in row and not truthy(row.get('eligibleForFullTextCopy')):return False
 text=' '.join(str(row.get(k) or '') for k in ('rightsStatus','publicNotes','editionNoteAr','blockerAr')).lower()
 return any(t in text for t in ('public domain','public-domain','public_domain','cc0','unrestricted','الملك العام'))
def archive_identifier(url):
 p=urlparse(url)
 if p.hostname not in {'archive.org','www.archive.org'}:return ''
 parts=[x for x in p.path.split('/') if x]
 return parts[1] if len(parts)>=2 and parts[0] in {'details','download'} else ''
def get_json(url,timeout=45):
 with urlopen(Request(url,headers={'User-Agent':UA}),timeout=timeout) as r:return json.load(r)
def file_kind(name):
 low=name.lower()
 for ext in ('epub','txt','docx','doc','odt','rtf','html','htm','md','xml'):
  if low.endswith('.'+ext):return ext
 if low.endswith('_text.pdf') or 'searchable' in low and low.endswith('.pdf'):return 'textpdf'
 if low.endswith('.pdf'):return 'pdf'
 return ''
def choose_archive_file(identifier):
 meta=get_json(f'https://archive.org/metadata/{quote(identifier)}');files=meta.get('files',[]) if isinstance(meta,dict) else [];c=[]
 for f in files:
  name=str(f.get('name') or '');kind=file_kind(name)
  if not kind:continue
  try:size=int(f.get('size') or 0)
  except Exception:size=0
  if size and (size<1024 or size>MAX_BYTES):continue
  c.append((PRIORITY[kind],size or MAX_BYTES,name,kind))
 if not c:return None
 _,_,name,kind=sorted(c)[0];fmt='pdf' if kind=='textpdf' else kind
 return {'format':fmt,'downloadUrl':f'https://archive.org/download/{quote(identifier)}/{quote(name)}','sourceIdentifier':identifier,'nativeSearchCompleted':True,'selectedByPriority':kind}
def gutenberg_download(url):
 p=urlparse(url)
 if p.hostname not in {'gutenberg.org','www.gutenberg.org'}:return None
 parts=[x for x in p.path.split('/') if x]
 try:i=parts.index('ebooks');eid=parts[i+1]
 except Exception:return None
 if not eid.isdigit():return None
 return {'format':'epub','downloadUrl':f'https://www.gutenberg.org/ebooks/{eid}.epub3.images','fallbackDownloadUrl':f'https://www.gutenberg.org/cache/epub/{eid}/pg{eid}.txt','sourceIdentifier':eid,'nativeSearchCompleted':True,'selectedByPriority':'epub'}
def professional_records(manifest):
 payload_path=manifest.get('compressedPayload')
 if not payload_path:return None
 raw=base64.b64decode((ROOT/str(payload_path)).read_text(encoding='utf-8').strip());payload=json.loads(gzip.decompress(raw).decode('utf-8'));schema=payload.get('schema',[])
 return [{k:(r[i] if i<len(r) else '') for i,k in enumerate(schema)} for r in payload.get('items',[])]
def iter_catalogue():
 m=read_json(MANIFEST,{})
 try:records=professional_records(m)
 except Exception:records=None
 if records is not None:yield from records;return
 for chunk in m.get('chunks') or m.get('fallbackChunks') or []:
  doc=read_json(ROOT/str(chunk.get('path') or ''),{})
  for raw in doc.get('items',[]):
   yield {k:(raw[i] if i<len(raw) else '') for i,k in enumerate(LEGACY_SCHEMA)} if isinstance(raw,list) else raw
def source_for(row):
 exact=str(row.get('exactSourceUrl') or row.get('verifiedSource') or '').strip();aid=str(row.get('archiveIdentifier') or '').strip()
 if exact:return exact,archive_identifier(exact) or aid
 if aid:return f'https://archive.org/details/{aid}',aid
 return '',''
def promote(limit):
 queue=read_json(QUEUE,{'schema':'strict-unrestricted-candidates-v1','rotationEnabled':True,'items':[]});items=queue.setdefault('items',[]);seen_work={str(x.get('workId') or '') for x in items};seen_source={(str(x.get('sourceRepository') or ''),str(x.get('sourceIdentifier') or '')) for x in items};scanned=eligible=added=0;errors=[]
 for row in iter_catalogue():
  scanned+=1
  if not explicit_public_domain(row):continue
  source,aid=source_for(row)
  if not source:continue
  eligible+=1;resolved=None;repo=''
  try:
   if aid:resolved=choose_archive_file(aid);repo='Internet Archive'
   else:resolved=gutenberg_download(source);repo='Project Gutenberg' if resolved else ''
  except Exception as exc:errors.append({'id':row.get('id'),'source':source,'error':type(exc).__name__});continue
  if not resolved:continue
  work_id=str(row.get('id') or resolved['sourceIdentifier']);key=(repo,str(resolved['sourceIdentifier']))
  if work_id in seen_work or key in seen_source:continue
  title_ar=str(row.get('titleAr') or '');title=str(row.get('originalTitle') or row.get('title') or title_ar or work_id);author=str(row.get('authorAr') or row.get('authorRomanized') or row.get('author') or '');language=str(row.get('language') or ('ar' if title_ar else 'en'))
  item={'workId':work_id,'catalogueId':work_id,'titleOriginal':title,'titleAr':title_ar,'author':author,'language':language,'format':resolved['format'],'sourceRepository':repo,'sourceIdentifier':resolved['sourceIdentifier'],'sourceUrl':source,'downloadUrl':resolved['downloadUrl'],'fallbackDownloadUrl':resolved.get('fallbackDownloadUrl'),'rightsEvidence':'Public domain — professional catalogue marks full-text copy eligible','rightsEvidenceUrl':source,'subjects':[str(row.get('categoryAr') or row.get('category') or 'المصادر')],'siteSections':['المصادر والدراسات'],'nativeSearchCompleted':True,'selectedByPriority':resolved.get('selectedByPriority')}
  items.append(item);seen_work.add(work_id);seen_source.add(key);added+=1
  if added>=limit:break
 if added:QUEUE.parent.mkdir(parents=True,exist_ok=True);QUEUE.write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'scanned':scanned,'eligible':eligible,'added':added,'queueTotal':len(items),'errors':errors[:20],'priority':list(PRIORITY)},ensure_ascii=False));return 0
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int,default=25);a=ap.parse_args();return promote(max(0,a.limit))
if __name__=='__main__':raise SystemExit(main())
