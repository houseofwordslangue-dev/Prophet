#!/usr/bin/env python3
from __future__ import annotations
import io, json, re, time
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

def scan_words(page):
 try:
  import pytesseract
  from PIL import Image
  pix=page.get_pixmap(matrix=__import__('fitz').Matrix(2,2),alpha=False);img=Image.open(io.BytesIO(pix.tobytes('png')));d=pytesseract.image_to_data(img,lang='ara+eng+fra',output_type=pytesseract.Output.DICT)
  out=[];iw,ih=img.size
  for i,t in enumerate(d.get('text',[])):
   t=str(t).strip()
   if not t:continue
   x,y,w,h=d['left'][i],d['top'][i],d['width'][i],d['height'][i];out.append({'text':t,'x':round(x/iw*100,4),'y':round(y/ih*100,4),'w':round(w/iw*100,4),'h':round(h/ih*100,4),'ocr':True})
  return out
 except Exception:return []

def extract(mid,pdf):
 try:import fitz
 except ImportError:raise RuntimeError('PyMuPDF is required: pip install pymupdf')
 doc=fitz.open(pdf);pages=[];total=0;ocr_pages=0
 for n,page in enumerate(doc):
  pw,ph=float(page.rect.width or 1),float(page.rect.height or 1);blocks=[]
  for b in page.get_text('words'):
   x0,y0,x1,y1,text,*rest=b;text=str(text).strip()
   if not text:continue
   blocks.append({'text':text,'x':round(x0/pw*100,4),'y':round(y0/ph*100,4),'w':round((x1-x0)/pw*100,4),'h':round((y1-y0)/ph*100,4),'ocr':False})
  if not blocks:
   blocks=scan_words(page)
   if blocks:ocr_pages+=1
  total+=len(blocks);pages.append({'page':n+1,'width':round(pw,2),'height':round(ph,2),'coordinateUnit':'percent','words':blocks})
 out={'id':mid,'source':str(pdf.relative_to(ROOT)),'generatedAt':int(time.time()),'method':'pdf-text-plus-tesseract-fallback','coordinateUnit':'percent','pages':pages,'wordBoxes':total,'ocrPages':ocr_pages,'ocrRequired':total==0};(OUT/(safe(mid)+'.json')).write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')),encoding='utf-8');return total,ocr_pages

def main():
 report={'processed':0,'generated':0,'ocrPages':0,'needsOCR':[],'missingLocalPdf':[],'failed':[],'dependencies':'PyMuPDF; optional pytesseract+Tesseract ara/eng/fra for image-only pages'}
 for x in items():
  mid=str(x.get('id') or x.get('workId'));pdf=local_pdf(x)
  if not pdf:report['missingLocalPdf'].append(mid);continue
  report['processed']+=1
  try:
   n,op=extract(mid,pdf);report['ocrPages']+=op
   if n:report['generated']+=1
   else:report['needsOCR'].append(mid)
  except Exception as e:report['failed'].append({'id':mid,'error':str(e)})
 (OUT/'status.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
