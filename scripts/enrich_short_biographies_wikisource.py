#!/usr/bin/env python3
from __future__ import annotations

import hashlib, html, json, re, time, urllib.parse, urllib.request
from html.parser import HTMLParser
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[1]; EDIT=ROOT/'data'/'editorial'
AUDIT=EDIT/'short_biographies_500_audit.json'; INDEX=EDIT/'short_biography_extensions.json'; OUT=EDIT/'short-biography-extensions'
EXPANDED=ROOT/'data'/'expanded_biographies_135_full.json'; TARGET=500
API='https://ar.wikisource.org/w/api.php'; UA='ProphetBiographyResearchBot/1.0 (source-verification; non-commercial research)'
ALLOWED_PREFIXES=('سير أعلام النبلاء/','أسد الغابة','الاستيعاب','الإصابة','تهذيب الكمال','صفة الصفوة','وفيات الأعيان','البداية والنهاية','تاريخ دمشق')
DIAC=re.compile(r'[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]'); AR=re.compile(r'[\u0600-\u06ff]')
STOP={'سيدنا','السيد','الإمام','الشيخ','العلامة','الحافظ','رضي','الله','عنه','عنها','الصديق','الزهراء'}

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
    s=re.sub(r'\s+',' ',str(s or '')).strip(); toks=s.split();
    if len(toks)<45:return False
    letters=len(re.findall(r'[A-Za-z\u0600-\u06ff]',s)); ratio=len(AR.findall(s))/max(1,letters)
    lens=[len(DIAC.sub('',t)) for t in toks]
    return ratio>.78 and max(lens,default=0)<42 and sum(n>20 for n in lens)/max(1,len(lens))<.035

def api(params,timeout=25):
    q=dict(params);q.update({'format':'json','formatversion':'2','origin':'*'})
    req=urllib.request.Request(API+'?'+urllib.parse.urlencode(q),headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8'))

class Text(HTMLParser):
    def __init__(self):super().__init__();self.out=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'):self.skip+=1
        if tag in ('p','br','li','h1','h2','h3','h4','tr'):self.out.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript') and self.skip:self.skip-=1
        if tag in ('p','li','h1','h2','h3','h4','tr'):self.out.append('\n')
    def handle_data(self,data):
        if not self.skip:self.out.append(data)
    def text(self):return re.sub(r'\n{3,}','\n\n',html.unescape(''.join(self.out))).strip()

def fetch_page(title):
    j=api({'action':'parse','page':title,'prop':'text|displaytitle','disabletoc':'1','disableeditsection':'1'})
    if 'error' in j or 'parse' not in j:return None
    parser=Text();parser.feed(j['parse'].get('text') or ''); text=parser.text()
    # Remove common rendered navigation/footer fragments and normalize whitespace while preserving paragraphs.
    lines=[]
    for ln in text.splitlines():
        ln=re.sub(r'\s+',' ',ln).strip()
        if not ln or ln in {'ويكي مصدر','من ويكي مصدر، المكتبة الحرة'}:continue
        lines.append(ln)
    text='\n\n'.join(lines)
    return {'title':j['parse'].get('title') or title,'text':text,'url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote((j['parse'].get('title') or title).replace(' ','_'))}

def tokens(name):return [x for x in norm(name).split() if len(x)>2 and x not in STOP]
def title_score(name,title):
    sub=title.split('/',1)[-1];nt=set(tokens(name));tt=set(tokens(sub))
    if not nt:return 0
    score=len(nt&tt)/len(nt)
    if norm(name) in norm(sub) or norm(sub) in norm(name):score+=.5
    return score

def search_titles(name):
    out=[]; direct='سير أعلام النبلاء/'+name; out.append(direct)
    queries=[f'intitle:"{name}"',f'"{name}"']
    for q in queries:
        try:j=api({'action':'query','list':'search','srsearch':q,'srnamespace':'0','srlimit':'10'})
        except Exception:continue
        for x in j.get('query',{}).get('search',[]):
            t=x.get('title') or ''
            if any(t.startswith(p) for p in ALLOWED_PREFIXES) and title_score(name,t)>=.58:out.append(t)
    seen=[]
    for t in out:
        if t not in seen:seen.append(t)
    return sorted(seen,key=lambda t:title_score(name,t),reverse=True)

def existing_urls_and_hashes():
    urls=set(); hashes=set(); p=read(EXPANDED,{}) or {}
    for r in p.get('people',[]) if isinstance(p,dict) else []:
        u=(r.get('source') or {}).get('url') if isinstance(r.get('source'),dict) else None
        if u:urls.add(u)
        t=r.get('biographyAr')
        if t:hashes.add(fp(t))
    return urls,hashes

def main():
    audit=read(AUDIT,{}) or {}; idx=read(INDEX,{}) or {}; idx.setdefault('people',{}); OUT.mkdir(parents=True,exist_ok=True)
    residual=list(audit.get('residualUnder500') or []); existing_urls,existing_hashes=existing_urls_and_hashes()
    pages_added=0; words_added=0; newly_complete=0; errors=[]
    for pos,r in enumerate(residual,1):
        pid=str(r.get('id') or ''); name=str(r.get('nameAr') or '')
        if len(AR.findall(name))<3:continue
        final=int(r.get('finalWords') or 0); meta=idx['people'].get(pid) or {}
        path=ROOT/(meta.get('file') or f'data/editorial/short-biography-extensions/{re.sub(r"[^A-Za-z0-9._-]+","-",pid)}.json')
        payload=read(path,{}) or {'schema':'short-biography-source-extension-v3','personId':pid,'personNameAr':name,'targetWords':TARGET,'beforeWords':int(r.get('beforeWords') or 0),'passages':[]}
        seen={fp(x.get('text') or '') for x in payload.get('passages',[]) if isinstance(x,dict)}
        current=int(payload.get('beforeWords') or r.get('beforeWords') or 0)+sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload.get('passages',[]) if isinstance(x,dict))
        for title in search_titles(name)[:5]:
            if current>=TARGET:break
            try:page=fetch_page(title);time.sleep(.08)
            except Exception as e:
                errors.append({'id':pid,'title':title,'error':str(e)[:180]});continue
            if not page or title_score(name,page['title'])<.58 or not readable(page['text']):continue
            # A direct biographical subpage must identify the target in its opening material.
            opening=norm(' '.join(page['text'].split()[:220])); nt=tokens(name)
            if nt and sum(t in opening for t in nt)<max(1,min(2,len(nt))):continue
            h=fp(page['text'])
            if h in seen or h in existing_hashes or page['url'] in existing_urls:continue
            text=page['text']; n=wc(text)
            payload.setdefault('passages',[]).append({'text':text,'wordCount':n,'kind':'direct-wikisource-biography-page','source':{
                'title':page['title'],'author':'الذهبي' if page['title'].startswith('سير أعلام النبلاء/') else None,'provider':'Arabic Wikisource','url':page['url'],'retrievedAt':now(),'ownershipBasis':'Direct biographical source page title matched to canonical person.'}})
            seen.add(h);current+=n;pages_added+=1;words_added+=n
        if payload.get('passages'):
            before=int(payload.get('beforeWords') or r.get('beforeWords') or 0); added=sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in payload['passages']); final2=before+added
            payload.update({'schema':'short-biography-source-extension-v3','generatedAt':now(),'addedWords':added,'finalWords':final2,'status':'EXTENDED_TO_500' if final2>=TARGET else 'SOURCE_LIMITED','policy':'Direct titled biographical source pages or direct local person-owned extracts only; no incidental mentions, context padding, or invented factual fill-in.'})
            path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            rel=str(path.relative_to(ROOT));idx['people'][pid]={'id':pid,'nameAr':name,'beforeWords':before,'addedWords':added,'finalWords':final2,'status':payload['status'],'file':rel}
            if int(r.get('finalWords') or 0)<TARGET and final2>=TARGET:newly_complete+=1
            r['addedWords']=added;r['finalWords']=final2;r['missingWords']=max(0,TARGET-final2)
    new_res=[r for r in residual if int(r.get('finalWords') or 0)<TARGET]
    audit.update({'schema':'short-biographies-500-audit-v3','generatedAt':now(),'onlineSource':'Arabic Wikisource direct biographical pages from approved biographical works','onlineWikisourcePagesAdded':pages_added,'onlineSourceWordsAdded':words_added,'onlineExtractionErrors':errors[:100],
                  'extendedTo500':int(audit.get('extendedTo500') or 0)+newly_complete,'sourceLimitedAfter':len(new_res),'residualUnder500':new_res,'complete':len(new_res)==0})
    idx.update({'schema':'short-biography-source-extension-index-v3','generatedAt':now()})
    INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:audit.get(k) for k in ('indexedPeople','below500Before','extendedTo500','sourceLimitedAfter','onlineWikisourcePagesAdded','onlineSourceWordsAdded','complete')},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
