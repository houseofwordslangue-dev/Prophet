#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,os,re,unicodedata,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
MAN=ROOT/'data/recovery/retained_search_batch_3.json'
REPORT=ROOT/'data/recovery/retained_search_batch_3_report.json'
INDEX=ROOT/'data/ingested_library.json'
LIB=ROOT/'library/works'
MAX=int(os.getenv('BATCH3_MAX_FILE_BYTES',str(95*1024*1024)))
TARGET=int(os.getenv('BATCH3_TARGET','50'))
UA='ProphetLibraryBatch3/1.0'

def now(): return datetime.now(timezone.utc).isoformat()
def getj(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=45) as r:return json.loads(r.read().decode('utf-8','replace'))
def norm(s):
    s=unicodedata.normalize('NFKD',s or '')
    s=''.join(c for c in s if not unicodedata.combining(c)).casefold().replace('ʿ','').replace('ʾ','')
    return ' '.join(re.sub(r'[^\w\u0600-\u06ff]+',' ',s).split())
def sim(a,b):
    A={x for x in norm(a).split() if len(x)>1}; B={x for x in norm(b).split() if len(x)>1}
    return len(A&B)/len(A|B) if A and B else 0.0
def publicish(d):
    txt=' '.join(str(d.get(k,'')) for k in ('rights','licenseurl','description')).casefold()
    if any(x in txt for x in ('public domain','creativecommons.org/publicdomain','cc0','no known copyright')): return True
    for k in ('date','year'):
        m=re.search(r'(1[0-9]{3}|20[0-9]{2})',str(d.get(k,'')))
        if m and int(m.group(1))<=1930:return True
    return False
def search(item):
    q=' '.join(x for x in (item['title'],item.get('author','')) if x)
    params=[('q',q),('fl[]','identifier'),('fl[]','title'),('fl[]','creator'),('fl[]','date'),('fl[]','year'),('fl[]','rights'),('fl[]','licenseurl'),('fl[]','description'),('rows','30'),('output','json'),('sort[]','downloads desc')]
    data=getj('https://archive.org/advancedsearch.php?'+urllib.parse.urlencode(params))
    docs=data.get('response',{}).get('docs',[])
    scored=[]
    for d in docs:
        title=d.get('title',''); creator=d.get('creator','')
        if isinstance(title,list): title=' '.join(map(str,title))
        if isinstance(creator,list): creator=' '.join(map(str,creator))
        ts=sim(item['title'],str(title)); ascore=sim(item.get('author',''),str(creator)) if item.get('author') else 0
        score=ts*.85+ascore*.15
        if norm(item['title'])==norm(str(title)):score=max(score,.96)
        scored.append((score,d,str(title)))
    scored.sort(key=lambda x:x[0],reverse=True)
    for score,d,title in scored:
        if score<.46: continue
        if publicish(d): return d.get('identifier',''),title,score
    return '','',0.0

def choose(identifier):
    meta=getj('https://archive.org/metadata/'+urllib.parse.quote(identifier,safe=''))
    md=meta.get('metadata',{})
    if str(md.get('is_dark','')).lower() in ('true','1'): return None
    choices=[]
    for f in meta.get('files',[]):
        if not isinstance(f,dict): continue
        n=str(f.get('name','')); low=n.casefold(); fmt=str(f.get('format','')).casefold()
        try:size=int(f.get('size') or 0)
        except:size=0
        if size and size>MAX: continue
        if low.endswith('_djvu.txt') or low.endswith('.txt') or 'full text' in fmt: rank=0; ext='.txt'
        elif low.endswith('.epub') or 'epub' in fmt: rank=1; ext='.epub'
        elif low.endswith('.pdf') or 'pdf' in fmt: rank=2; ext='.pdf'
        else: continue
        if size and size<1500: continue
        choices.append((rank,size or MAX,n,ext))
    if not choices:return None
    choices.sort(key=lambda x:(x[0],x[1]))
    _,size,n,ext=choices[0]
    return f'https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(n)}',size,ext

def download(url,dest):
    dest.parent.mkdir(parents=True,exist_ok=True); tmp=dest.with_suffix(dest.suffix+'.part'); h=hashlib.sha256(); total=0
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    try:
        with urllib.request.urlopen(req,timeout=90) as r,tmp.open('wb') as f:
            cl=r.headers.get('Content-Length')
            if cl and int(cl)>MAX: raise ValueError('oversized')
            while True:
                b=r.read(1024*1024)
                if not b:break
                total+=len(b)
                if total>MAX:raise ValueError('oversized')
                h.update(b);f.write(b)
        tmp.replace(dest);return total,h.hexdigest()
    except:
        tmp.unlink(missing_ok=True);raise

def main():
    manifest=json.loads(MAN.read_text(encoding='utf-8'))
    idx=json.loads(INDEX.read_text(encoding='utf-8')) if INDEX.exists() else {'schema':'ingested-library-v2','items':[]}
    items=idx.get('items',[]); existing={str(x.get('workId')) for x in items if isinstance(x,dict)}
    outcomes=[];success=0
    for c in manifest['candidates']:
        if success>=TARGET: break
        if c['workId'] in existing:
            outcomes.append({**c,'status':'already-present'});continue
        try:
            ident,rt,score=search(c)
            if not ident:
                outcomes.append({**c,'status':'unresolved'});continue
            chosen=choose(ident)
            if not chosen:
                outcomes.append({**c,'status':'no-file','archiveIdentifier':ident,'matchedTitle':rt});continue
            url,_,ext=chosen
            seed=hashlib.sha1(url.encode()).hexdigest()[:12]
            rel=Path('library/works')/c['workId']/'editions'/f'ed-{seed}'/f'original{ext}'
            size,sha=download(url,ROOT/rel)
            record={'id':f"{c['workId']}:ed-{seed}",'workId':c['workId'],'editionId':f'ed-{seed}','titleOriginal':c['title'],'author':c.get('author',''),'language':'','subjects':['المصادر والدراسات'],'siteSections':['المصادر والدراسات'],'format':ext.lstrip('.'),'mimeType':{'txt':'text/plain','epub':'application/epub+zip','pdf':'application/pdf'}[ext.lstrip('.')],'size':size,'sha256':sha,'localUrl':'/'+rel.as_posix(),'readerUrl':'/'+rel.as_posix(),'sourceUrl':url,'archiveIdentifier':ident,'capabilities':{'readable':True,'searchable':ext=='.txt','listenable':ext=='.txt','watchable':False},'searchMode':'fulltext-browser' if ext=='.txt' else 'reader-search','listenMode':'browser-tts' if ext=='.txt' else 'none','watchMode':'none','publishedAsset':True,'recoveredAt':now()}
            items.append(record);existing.add(c['workId']);success+=1
            outcomes.append({**c,'status':'downloaded','archiveIdentifier':ident,'matchedTitle':rt,'score':score,'size':size,'sha256':sha,'localUrl':'/'+rel.as_posix()})
            print(f'downloaded {success}/{TARGET}: {c["title"]}',flush=True)
        except Exception as e:
            outcomes.append({**c,'status':'failed','error':str(e)[:300]})
    idx['items']=items;idx['count']=len(items);idx['currentBatchCount']=success;idx['generatedAt']=now();INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.write_text(json.dumps({'generatedAt':now(),'target':TARGET,'downloaded':success,'attempted':len(outcomes),'items':outcomes},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if success<TARGET: raise SystemExit(f'only {success} of {TARGET} downloaded')
if __name__=='__main__':main()
