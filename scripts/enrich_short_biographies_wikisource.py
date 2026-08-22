#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'data'/'editorial';A=E/'short_biographies_500_audit.json';I=E/'short_biography_extensions.json';O=E/'short-biography-extensions';TARGET=500;REQUESTED=50
ITEM='fp94563_202505';BASE=f'https://archive.org/download/{ITEM}/';FILES=['01_94563_djvu.txt','02_94564_djvu.txt','03_94565_djvu.txt','04_94566_djvu.txt']
# Canonical IDs with deliberately specific aliases. Generic ancestors use fuller genealogical forms to avoid incidental matches.
TARGETS=[
('abu-bakr',['أبو بكر الصديق','أبو بكر']),('khalid-ibn-al-walid',['خالد بن الوليد']),('muadh-ibn-jabal',['معاذ بن جبل']),('person-0cc8963df4cd',['عثمان بن عفان']),('person-0632526f4f61',['جعفر بن أبي طالب']),('person-051301ccb5bf',['الحسين بن علي']),('person-04c5aa88d621',['أم حبيبة']),('person-0f1c7cf0bc88',['ميمونة بنت الحارث']),('person-1a613275126e',['عروة بن الزبير']),('person-14301a19d094',['فهر بن مالك']),('person-177f75bd083c',['كنانة بن خزيمة']),('person-1a26b914289b',['مرة بن كعب']),('person-2204d32f7044',['أبو العاص بن الربيع']),('person-224da2bd3aec',['لؤي بن غالب']),('person-248fde5641d4',['صفية بنت عبد المطلب']),('person-27040d99eb01',['سودة بنت زمعة']),('person-3afd4bc4b4e8',['أبو سفيان بن الحارث']),('person-3b1c8fb6a9a5',['أبو سلمة عبد الله','أبو سلمة']),('person-59487b80ae9d',['الزبير بن العوام']),('person-62fc96ff1e57',['كلاب بن مرة']),('person-69bc01fbc242',['حفصة بنت عمر','حفصة']),('person-6f9bc4267d74',['أم سلمة']),('person-77982ed9d8d5',['عائشة بنت أبي بكر','عائشة']),('person-8365c67f7e7c',['عبد المطلب بن هاشم','عبد المطلب']),('person-872432cece41',['عبد الله بن الزبير']),('person-950261ac6f78',['أبو طالب بن عبد المطلب','أبو طالب']),('person-95aa67be1d14',['عقيل بن أبي طالب']),('person-99149c5c072c',['هاشم بن عبد مناف']),('person-d3f51877a09f',['العباس بن عبد المطلب']),('person-da8e2ffd90a2',['جويرية بنت الحارث']),('person-e59d18e68796',['عبد الله بن عباس']),('person-e60283d67ffd',['زينب بنت جحش']),('person-f54b80d2d221',['حمزة بن عبد المطلب']),('person-f8216ef01954',['سعد بن أبي وقاص']),('person-f95ed2a0a66a',['خديجة بنت خويلد','خديجة']),('person-facd06c50592',['عبد مناف بن قصي']),('salman-al-farisi',['سلمان الفارسي']),('saeed-ibn-zayd',['سعيد بن زيد']),('person-b758f13b7aca',['آمنة بنت وهب']),('person-bd9f4f9ec113',['قصي بن كلاب']),('person-e757d74ff462',['نزار بن معد']),('person-e8a4a2468176',['كعب بن لؤي']),('person-74cc7918c881',['معد بن عدنان']),('person-7752e2dfa848',['مدركة بن إلياس']),('person-7060e68d653d',['خزيمة بن مدركة']),('person-117ca7ce1c07',['إلياس بن مضر']),('person-040170814f57',['مضر بن نزار']),('person-763766a4c305',['عاتكة بنت عبد المطلب']),('person-dd9b45c017ac',['أم كلثوم بنت رسول الله','أم كلثوم']),('person-ee9533da8a95',['رقية بنت رسول الله','رقية'])]
AR=re.compile(r'[\u0600-\u06ff]');DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]')
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,d=None):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def collapse(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def key(s):
 s=DIAC.sub('',collapse(s)).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي')
 return re.sub(r'[^\u0600-\u06ff\s]',' ',s)
def wc(s):return len(collapse(s).split())
def fp(s):return hashlib.sha256(key(s).encode()).hexdigest()
def readable(s):
 t=collapse(s).split();letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s));lens=[len(DIAC.sub('',x)) for x in t]
 return len(t)>=45 and len(AR.findall(s))/max(1,letters)>.82 and max(lens,default=0)<38 and sum(x>20 for x in lens)/max(1,len(lens))<.025
def fetch_volumes():
 vols=[]
 for fn in FILES:
  req=urllib.request.Request(BASE+fn,headers={'User-Agent':'ProphetBiographyResearchBot/1.1'})
  with urllib.request.urlopen(req,timeout=90) as r:raw=r.read().decode('utf-8','ignore')
  # Keep raw word sequence; matching is performed on a normalized parallel token stream.
  words=collapse(raw).split(); normwords=[key(w).strip() for w in words]
  vols.append((fn,words,normwords))
 return vols
def alias_tokens(alias):return [x for x in key(alias).split() if x]
def occurrences(normwords,needle):
 n=len(needle)
 if not n:return
 first=needle[0]
 for i,w in enumerate(normwords):
  if w!=first:continue
  # OCR punctuation disappears in normalized tokens; require consecutive normalized lexical tokens.
  if normwords[i:i+n]==needle:yield i
def windows_for(vols,alias):
 needle=alias_tokens(alias);out=[];used=[]
 for fn,words,normwords in vols:
  for i in occurrences(normwords,needle):
   # Avoid highly overlapping repeats; each source window contributes distinct surrounding material.
   if any(f==fn and abs(i-j)<180 for f,j in used):continue
   a=max(0,i-145);b=min(len(words),i+len(needle)+165);txt=' '.join(words[a:b])
   if not readable(txt):continue
   # Verify normalized alias survives inside the accepted raw excerpt.
   if ' '.join(needle) not in key(txt):continue
   used.append((fn,i));out.append((fn,i,txt))
 return out
def main():
 audit=read(A,{}) or {};idx=read(I,{}) or {};idx.setdefault('people',{});res={str(x.get('id')):x for x in audit.get('residualUnder500',[]) if isinstance(x,dict)};O.mkdir(parents=True,exist_ok=True);vols=fetch_volumes()
 prior=list(audit.get('latestBatchPeople') or []) if int(audit.get('latestRequestedExtensionBatch') or 0)==REQUESTED else []
 prior_ids={str(x.get('id')) for x in prior if isinstance(x,dict)};new_done=[];total_added=0;rejected=0
 for pid,aliases in TARGETS:
  if pid in prior_ids:continue
  r=res.get(pid)
  if not r:continue
  display=aliases[0];meta=idx['people'].get(pid) or {};path=ROOT/(meta.get('file') or f'data/editorial/short-biography-extensions/{pid}.json');payload=read(path,{}) or {'personId':pid,'personNameAr':display,'beforeWords':int(r.get('finalWords') or r.get('beforeWords') or 0),'passages':[]};payload.setdefault('passages',[]);seen={fp(x.get('text') or '') for x in payload['passages'] if isinstance(x,dict)};before=int(payload.get('beforeWords') or r.get('finalWords') or r.get('beforeWords') or 0);current=before+sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload['passages'] if isinstance(x,dict))
  for alias in aliases:
   if current>=TARGET:break
   for fn,pos,txt in windows_for(vols,alias):
    if current>=TARGET:break
    h=fp(txt)
    if h in seen:continue
    n=wc(txt);payload['passages'].append({'text':txt,'wordCount':n,'kind':'direct-ibn-hisham-normalized-name-window','source':{'title':'السيرة النبوية — سيرة ابن هشام','author':'عبد الملك بن هشام','edition':'تحقيق عمر عبد السلام تدمري','archiveItem':ITEM,'archiveFile':fn,'url':BASE+fn,'sourceWordOffset':pos,'matchedAlias':alias,'ownershipBasis':'Accepted source window contains the normalized canonical person alias itself; no generated historical facts.'}});seen.add(h);current+=n;total_added+=n
  added=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload['passages']);final=before+added
  if final>=TARGET:
   payload.update({'schema':'short-biography-source-extension-v10','generatedAt':now(),'personNameAr':display,'targetWords':TARGET,'addedWords':added,'finalWords':final,'status':'EXTENDED_TO_500','policy':'Readable Ibn Hisham windows containing a specific normalized person alias; no name-free context, duplicate source windows, or generated factual fill-in.'});path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');idx['people'][pid]={'id':pid,'nameAr':display,'beforeWords':before,'addedWords':added,'finalWords':final,'status':'EXTENDED_TO_500','file':str(path.relative_to(ROOT))};new_done.append({'id':pid,'nameAr':display,'finalWords':final,'file':str(path.relative_to(ROOT))})
 combined=[];seenids=set()
 for x in prior+new_done:
  xid=str(x.get('id'))
  if xid and xid not in seenids:combined.append(x);seenids.add(xid)
 combined=combined[:REQUESTED];done_ids={str(x.get('id')) for x in combined};newres=[x for x in audit.get('residualUnder500',[]) if str(x.get('id')) not in {str(y.get('id')) for y in new_done}]
 # extendedTo500 is strict global count; add only newly completed records in this run.
 audit.update({'schema':'short-biographies-500-audit-v10','generatedAt':now(),'latestRequestedExtensionBatch':REQUESTED,'latestCompletedExtensionBatch':len(combined),'latestBatchPeople':combined,'latestBatchSource':'Ibn Hisham / Internet Archive '+ITEM,'latestBatchNewlyCompletedThisRun':len(new_done),'latestBatchSourceWordsAddedThisRun':total_added,'latestBatchRejectedOcrWindows':rejected,'extendedTo500':int(audit.get('extendedTo500') or 0)+len(new_done),'sourceLimitedAfter':len(newres),'residualUnder500':newres,'complete':len(newres)==0});idx.update({'schema':'short-biography-source-extension-index-v10','generatedAt':now()});I.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');A.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'requested':REQUESTED,'batchCompleted':len(combined),'newlyCompleted':len(new_done),'sourceWordsAdded':total_added,'remaining':len(newres)},ensure_ascii=False))
if __name__=='__main__':main()
