#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]; EDIT=ROOT/'data'/'editorial'
AUDIT=EDIT/'short_biographies_500_audit.json'; INDEX=EDIT/'short_biography_extensions.json'; OUT=EDIT/'short-biography-extensions'
EXPANDED=ROOT/'data'/'expanded_biographies_135_full.json'; TARGET=500; GOAL=50
API='https://ar.wikisource.org/w/api.php'; UA='ProphetBiographyResearchBot/1.3 (strict direct biography extraction)'
ALLOWED_PREFIXES=('سير أعلام النبلاء/','أسد الغابة','الاستيعاب','الإصابة','تهذيب الكمال','صفة الصفوة','وفيات الأعيان','البداية والنهاية','تاريخ دمشق')
DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]'); AR=re.compile(r'[\u0600-\u06ff]')
STOP={'سيدنا','السيد','الإمام','الشيخ','العلامة','الحافظ','رضي','الله','عنه','عنها','الصديق','الزهراء'}
BAD=('traditions','source-critical','sunan','musnad','edition','editor')
TOKENS={'abdullah':'عبد الله','abd':'عبد','ibn':'بن','bin':'بن','bint':'بنت','abu':'أبو','umm':'أم','ali':'علي','akbar':'الأكبر','husayn':'الحسين','hasan':'الحسن','muttalib':'المطلب','manaf':'مناف','mudar':'مضر','nizar':'نزار','habiba':'حبيبة','lahab':'لهب','jafar':'جعفر','uthman':'عثمان','affan':'عفان','maymuna':'ميمونة','harith':'الحارث','ilyas':'إلياس','halima':'حليمة','sadiyya':'السعدية','fihr':'فهر','arwa':'أروى','qasim':'القاسم','zayd':'زيد','urwa':'عروة','zubayr':'الزبير','zubair':'الزبير','as':'العاص','aas':'العاص','rabi':'الربيع','luayy':'لؤي','ghalib':'غالب','kinana':'كنانة','khuzayma':'خزيمة','murra':'مرة','kab':'كعب','safiyya':'صفية','yaghuth':'يغوث','wahb':'وهب','amir':'عامر','hashim':'هاشم','saad':'سعد','talib':'طالب','abbas':'عباس','hamza':'حمزة','aqil':'عقيل','zaynab':'زينب','ruqayya':'رقية','kulthum':'كلثوم','fatima':'فاطمة','khalid':'خالد','walid':'الوليد','muadh':'معاذ','jabal':'جبل','bakr':'بكر','hurayra':'هريرة','ubayda':'عبيدة','jarrah':'الجراح','anas':'أنس','malik':'مالك','bilal':'بلال','rabah':'رباح','jabir':'جابر','omar':'عمر','umar':'عمر','khattab':'الخطاب','amr':'عمرو','salman':'سلمان','farisi':'الفارسي','ammar':'عمار','yasir':'ياسر','miqdad':'المقداد','aswad':'الأسود','abi':'أبي','waqqas':'وقاص','talha':'طلحة','ubaydullah':'عبيد الله','awwam':'العوام','saeed':'سعيد','zaid':'زيد','thabit':'ثابت','thawban':'ثوبان'}

def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(p,d=None):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def norm(s):
    s=DIAC.sub('',str(s or '')).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    s=re.sub(r'[^\u0600-\u06ff\s-]',' ',s);return re.sub(r'\s+',' ',s).strip()
def wc(s):return len(re.findall(r'\S+',str(s or '').strip()))
def fp(s):return hashlib.sha256(norm(s).encode()).hexdigest()
def readable(s):
    toks=str(s or '').split()
    if len(toks)<45:return False
    letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s)); ratio=len(AR.findall(s))/max(1,letters); lens=[len(DIAC.sub('',t)) for t in toks]
    return ratio>.78 and max(lens,default=0)<42 and sum(n>20 for n in lens)/max(1,len(lens))<.035

def translit(value):
    s=str(value or '').strip().lower().replace('_','-'); parts=[p for p in re.split(r'[-\s]+',s) if p and p not in {'al','el'}]
    if len(AR.findall(s))>=3:return value
    if not parts or any(p not in TOKENS for p in parts):return None
    return ' '.join(TOKENS[p] for p in parts)
def variants(name):
    out=[]
    for raw in (name,translit(name)):
        if raw and len(AR.findall(str(raw)))>=3 and raw not in out:out.append(str(raw))
    for raw in list(out):
        s=raw
        for x in ('سيدنا','السيد','الإمام','الشيخ','العلامة','الحافظ','الصديق','الزهراء','رضي الله عنه','رضي الله عنها'):s=s.replace(x,' ')
        s=re.sub(r'\s+',' ',s).strip()
        if s and s not in out:out.append(s)
    return out

def api(params,timeout=25):
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
    p=Text();p.feed(j['parse'].get('text') or ''); title=j['parse'].get('title') or title
    return {'title':title,'text':p.text(),'url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote(title.replace(' ','_'))}
def tokens(name):return [x for x in norm(name).split() if len(x)>2 and x not in STOP]
def score(name,title):
    a=set(tokens(name));b=set(tokens(title.split('/',1)[-1]));
    if not a:return 0
    s=len(a&b)/len(a)
    if norm(name) in norm(title) or norm(title.split('/',1)[-1]) in norm(name):s+=.5
    return s
def titles(name):
    out=['سير أعلام النبلاء/'+name]
    for q in (f'intitle:"{name}"',f'"{name}"'):
        try:j=api({'action':'query','list':'search','srsearch':q,'srnamespace':'0','srlimit':'15'})
        except Exception:continue
        for x in j.get('query',{}).get('search',[]):
            t=x.get('title') or ''
            if any(t.startswith(p) for p in ALLOWED_PREFIXES) and score(name,t)>=.58:out.append(t)
        time.sleep(.04)
    seen=[]
    for t in sorted(out,key=lambda x:score(name,x),reverse=True):
        if t not in seen:seen.append(t)
    return seen
def ownership(name,page):
    if score(name,page['title'])<.58:return False
    tt=tokens(name); opening=norm(' '.join(page['text'].split()[:240]))
    return bool(tt) and sum(t in opening for t in tt)>=max(1,min(2,len(tt)))
def existing_dup_sets():
    urls=set();hashes=set();p=read(EXPANDED,{}) or {}
    for r in p.get('people',[]) if isinstance(p,dict) else []:
        src=r.get('source') if isinstance(r.get('source'),dict) else {};u=src.get('url');t=r.get('biographyAr')
        if u:urls.add(u)
        if t:hashes.add(fp(t))
    return urls,hashes

def main():
    audit=read(AUDIT,{}) or {};idx=read(INDEX,{}) or {};idx.setdefault('people',{});OUT.mkdir(parents=True,exist_ok=True)
    residual=list(audit.get('residualUnder500') or []);known_urls,known_hashes=existing_dup_sets();completed=[];attempted=0;pages_added=words_added=0;errors=[]
    for r in residual:
        if len(completed)>=GOAL:break
        pid=str(r.get('id') or '');raw=str(r.get('nameAr') or '')
        if not pid or any(x in raw.lower() for x in BAD):continue
        aliases=variants(raw)
        if not aliases:continue
        name=aliases[-1];meta=idx['people'].get(pid) or {};path=ROOT/(meta.get('file') or f'data/editorial/short-biography-extensions/{re.sub(r"[^A-Za-z0-9._-]+","-",pid)}.json')
        payload=read(path,{}) or {'schema':'short-biography-source-extension-v5','personId':pid,'personNameAr':name,'targetWords':TARGET,'beforeWords':int(r.get('beforeWords') or 0),'passages':[]}
        payload.setdefault('passages',[]);before=int(payload.get('beforeWords') or r.get('beforeWords') or 0);seen={fp(x.get('text') or '') for x in payload['passages'] if isinstance(x,dict)}
        current=before+sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload['passages'] if isinstance(x,dict))
        if current>=TARGET:continue
        attempted+=1
        for alias in aliases:
            for title in titles(alias)[:10]:
                if current>=TARGET:break
                try:page=fetch_page(title);time.sleep(.05)
                except Exception as e:errors.append({'id':pid,'title':title,'error':str(e)[:160]});continue
                if not page or not readable(page['text']) or not ownership(alias,page):continue
                h=fp(page['text'])
                if h in seen or h in known_hashes or page['url'] in known_urls:continue
                n=wc(page['text']);payload['passages'].append({'text':page['text'],'wordCount':n,'kind':'direct-approved-biography-page','source':{'title':page['title'],'provider':'Arabic Wikisource','url':page['url'],'retrievedAt':now(),'ownershipBasis':'Direct biographical page title and opening matched to canonical person.'}})
                seen.add(h);known_hashes.add(h);known_urls.add(page['url']);current+=n;pages_added+=1;words_added+=n
            if current>=TARGET:break
        added=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload['passages']);final=before+added
        if payload['passages']:
            status='EXTENDED_TO_500' if final>=TARGET else 'SOURCE_LIMITED';payload.update({'schema':'short-biography-source-extension-v5','generatedAt':now(),'personNameAr':name,'addedWords':added,'finalWords':final,'status':status,'policy':'Readable direct titled biographical source pages only; no incidental mentions, context padding, duplicates, or invented factual fill-in.'})
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');idx['people'][pid]={'id':pid,'nameAr':name,'beforeWords':before,'addedWords':added,'finalWords':final,'status':status,'file':str(path.relative_to(ROOT))}
        if final>=TARGET:
            completed.append({'id':pid,'nameAr':name,'finalWords':final,'file':str(path.relative_to(ROOT))});r['finalWords']=final;r['addedWords']=added;r['missingWords']=0
    done={x['id'] for x in completed};new_res=[r for r in residual if r.get('id') not in done]
    audit.update({'schema':'short-biographies-500-audit-v7','generatedAt':now(),'onlineSource':'Approved Arabic Wikisource direct biographical works','latestRequestedExtensionBatch':GOAL,'latestCompletedExtensionBatch':len(completed),'latestBatchPeople':completed,'latestBatchAttempted':attempted,'latestBatchPagesAdded':pages_added,'latestBatchSourceWordsAdded':words_added,'onlineExtractionErrors':errors[:100],'extendedTo500':int(audit.get('extendedTo500') or 0)+len(completed),'sourceLimitedAfter':len(new_res),'residualUnder500':new_res,'complete':len(new_res)==0})
    idx.update({'schema':'short-biography-source-extension-index-v7','generatedAt':now()});INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'requested':GOAL,'completed':len(completed),'attempted':attempted,'pagesAdded':pages_added,'wordsAdded':words_added,'remaining':len(new_res)},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
