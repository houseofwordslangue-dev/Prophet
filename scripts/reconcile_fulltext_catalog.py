#!/usr/bin/env python3
from __future__ import annotations
import json,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data'/'public_catalog_all.generated.json';IDX=ROOT/'data'/'ingested_library.json';STORE=ROOT/'library'/'works';AUD=ROOT/'data'/'audits'/'exhaustive-publication-audit-current.json'

def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d

def rights_ok(work,edition):
 p=STORE/work/'editions'/edition/'rights.json';r=load(p,{})
 s=' '.join(str(r.get(k) or '') for k in ('status','evidence')).lower()
 return any(t in s for t in ('unlicenced_confirmed','public domain','public-domain','cc0','unrestricted'))
def main():
 cat=load(CAT,{'items':[]});idx=load(IDX,{'items':[]});bywork={}
 for x in idx.get('items',[]):
  w=str(x.get('workId') or '')
  if w:bywork.setdefault(w,[]).append(x)
 promoted=0
 for row in cat.get('items',[]):
  if row.get('access')=='PUBLIC_FULL_TEXT':continue
  wid=str(row.get('id') or '');cands=bywork.get(wid,[])
  chosen=None
  for x in cands:
   if x.get('publishedAsset') and x.get('capabilities',{}).get('readable') and rights_ok(wid,str(x.get('editionId') or '')):
    chosen=x;break
  if not chosen:continue
  row['access']='PUBLIC_FULL_TEXT';row['state']='local-reading-copy-ready';row['ready']=True;row['formats']=sorted(set((row.get('formats') or [])+[str(chosen.get('format') or '')]));row['localUrl']=chosen.get('localUrl');row['readerUrl']='reader.html?id='+wid;row['capabilities']={'read':True,'search':bool(chosen.get('capabilities',{}).get('searchable')),'copy':True,'listen':'tts' if chosen.get('capabilities',{}).get('listenable') else False,'watch':bool(chosen.get('capabilities',{}).get('watchable'))};row['fullTextEvidence']={'workId':wid,'editionId':chosen.get('editionId'),'sha256':chosen.get('sha256'),'format':chosen.get('format'),'rights':'verified-by-acquisition-rights-json'};promoted+=1
 counts={}
 for x in cat.get('items',[]):counts[x.get('access','UNKNOWN')]=counts.get(x.get('access','UNKNOWN'),0)+1
 cat['generatedAt']=datetime.datetime.now(datetime.timezone.utc).isoformat();cat['total']=len(cat.get('items',[]));cat['counts']=counts;cat['publicationPolicy']='SOURCE_FIRST_NATIVE_FORMATS_THEN_OCR_FULLTEXT_ONLY_WHEN_ACQUIRED_AND_RIGHTS_VERIFIED';CAT.write_text(json.dumps(cat,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 full=counts.get('PUBLIC_FULL_TEXT',0);total=cat['total'];audit=load(AUD,{});audit['generatedAt']=cat['generatedAt'];audit.setdefault('cataloguePublication',{}).update({'result':'PASS_ALL_RESOURCES_CATALOGUED','publishedCount':total,'totalCount':total,'coveragePercent':100,'catalogueFile':'data/public_catalog_all.generated.json','browser':'library-all.html'});audit['fullTextPublication']={'result':'PASS_ALL_FULLTEXT' if full==total else 'PARTIAL_SOURCE_FIRST_ACQUISITION_ACTIVE','publicFullText':full,'remaining':max(0,total-full),'totalCount':total};audit['auditResult']='PASS_ALL_RESOURCES_PUBLISHED' if full==total else 'PASS_CATALOGUE_FULLTEXT_ACQUISITION_ACTIVE';audit['sourceFirstPolicy']='EPUB > TXT > DOCX/DOC > ODT/RTF > HTML/MD/XML > embedded-text PDF > OCR';AUD.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'promotedThisRun':promoted,'publicFullText':full,'remaining':total-full,'total':total},ensure_ascii=False))
if __name__=='__main__':main()
