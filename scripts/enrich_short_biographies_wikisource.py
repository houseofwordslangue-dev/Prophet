#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import hashlib,html,json,re,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];E=ROOT/'data'/'editorial';A=E/'short_biographies_500_audit.json';I=E/'short_biography_extensions.json';O=E/'short-biography-extensions';TARGET=500;REQUESTED=50;BATCH=3
API='https://ar.wikisource.org/w/api.php';UA='ProphetBiographyResearchBot/1.6 (direct classical biography extraction)'
PREFIXES=('سير أعلام النبلاء/','وفيات الأعيان/','تاريخ دمشق/','تهذيب الكمال/','الاستيعاب/','الإصابة/','أسد الغابة/','صفة الصفوة/','البداية والنهاية/')
AR=re.compile(r'[\u0600-\u06ff]');D=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]')
BAD=('traditions','source-critical','sunan','musnad','edition','editor','scholarship','literature','sayings','biographies','stories','unknown','مؤلف غير محسوم','غير مذكور')
def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,d=None):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def norm(s):
 s=D.sub('',str(s or '')).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي')
 return re.sub(r'\s+',' ',re.sub(r'[^\u0600-\u06ff\s]',' ',s)).strip()
def wc(s):return len(str(s or '').split())
def fp(s):return hashlib.sha256(norm(s).encode()).hexdigest()
def readable(s):
 t=str(s or '').split()
 if len(t)<45:return False
 lens=[len(D.sub('',x)) for x in t];letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s))
 return len(AR.findall(s))/max(1,letters)>.78 and max(lens,default=0)<42 and sum(x>20 for x in lens)/max(1,len(lens))<.035
class H(HTMLParser):
 def __init__(self):super().__init__();self.a=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style','noscript'):self.skip+=1
  if t in ('p','br','li','h1','h2','h3','h4','tr'):self.a.append('\n')
 def handle_endtag(self,t):
  if t in ('script','style','noscript') and self.skip:self.skip-=1
  if t in ('p','li','h1','h2','h3','h4','tr'):self.a.append('\n')
 def handle_data(self,d):
  if not self.skip:self.a.append(d)
 def text(self):return re.sub(r'\n{3,}','\n\n',html.unescape(''.join(self.a))).strip()
def api(params,timeout=20):
 q=dict(params);q.update({'format':'json','formatversion':'2','origin':'*'});req=urllib.request.Request(API+'?'+urllib.parse.urlencode(q),headers={'User-Agent':UA})
 with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8'))
def get(title):
 try:j=api({'action':'parse','page':title,'prop':'text','disabletoc':'1','disableeditsection':'1'})
 except Exception:return None
 if 'parse' not in j:return None
 h=H();h.feed(j['parse'].get('text') or '');title=j['parse'].get('title') or title
 return {'title':title,'text':h.text(),'url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote(title.replace(' ','_'))}
def nt(name):return [x for x in norm(name).split() if len(x)>2 and x not in {'الامام','الشيخ','الحافظ','السيد','ابن','بنت','ابي','ابو'}]
def score(name,title):
 a=set(nt(name));b=set(nt(title.split('/',1)[-1]));
 if not a:return 0
 s=len(a&b)/len(a)
 if norm(name) in norm(title) or norm(title.split('/',1)[-1]) in norm(name):s+=.5
 return s
def variants(name):
 out=[str(name or '').strip()];s=out[0]
 for x in ('سيدنا','السيد','الإمام','الشيخ','العلامة','الحافظ','رضي الله عنه','رضي الله عنها'):s=s.replace(x,' ')
 s=re.sub(r'\s+',' ',s).strip()
 if s and s not in out:out.append(s)
 return [x for x in out if len(AR.findall(x))>=3]
def titles(name):
 out=[]
 for p in PREFIXES:out.append(p+name)
 for q in (f'intitle:"{name}"',f'"{name}"'):
  try:j=api({'action':'query','list':'search','srsearch':q,'srnamespace':'0','srlimit':'20'})
  except Exception:continue
  for x in j.get('query',{}).get('search',[]):
   t=x.get('title') or ''
   if any(t.startswith(p) for p in PREFIXES) and score(name,t)>=.5:out.append(t)
  time.sleep(.04)
 seen=[]
 for t in sorted(out,key=lambda x:score(name,x),reverse=True):
  if t not in seen:seen.append(t)
 return seen[:18]
def owned(name,page):
 if score(name,page['title'])<.5:return False
 toks=nt(name);opening=norm(' '.join(page['text'].split()[:320]))
 return bool(toks) and sum(t in opening for t in toks)>=max(1,min(2,len(toks)))
def main():
 audit=read(A,{}) or {};idx=read(I,{}) or {};idx.setdefault('people',{});O.mkdir(parents=True,exist_ok=True)
 residual=[x for x in audit.get('residualUnder500',[]) if isinstance(x,dict)]
 # Complete easiest source-backed cases first, but never count non-person records.
 residual.sort(key=lambda x:(int(x.get('missingWords') or TARGET),str(x.get('id') or '')))
 completed=[];attempted=0;pages=0;words=0;errors=[]
 for r in residual:
  if len(completed)>=REQUESTED:break
  pid=str(r.get('id') or '');name=str(r.get('nameAr') or '').strip();low=name.lower()
  if not pid or any(b in low for b in BAD) or len(AR.findall(name))<3:continue
  meta=idx['people'].get(pid) or {};path=ROOT/(meta.get('file') or f'data/editorial/short-biography-extensions/{re.sub(r"[^A-Za-z0-9._-]+","-",pid)}.json')
  p=read(path,{}) or {'personId':pid,'personNameAr':name,'targetWords':TARGET,'beforeWords':int(r.get('finalWords') or r.get('beforeWords') or 0),'passages':[]};p.setdefault('passages',[])
  before=int(p.get('beforeWords') or r.get('finalWords') or r.get('beforeWords') or 0);seen={fp(x.get('text') or '') for x in p['passages'] if isinstance(x,dict)};urls={str((x.get('source') or {}).get('url') or '') for x in p['passages'] if isinstance(x,dict)}
  current=before+sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in p['passages'] if isinstance(x,dict))
  if current>=TARGET:continue
  attempted+=1
  for v in variants(name):
   for title in titles(v):
    if current>=TARGET:break
    try:page=get(title);time.sleep(.04)
    except Exception as e:errors.append({'id':pid,'title':title,'error':str(e)[:140]});continue
    if not page or page['url'] in urls or not readable(page['text']) or not owned(v,page):continue
    h=fp(page['text'])
    if h in seen:continue
    n=wc(page['text']);p['passages'].append({'text':page['text'],'wordCount':n,'kind':'direct-classical-biography-page','source':{'title':page['title'],'provider':'Arabic Wikisource','url':page['url'],'retrievedAt':now(),'ownershipBasis':'Direct classical biography page title and opening match the canonical person; no generated historical facts.'}});seen.add(h);urls.add(page['url']);current+=n;pages+=1;words+=n
   if current>=TARGET:break
  added=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in p['passages']);final=before+added
  if p['passages']:
   status='EXTENDED_TO_500' if final>=TARGET else 'SOURCE_LIMITED';p.update({'schema':'short-biography-source-extension-v11','generatedAt':now(),'personNameAr':name,'addedWords':added,'finalWords':final,'status':status,'policy':'Direct readable classical biography pages only; exact person ownership required; duplicates, incidental mentions, collapsed OCR, and invented factual fill-in excluded.'});path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');idx['people'][pid]={'id':pid,'nameAr':name,'beforeWords':before,'addedWords':added,'finalWords':final,'status':status,'file':str(path.relative_to(ROOT))}
  if final>=TARGET:completed.append({'id':pid,'nameAr':name,'finalWords':final,'file':str(path.relative_to(ROOT))})
 done={x['id'] for x in completed};newres=[x for x in audit.get('residualUnder500',[]) if str(x.get('id')) not in done]
 audit.update({'schema':'short-biographies-500-audit-v11','generatedAt':now(),'latestRequestedExtensionBatch':REQUESTED,'latestCompletedExtensionBatch':len(completed),'latestBatchNumber':BATCH,'latestBatchPeople':completed,'latestBatchSource':'Arabic Wikisource direct classical biography works','latestBatchAttempted':attempted,'latestBatchPagesAdded':pages,'latestBatchSourceWordsAdded':words,'latestBatchErrors':errors[:100],'extendedTo500':int(audit.get('extendedTo500') or 0)+len(completed),'sourceLimitedAfter':len(newres),'residualUnder500':newres,'complete':len(newres)==0})
 idx.update({'schema':'short-biography-source-extension-index-v11','generatedAt':now()});I.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');A.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'batch':BATCH,'requested':REQUESTED,'completed':len(completed),'attempted':attempted,'pagesAdded':pages,'wordsAdded':words,'remaining':len(newres)},ensure_ascii=False))
if __name__=='__main__':main()
