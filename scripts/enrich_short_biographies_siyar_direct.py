#!/usr/bin/env python3
from __future__ import annotations
import json,re,urllib.parse,urllib.request,html,hashlib
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'data'/'editorial';A=E/'short_biographies_500_audit.json';I=E/'short_biography_extensions.json';O=E/'short-biography-extensions';TARGET=500
API='https://ar.wikisource.org/w/api.php';UA='ProphetBiographyResearchBot/1.0';AR=re.compile(r'[\u0600-\u06ff]');D=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]')
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,d=None):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return d
def norm(s):
 s=D.sub('',str(s or '')).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي');return re.sub(r'\s+',' ',re.sub(r'[^\u0600-\u06ff\s]',' ',s)).strip()
def wc(s):return len(str(s or '').split())
def fp(s):return hashlib.sha256(norm(s).encode()).hexdigest()
def readable(s):
 t=str(s or '').split();
 if len(t)<45:return False
 lens=[len(D.sub('',x)) for x in t];letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s));return len(AR.findall(s))/max(1,letters)>.78 and max(lens,default=0)<42 and sum(x>20 for x in lens)/len(lens)<.035
class H(HTMLParser):
 def __init__(self):super().__init__();self.a=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style','noscript'):self.skip+=1
  if t in ('p','br','li','h1','h2','h3'):self.a.append('\n')
 def handle_endtag(self,t):
  if t in ('script','style','noscript') and self.skip:self.skip-=1
  if t in ('p','li','h1','h2','h3'):self.a.append('\n')
 def handle_data(self,d):
  if not self.skip:self.a.append(d)
 def text(self):return re.sub(r'\n{3,}','\n\n',html.unescape(''.join(self.a))).strip()
def get(title):
 q=urllib.parse.urlencode({'action':'parse','page':title,'prop':'text','format':'json','formatversion':'2'});req=urllib.request.Request(API+'?'+q,headers={'User-Agent':UA})
 try:
  with urllib.request.urlopen(req,timeout=12) as r:j=json.loads(r.read().decode())
 except:return None
 if 'parse' not in j:return None
 h=H();h.feed(j['parse'].get('text') or '');text=h.text();return {'title':j['parse'].get('title') or title,'text':text,'url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote((j['parse'].get('title') or title).replace(' ','_'))}
def variants(name):
 out=[name];s=name
 for x in ('سيدنا','السيد','الإمام','الشيخ','العلامة','الحافظ','الصديق','الزهراء','رضي الله عنه','رضي الله عنها'):
  s=s.replace(x,' ')
 s=re.sub(r'\s+',' ',s).strip()
 if s and s not in out:out.append(s)
 return out
def match(name,title,text):
 sub=title.split('/',1)[-1];a=set(norm(name).split());b=set(norm(sub).split());a={x for x in a if len(x)>2};b={x for x in b if len(x)>2}
 if not a or len(a&b)/len(a)<.6:return False
 opening=norm(' '.join(text.split()[:220]));return sum(x in opening for x in a)>=max(1,min(2,len(a)))
def main():
 audit=read(A,{}) or {};idx=read(I,{}) or {};idx.setdefault('people',{});O.mkdir(parents=True,exist_ok=True);res=list(audit.get('residualUnder500') or []);added_pages=added_words=completed=0;errors=[]
 for r in res:
  pid=str(r.get('id') or '');name=str(r.get('nameAr') or '')
  if len(AR.findall(name))<3:continue
  meta=idx['people'].get(pid) or {};path=ROOT/(meta.get('file') or f'data/editorial/short-biography-extensions/{re.sub(r"[^A-Za-z0-9._-]+","-",pid)}.json');p=read(path,{}) or {'personId':pid,'personNameAr':name,'targetWords':TARGET,'beforeWords':int(r.get('beforeWords') or 0),'passages':[]};seen={fp(x.get('text') or '') for x in p.get('passages',[]) if isinstance(x,dict)};before=int(p.get('beforeWords') or r.get('beforeWords') or 0);current=before+sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in p.get('passages',[]) if isinstance(x,dict))
  if current>=TARGET:continue
  for v in variants(name):
   page=get('سير أعلام النبلاء/'+v)
   if not page:continue
   if not readable(page['text']) or not match(v,page['title'],page['text']):continue
   k=fp(page['text'])
   if k in seen:continue
   n=wc(page['text']);p.setdefault('passages',[]).append({'text':page['text'],'wordCount':n,'kind':'direct-siyar-biography-page','source':{'title':page['title'],'author':'الذهبي','provider':'Arabic Wikisource','url':page['url'],'retrievedAt':now(),'ownershipBasis':'Direct Siyar biographical subpage matched to canonical person.'}});seen.add(k);current+=n;added_pages+=1;added_words+=n;break
  if p.get('passages'):
   added=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in p['passages']);final=before+added;status='EXTENDED_TO_500' if final>=TARGET else 'SOURCE_LIMITED';p.update({'schema':'short-biography-source-extension-v4','generatedAt':now(),'addedWords':added,'finalWords':final,'status':status,'policy':'Direct Siyar biography pages and prior direct source-owned extracts only; no incidental mentions or invented factual fill-in.'});path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');idx['people'][pid]={'id':pid,'nameAr':name,'beforeWords':before,'addedWords':added,'finalWords':final,'status':status,'file':str(path.relative_to(ROOT))};
   if int(r.get('finalWords') or 0)<TARGET and final>=TARGET:completed+=1
   r.update({'addedWords':added,'finalWords':final,'missingWords':max(0,TARGET-final)})
 new=[x for x in res if int(x.get('finalWords') or 0)<TARGET];audit.update({'schema':'short-biographies-500-audit-v4','generatedAt':now(),'directSiyarPagesAdded':added_pages,'directSiyarWordsAdded':added_words,'extendedTo500':int(audit.get('extendedTo500') or 0)+completed,'sourceLimitedAfter':len(new),'residualUnder500':new,'complete':len(new)==0});idx.update({'schema':'short-biography-source-extension-index-v4','generatedAt':now()});I.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');A.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:audit.get(k) for k in ('indexedPeople','below500Before','extendedTo500','sourceLimitedAfter','directSiyarPagesAdded','directSiyarWordsAdded','complete')},ensure_ascii=False))
if __name__=='__main__':main()
