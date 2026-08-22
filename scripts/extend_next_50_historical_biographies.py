#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import hashlib, html, json, re, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'data'/'editorial'
AUDIT=E/'short_biographies_500_audit.json'
INDEX=E/'short_biography_extensions.json'
OUT=E/'short-biography-extensions'
BATCH_DIR=ROOT/'data'/'biography_batches'
TARGET=500
GOAL=50
API='https://ar.wikisource.org/w/api.php'
UA='ProphetBiographyResearchBot/1.2 (direct-biography-source extraction)'
AR=re.compile(r'[\u0600-\u06ff]')
DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]')
ALLOWED_PREFIXES=(
 'سير أعلام النبلاء/','أسد الغابة','الاستيعاب','الإصابة','تهذيب الكمال',
 'صفة الصفوة','وفيات الأعيان','البداية والنهاية','تاريخ دمشق'
)
BAD_RECORD_MARKERS=('traditions','source-critical','sunan','musnad','edition','editor')
STOP={'سيدنا','السيد','الإمام','الشيخ','العلامة','الحافظ','رضي','الله','عنه','عنها','الصديق','الزهراء'}
TOKENS={
'abdullah':'عبد الله','abd':'عبد','ibn':'بن','bin':'بن','bint':'بنت','abu':'أبو','umm':'أم',
'ali':'علي','akbar':'الأكبر','husayn':'الحسين','hasan':'الحسن','muttalib':'المطلب','manaf':'مناف',
'mudar':'مضر','nizar':'نزار','habiba':'حبيبة','lahab':'لهب','jafar':'جعفر','uthman':'عثمان','affan':'عفان',
'maymuna':'ميمونة','harith':'الحارث','ilyas':'إلياس','halima':'حليمة','sadiyya':'السعدية','fihr':'فهر',
'arwa':'أروى','qasim':'القاسم','zayd':'زيد','urwa':'عروة','zubayr':'الزبير','as':'العاص','rabi':'الربيع',
'luayy':'لؤي','ghalib':'غالب','kinana':'كنانة','khuzayma':'خزيمة','murra':'مرة','kab':'كعب','safiyya':'صفية',
'yaghuth':'يغوث','wahb':'وهب','amir':'عامر','hashim':'هاشم','quraysh':'قريش','saad':'سعد','talib':'طالب',
'abbas':'عباس','hamza':'حمزة','aqil':'عقيل','zaynab':'زينب','ruqayya':'رقية','kulthum':'كلثوم','fatima':'فاطمة',
'khalid':'خالد','walid':'الوليد','muadh':'معاذ','jabal':'جبل','bakr':'بكر','hurayra':'هريرة','ubayda':'عبيدة',
'jarrah':'الجراح','anas':'أنس','malik':'مالك','bilal':'بلال','rabah':'رباح','jabir':'جابر','omar':'عمر','umar':'عمر',
'khattab':'الخطاب','aas':'العاص','amr':'عمرو','salman':'سلمان','farisi':'الفارسي','ammar':'عمار','yasir':'ياسر',
'miqdad':'المقداد','aswad':'الأسود','saad':'سعد','abi':'أبي','waqqas':'وقاص','talha':'طلحة','ubaydullah':'عبيد الله',
'zubair':'الزبير','awwam':'العوام','saeed':'سعيد','zaid':'زيد','thabit':'ثابت','thabit':'ثابت','thawban':'ثوبان'
}

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,d=None):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def norm(s):
    s=DIAC.sub('',str(s or '')).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    return re.sub(r'\s+',' ',re.sub(r'[^\u0600-\u06ff\s]',' ',s)).strip()
def wc(s):return len(re.findall(r'\S+',str(s or '').strip()))
def fp(s):return hashlib.sha256(norm(s).encode('utf-8')).hexdigest()
def readable(s):
    toks=str(s or '').split()
    if len(toks)<45:return False
    letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s)); ratio=len(AR.findall(s))/max(1,letters)
    lens=[len(DIAC.sub('',t)) for t in toks]
    return ratio>.78 and max(lens,default=0)<42 and sum(n>20 for n in lens)/max(1,len(lens))<.035

def translit_to_ar(value):
    s=str(value or '').strip().lower().replace('_','-')
    if len(AR.findall(s))>=3:return value
    parts=[p for p in re.split(r'[-\s]+',s) if p and p not in {'al','el'}]
    if not parts or any(p not in TOKENS for p in parts):return None
    out=[]
    for p in parts:
        v=TOKENS[p]
        if out and p not in {'ibn','bin','bint','abi'} and v.startswith('ال') and out[-1] in {'بن','بنت','أبي'}:
            pass
        out.append(v)
    return ' '.join(out)

def variants(name):
    out=[]
    for raw in (name, translit_to_ar(name)):
        if raw and len(AR.findall(str(raw)))>=3 and raw not in out:out.append(str(raw))
    for raw in list(out):
        s=raw
        for x in ('سيدنا','السيد','الإمام','الشيخ','العلامة','الحافظ','الصديق','الزهراء','رضي الله عنه','رضي الله عنها'):
            s=s.replace(x,' ')
        s=re.sub(r'\s+',' ',s).strip()
        if s and s not in out:out.append(s)
    return out

def api(params,timeout=20):
    q=dict(params);q.update({'format':'json','formatversion':'2','origin':'*'})
    req=urllib.request.Request(API+'?'+urllib.parse.urlencode(q),headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8'))

class Text(HTMLParser):
    def __init__(self):super().__init__();self.out=[];self.skip=0
    def handle_starttag(self,t,a):
        if t in ('script','style','noscript'):self.skip+=1
        if t in ('p','br','li','h1','h2','h3','h4','tr'):self.out.append('\n')
    def handle_endtag(self,t):
        if t in ('script','style','noscript') and self.skip:self.skip-=1
        if t in ('p','li','h1','h2','h3','h4','tr'):self.out.append('\n')
    def handle_data(self,d):
        if not self.skip:self.out.append(d)
    def text(self):return re.sub(r'\n{3,}','\n\n',html.unescape(''.join(self.out))).strip()

def fetch_page(title):
    try:j=api({'action':'parse','page':title,'prop':'text|displaytitle','disabletoc':'1','disableeditsection':'1'})
    except Exception:return None
    if 'parse' not in j:return None
    p=Text();p.feed(j['parse'].get('text') or '');text=p.text()
    title=j['parse'].get('title') or title
    return {'title':title,'text':text,'url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote(title.replace(' ','_'))}

def ntokens(name):return [x for x in norm(name).split() if len(x)>2 and x not in STOP]
def score(name,title):
    a=set(ntokens(name));b=set(ntokens(title.split('/',1)[-1]))
    if not a:return 0
    s=len(a&b)/len(a)
    if norm(name) in norm(title) or norm(title.split('/',1)[-1]) in norm(name):s+=.5
    return s

def direct_titles(name):
    titles=['سير أعلام النبلاء/'+name]
    for q in (f'intitle:"{name}"',f'"{name}"'):
        try:j=api({'action':'query','list':'search','srsearch':q,'srnamespace':'0','srlimit':'12'})
        except Exception:continue
        for x in j.get('query',{}).get('search',[]):
            t=x.get('title') or ''
            if any(t.startswith(p) for p in ALLOWED_PREFIXES) and score(name,t)>=.58:titles.append(t)
        time.sleep(.05)
    seen=[]
    for t in sorted(titles,key=lambda x:score(name,x),reverse=True):
        if t not in seen:seen.append(t)
    return seen

def ownership_ok(name,page):
    if score(name,page['title'])<.58:return False
    toks=ntokens(name);opening=norm(' '.join(page['text'].split()[:240]))
    return bool(toks) and sum(t in opening for t in toks)>=max(1,min(2,len(toks)))

def existing_for(pid,name,r,idx):
    meta=(idx.get('people') or {}).get(pid) or {}
    path=ROOT/(meta.get('file') or f'data/editorial/short-biography-extensions/{re.sub(r"[^A-Za-z0-9._-]+","-",pid)}.json')
    p=read(path,{}) or {'personId':pid,'personNameAr':name,'targetWords':TARGET,'beforeWords':int(r.get('beforeWords') or 0),'passages':[]}
    p.setdefault('passages',[])
    return path,p

def main():
    audit=read(AUDIT,{}) or {};idx=read(INDEX,{}) or {};idx.setdefault('people',{});OUT.mkdir(parents=True,exist_ok=True);BATCH_DIR.mkdir(parents=True,exist_ok=True)
    residual=list(audit.get('residualUnder500') or [])
    completed=[];attempted=[];pages_added=words_added=0
    for r in residual:
        if len(completed)>=GOAL:break
        pid=str(r.get('id') or '');raw_name=str(r.get('nameAr') or '')
        if not pid or any(x in raw_name.lower() for x in BAD_RECORD_MARKERS):continue
        aliases=variants(raw_name)
        if not aliases:continue
        name=aliases[-1] if len(AR.findall(aliases[-1]))>=3 else aliases[0]
        path,p=existing_for(pid,name,r,idx)
        before=int(p.get('beforeWords') or r.get('beforeWords') or 0)
        seen={fp(x.get('text') or '') for x in p.get('passages',[]) if isinstance(x,dict)}
        current=before+sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in p['passages'] if isinstance(x,dict))
        if current>=TARGET:continue
        attempted.append({'id':pid,'nameAr':name,'beforeWords':current})
        for alias in aliases:
            for title in direct_titles(alias)[:8]:
                if current>=TARGET:break
                page=fetch_page(title);time.sleep(.06)
                if not page or not readable(page['text']) or not ownership_ok(alias,page):continue
                k=fp(page['text'])
                if k in seen:continue
                n=wc(page['text']);p['passages'].append({'text':page['text'],'wordCount':n,'kind':'direct-approved-biography-page','source':{'title':page['title'],'provider':'Arabic Wikisource','url':page['url'],'retrievedAt':now(),'ownershipBasis':'Direct biographical page title and opening matched to canonical person.'}})
                seen.add(k);current+=n;pages_added+=1;words_added+=n
            if current>=TARGET:break
        added=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in p['passages'])
        final=before+added
        if p['passages']:
            status='EXTENDED_TO_500' if final>=TARGET else 'SOURCE_LIMITED'
            p.update({'schema':'short-biography-source-extension-v6','generatedAt':now(),'personNameAr':name,'addedWords':added,'finalWords':final,'status':status,'policy':'Readable direct titled biography pages only; no incidental mentions, documentary padding, duplicate text, or invented factual fill-in.'})
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            idx['people'][pid]={'id':pid,'nameAr':name,'beforeWords':before,'addedWords':added,'finalWords':final,'status':status,'file':str(path.relative_to(ROOT))}
        if final>=TARGET:
            completed.append({'id':pid,'nameAr':name,'beforeWords':int(r.get('finalWords') or r.get('beforeWords') or 0),'finalWords':final,'addedWords':max(0,final-int(r.get('finalWords') or r.get('beforeWords') or 0)),'file':str(path.relative_to(ROOT))})
            r['finalWords']=final;r['addedWords']=added;r['missingWords']=0
    completed_ids={x['id'] for x in completed}
    new_res=[r for r in residual if r.get('id') not in completed_ids]
    batch={
      'schema':'short-biography-extension-batch-v1','generatedAt':now(),'requestedCount':GOAL,'completedCount':len(completed),
      'status':'COMPLETE' if len(completed)==GOAL else 'PARTIAL_SOURCE_LIMITED','sourcePolicy':'Direct readable titled biographies from approved Arabic Wikisource biographical works; no invented fill-in.',
      'pagesAdded':pages_added,'sourceWordsAdded':words_added,'people':completed,'attemptedCount':len(attempted)
    }
    batch_path=BATCH_DIR/'short-extension-batch-02.json';batch_path.write_text(json.dumps(batch,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    previous_completed=int(audit.get('extendedTo500') or 0)
    audit.update({'schema':'short-biographies-500-audit-v6','generatedAt':now(),'extendedTo500':previous_completed+len(completed),'sourceLimitedAfter':len(new_res),'residualUnder500':new_res,'latestBatch':'data/biography_batches/short-extension-batch-02.json','latestBatchRequested':GOAL,'latestBatchCompleted':len(completed),'latestBatchPagesAdded':pages_added,'latestBatchSourceWordsAdded':words_added,'complete':len(new_res)==0})
    idx.update({'schema':'short-biography-source-extension-index-v6','generatedAt':now()})
    INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'requested':GOAL,'completed':len(completed),'attempted':len(attempted),'pagesAdded':pages_added,'wordsAdded':words_added,'remaining':len(new_res)},ensure_ascii=False,indent=2))
    if len(completed)<GOAL:raise SystemExit(2)

if __name__=='__main__':main()
