#!/usr/bin/env python3
from __future__ import annotations
import json, re, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'data'/'ocr'; OUT.mkdir(parents=True,exist_ok=True)
INDEXES=[ROOT/'data'/'ingested_library.json',ROOT/'data'/'published_user_books.json']

def safe(s):return re.sub(r'[^A-Za-z0-9_.-]+','_',str(s))[:160]
def local_pdf(x):
 for k in ('localUrl','readerUrl','downloadUrl','pdfUrl','sourceUrl'):
  v=x.get(k)
  if isinstance(v,str) and v.lower().split('?')[0].endswith('.pdf') and (v.startswith('/') or not v.startswith('http')):
   p=ROOT/v.lstrip('/')
   if p.exists():return p
 return None

def items():
 out={}
 for p in INDEXES:
  if not p.exists():continue
  try:j=json.loads(p.read_text(encoding='utf-8'))
  except:continue
  for x in j.get('items',[]):
   i=str(x.get('id') or x.get('workId') or '')
   if i:out[i]={**out.get(i,{}),**x}
 return out.values()

def extract(mid,pdf):
 try:import fitz
 except ImportError:raise RuntimeError('PyMuPDF is required: pip install pymupdf')
 doc=fitz.open(pdf);pages=[];total=0
 for n,page in enumerate(doc):
  pw,ph=float(page.rect.width or 1),float(page.rect.height or 1);blocks=[]
  for b in page.get_text('words'):
   x0,y0,x1,y1,text,*rest=b;text=str(text).strip()
   if not text:continue
   blocks.append({'text':text,'x':round(x0/pw*100,4),'y':round(y0/ph*100,4),'w':round((x1-x0)/pw*100,4),'h':round((y1-y0)/ph*100,4)});total+=1
  pages.append({'page':n+1,'width':round(pw,2),'height':round(ph,2),'coordinateUnit':'percent','words':blocks})
 out={'id':mid,'source':str(pdf.relative_to(ROOT)),'generatedAt':int(time.time()),'method':'embedded-pdf-text-coordinates','coordinateUnit':'percent','pages':pages,'wordBoxes':total,'ocrRequired':total==0};(OUT/(safe(mid)+'.json')).write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8');return total

def main():
 report={'processed':0,'generated':0,'needsOCR':[],'missingLocalPdf':[],'failed':[]}
 for x in items():
  mid=str(x.get('id') or x.get('workId'));pdf=local_pdf(x)
  if not pdf:report['missingLocalPdf'].append(mid);continue
  report['processed']+=1
  try:
   n=extract(mid,pdf)
   if n:report['generated']+=1
   else:report['needsOCR'].append(mid)
  except Exception as e:report['failed'].append({'id':mid,'error':str(e)})
 (OUT/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
