#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'data'/'editorial';A=E/'short_biographies_500_audit.json';I=E/'short_biography_extensions.json';O=E/'short-biography-extensions';TARGET=500
ITEM='fp94563_202505';BASE=f'https://archive.org/download/{ITEM}/';FILES=['01_94563_djvu.txt','02_94564_djvu.txt','03_94565_djvu.txt','04_94566_djvu.txt']
TARGETS=[
('abu-bakr','أبو بكر'),('khalid-ibn-al-walid','خالد بن الوليد'),('muadh-ibn-jabal','معاذ بن جبل'),('person-0cc8963df4cd','عثمان بن عفان'),('person-0632526f4f61','جعفر بن أبي طالب'),('person-051301ccb5bf','الحسين بن علي'),('person-04c5aa88d621','أم حبيبة'),('person-0f1c7cf0bc88','ميمونة بنت الحارث'),('person-1a613275126e','عروة بن الزبير'),('person-14301a19d094','فهر بن مالك'),('person-177f75bd083c','كنانة'),('person-1a26b914289b','مرة بن كعب'),('person-2204d32f7044','أبو العاص بن الربيع'),('person-224da2bd3aec','لؤي بن غالب'),('person-248fde5641d4','صفية بنت عبد المطلب'),('person-27040d99eb01','سودة بنت زمعة'),('person-3afd4bc4b4e8','أبو سفيان بن الحارث'),('person-3b1c8fb6a9a5','أبو سلمة'),('person-59487b80ae9d','الزبير بن العوام'),('person-62fc96ff1e57','كلاب بن مرة'),('person-69bc01fbc242','حفصة بنت عمر'),('person-6f9bc4267d74','أم سلمة'),('person-77982ed9d8d5','عائشة'),('person-8365c67f7e7c','عبد المطلب'),('person-872432cece41','عبد الله بن الزبير'),('person-950261ac6f78','أبو طالب'),('person-95aa67be1d14','عقيل بن أبي طالب'),('person-99149c5c072c','هاشم بن عبد مناف'),('person-d3f51877a09f','العباس بن عبد المطلب'),('person-da8e2ffd90a2','جويرية بنت الحارث'),('person-e59d18e68796','عبد الله بن عباس'),('person-e60283d67ffd','زينب بنت جحش'),('person-f54b80d2d221','حمزة بن عبد المطلب'),('person-f8216ef01954','سعد بن أبي وقاص'),('person-f95ed2a0a66a','خديجة'),('person-facd06c50592','عبد مناف بن قصي'),('salman-al-farisi','سلمان الفارسي'),('saeed-ibn-zayd','سعيد بن زيد'),('person-b758f13b7aca','آمنة بنت وهب'),('person-bd9f4f9ec113','قصي بن كلاب'),('person-e757d74ff462','نزار بن معد'),('person-e8a4a2468176','كعب بن لؤي'),('person-74cc7918c881','معد بن عدنان'),('person-7752e2dfa848','مدركة'),('person-7060e68d653d','خزيمة'),('person-117ca7ce1c07','إلياس'),('person-040170814f57','مضر'),('person-763766a4c305','عاتكة بنت عبد المطلب'),('person-dd9b45c017ac','أم كلثوم'),('person-ee9533da8a95','رقية')]
AR=re.compile(r'[\u0600-\u06ff]');DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]')
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,d=None):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return d
def norm(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def wc(s):return len(norm(s).split())
def fp(s):return hashlib.sha256(DIAC.sub('',norm(s)).encode()).hexdigest()
def readable(s):
 t=norm(s).split();letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s));lens=[len(DIAC.sub('',x)) for x in t]
 return len(t)>=35 and len(AR.findall(s))/max(1,letters)>.80 and max(lens,default=0)<40 and sum(x>20 for x in lens)/max(1,len(lens))<.035
def fetch_sources():
 out=[]
 for fn in FILES:
  req=urllib.request.Request(BASE+fn,headers={'User-Agent':'ProphetBiographyResearchBot/1.0'})
  with urllib.request.urlopen(req,timeout=60) as r: txt=r.read().decode('utf-8','ignore')
  # IA OCR text is page/paragraph oriented. Keep paragraph blocks, then bounded direct-name excerpts.
  for p in re.split(r'\n\s*\n|\f',txt):
   p=norm(p)
   if readable(p):out.append((fn,p))
 return out
def excerpt(p,name):
 words=p.split();joined=' '.join(words);pos=joined.find(name)
 if pos<0:return None
 # centre a bounded 280-word source excerpt around the exact person mention
 pre=joined[:pos].split();i=len(pre);a=max(0,i-130);b=min(len(words),i+150);x=' '.join(words[a:b])
 return x if name in x and readable(x) else None
def main():
 audit=read(A,{}) or {};idx=read(I,{}) or {};idx.setdefault('people',{});res={str(x.get('id')):x for x in audit.get('residualUnder500',[]) if isinstance(x,dict)};O.mkdir(parents=True,exist_ok=True);blocks=fetch_sources();done=[];total_added=0;rejected=0
 for pid,name in TARGETS:
  r=res.get(pid)
  if not r:continue
  meta=idx['people'].get(pid) or {};path=ROOT/(meta.get('file') or f'data/editorial/short-biography-extensions/{pid}.json');payload=read(path,{}) or {'personId':pid,'personNameAr':name,'beforeWords':int(r.get('finalWords') or r.get('beforeWords') or 0),'passages':[]};payload.setdefault('passages',[]);seen={fp(x.get('text') or '') for x in payload['passages'] if isinstance(x,dict)};before=int(payload.get('beforeWords') or 0);current=before+sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload['passages'] if isinstance(x,dict))
  for fn,p in blocks:
   if current>=TARGET:break
   if name not in p:continue
   x=excerpt(p,name)
   if not x:rejected+=1;continue
   h=fp(x)
   if h in seen:continue
   n=wc(x);payload['passages'].append({'text':x,'wordCount':n,'kind':'direct-ibn-hisham-source-context','source':{'title':'السيرة النبوية — سيرة ابن هشام','author':'عبد الملك بن هشام','edition':'تحقيق عمر عبد السلام تدمري','archiveItem':ITEM,'archiveFile':fn,'url':BASE+fn,'ownershipBasis':'Every accepted excerpt contains the exact canonical person name; no generated historical facts.'}});seen.add(h);current+=n;total_added+=n
  added=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload['passages']);final=before+added
  if final>=TARGET:
   payload.update({'schema':'short-biography-source-extension-v9','generatedAt':now(),'personNameAr':name,'targetWords':TARGET,'addedWords':added,'finalWords':final,'status':'EXTENDED_TO_500','policy':'Readable direct Ibn Hisham excerpts containing the exact person name; no incidental name-free context and no generated factual fill-in.'});path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');idx['people'][pid]={'id':pid,'nameAr':name,'beforeWords':before,'addedWords':added,'finalWords':final,'status':'EXTENDED_TO_500','file':str(path.relative_to(ROOT))};done.append({'id':pid,'nameAr':name,'finalWords':final,'file':str(path.relative_to(ROOT))})
 done_ids={x['id'] for x in done};newres=[x for x in audit.get('residualUnder500',[]) if str(x.get('id')) not in done_ids];audit.update({'schema':'short-biographies-500-audit-v9','generatedAt':now(),'latestRequestedExtensionBatch':50,'latestCompletedExtensionBatch':len(done),'latestBatchPeople':done,'latestBatchSource':'Ibn Hisham / Internet Archive '+ITEM,'latestBatchSourceWordsAdded':total_added,'latestBatchRejectedOcrBlocks':rejected,'extendedTo500':int(audit.get('extendedTo500') or 0)+len(done),'sourceLimitedAfter':len(newres),'residualUnder500':newres,'complete':len(newres)==0});idx.update({'schema':'short-biography-source-extension-index-v9','generatedAt':now()});I.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');A.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'requested':50,'completed':len(done),'sourceWordsAdded':total_added,'remaining':len(newres)},ensure_ascii=False))
if __name__=='__main__':main()
