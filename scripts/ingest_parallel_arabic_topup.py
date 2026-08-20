#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures,hashlib,json,os,re,unicodedata,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
INDEX=ROOT/'data/ingested_library.json'
REPORT=ROOT/'data/recovery/parallel_arabic_topup_report.json'
CFG=ROOT/'data/recovery/arabic_topup_batch.json'
MAX=int(os.getenv('PARALLEL_TOPUP_MAX_FILE_BYTES',str(95*1024*1024)))
TARGET=int(os.getenv('PARALLEL_TOPUP_TARGET','49'))
UA='ProphetParallelArabicTopup/1.0'

def now(): return datetime.now(timezone.utc).isoformat()
def getj(url,timeout=45):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=timeout) as r:return json.loads(r.read().decode('utf-8','replace'))
def norm(s):
    s=unicodedata.normalize('NFKD',s or '')
    s=''.join(c for c in s if not unicodedata.combining(c)).casefold().replace('ـ','')
    return ' '.join(re.sub(r'[^\w\u0600-\u06ff]+',' ',s).split())
def sim(a,b):
    A={x for x in norm(a).split() if len(x)>1};B={x for x in norm(b).split() if len(x)>1}
    return len(A&B)/len(A|B) if A and B else 0.0
def years(s):return [int(x) for x in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)',str(s or ''))]
def publicish(d):
    txt=' '.join(str(d.get(k,'')) for k in ('rights','licenseurl','description')).casefold()
    if any(x in txt for x in ('public domain','public-domain','creativecommons.org/publicdomain','cc0','no known copyright')):return True
    yy=years(d.get('date') or d.get('year'))
    return bool(yy and min(yy)<=1930)
def load_chunks():
    out=[]
    for p in sorted((ROOT/'data/catalogue').glob('chunk-*.json')):
        d=json.loads(p.read_text(encoding='utf-8'))
        for a in d.get('items',[]):
            if not isinstance(a,list) or len(a)<15:continue
            out.append({'workId':str(a[0]),'entryNumber':int(a[1]),'category':str(a[2]),'title':str(a[3] or ''),'titleRomanized':str(a[4] or ''),'author':str(a[5] or ''),'authorRomanized':str(a[6] or ''),'kind':str(a[7] or ''),'rightsStatus':str(a[8] or ''),'verificationStatus':str(a[9] or ''),'ingestionStatus':str(a[10] or ''),'availability':str(a[11] or ''),'exactSourceUrl':str(a[12] or ''),'notes':str(a[13] or ''),'localStatus':str(a[14] or '')})
    return out

def archive_id(url):
    m=re.search(r'archive\.org/details/([^/?#]+)',url or '')
    return urllib.parse.unquote(m.group(1)) if m else ''
def safe_exact(c):
    u=c.get('exactSourceUrl','');r=(c.get('rightsStatus','')+' '+c.get('notes','')+' '+c.get('localStatus','')).casefold()
    if not u:return False
    if 'rights-restricted' in r:return False
    return any(h in u for h in ('archive.org/details/','gutenberg.org/','upload.wikimedia.org/','mc.dlib.nyu.edu/files/books/'))
def search_one(c):
    title=c['title'];author=c.get('author','')
    queries=[f'title:("{title}") AND creator:("{author}")' if author else f'title:("{title}")',f'"{title}" {author}'.strip(),title]
    best=[]
    for q in queries:
        params=[('q',q),('fl[]','identifier'),('fl[]','title'),('fl[]','creator'),('fl[]','date'),('fl[]','year'),('fl[]','rights'),('fl[]','licenseurl'),('fl[]','description'),('rows','30'),('output','json'),('sort[]','downloads desc')]
        try:docs=getj('https://archive.org/advancedsearch.php?'+urllib.parse.urlencode(params)).get('response',{}).get('docs',[])
        except Exception:continue
        for d in docs:
            dt=d.get('title','');cr=d.get('creator','')
            if isinstance(dt,list):dt=' '.join(map(str,dt))
            if isinstance(cr,list):cr=' '.join(map(str,cr))
            score=sim(title,str(dt))*.9+(sim(author,str(cr))*.1 if author else 0)
            if norm(title)==norm(str(dt)):score=max(score,.98)
            if score>=.40 and publicish(d):best.append((score,str(d.get('identifier','')),str(dt),d))
        if best:break
    if not best:return None
    best.sort(reverse=True,key=lambda x:x[0]);score,ident,dt,d=best[0]
    return {'identifier':ident,'matchedTitle':dt,'score':score,'doc':d}
def choose_archive(identifier,allow_text_only=False):
    meta=getj('https://archive.org/metadata/'+urllib.parse.quote(identifier,safe=''),60);md=meta.get('metadata',{})
    if str(md.get('is_dark','')).lower() in ('true','1'):return None
    pub=publicish(md)
    choices=[]
    for f in meta.get('files',[]):
        if not isinstance(f,dict):continue
        n=str(f.get('name',''));low=n.casefold();fmt=str(f.get('format','')).casefold()
        try:size=int(f.get('size') or 0)
        except:size=0
        if size and size>MAX:continue
        if low.endswith('_djvu.txt') or low.endswith('.txt') or 'full text' in fmt:rank=0;ext='.txt'
        elif low.endswith('.epub') or 'epub' in fmt:rank=1;ext='.epub'
        elif (low.endswith('.pdf') or 'pdf' in fmt) and pub and not allow_text_only:rank=2;ext='.pdf'
        else:continue
        if size and size<1500:continue
        choices.append((rank,size or MAX,n,ext))
    if not choices:return None
    choices.sort(key=lambda x:(x[0],x[1]));_,_,n,ext=choices[0]
    return f'https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(n)}',ext

def direct_source(c):
    u=c.get('exactSourceUrl','')
    ident=archive_id(u)
    if ident:
        ch=choose_archive(ident,allow_text_only=True)
        return (ch[0],ch[1],ident) if ch else None
    if re.search(r'\.(?:txt|pdf|epub)(?:$|[?#])',u,re.I):
        ext=Path(urllib.parse.urlparse(u).path).suffix.lower() or '.bin';return u,ext,''
    return None

def download(url,dest):
    dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix(dest.suffix+'.part');h=hashlib.sha256();total=0
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    try:
        with urllib.request.urlopen(req,timeout=120) as r,tmp.open('wb') as f:
            cl=r.headers.get('Content-Length')
            if cl and int(cl)>MAX:raise ValueError('oversized')
            while True:
                b=r.read(1024*1024)
                if not b:break
                total+=len(b)
                if total>MAX:raise ValueError('oversized')
                h.update(b);f.write(b)
        tmp.replace(dest);return total,h.hexdigest()
    except:
        tmp.unlink(missing_ok=True);raise

def record_asset(c,url,ext,ident=''):
    seed=hashlib.sha1(url.encode()).hexdigest()[:12];rel=Path('library/works')/c['workId']/'editions'/f'ed-{seed}'/f'original{ext}'
    size,sha=download(url,ROOT/rel)
    mime={'.txt':'text/plain','.epub':'application/epub+zip','.pdf':'application/pdf'}.get(ext,'application/octet-stream')
    return {'id':f"{c['workId']}:ed-{seed}",'workId':c['workId'],'editionId':f'ed-{seed}','titleOriginal':c['title'],'titleAr':c['title'],'author':c.get('author',''),'language':'ar','subjects':['المصادر والدراسات'],'siteSections':['المصادر والدراسات'],'format':ext.lstrip('.'),'mimeType':mime,'size':size,'sha256':sha,'localUrl':'/'+rel.as_posix(),'readerUrl':'/'+rel.as_posix(),'sourceUrl':url,'archiveIdentifier':ident or None,'capabilities':{'readable':True,'searchable':ext=='.txt','listenable':ext=='.txt','watchable':False},'searchMode':'fulltext-browser' if ext=='.txt' else 'reader-search','listenMode':'browser-tts' if ext=='.txt' else 'none','watchMode':'none','publishedAsset':True,'recoveredAt':now()}

def main():
    idx=json.loads(INDEX.read_text(encoding='utf-8'));items=idx.get('items',[]);existing={str(x.get('workId')) for x in items if isinstance(x,dict)}
    chunks=load_chunks();outcomes=[];success=0
    # exact retained source URLs first
    for c in chunks:
        if success>=TARGET:break
        if c['workId'] in existing or not safe_exact(c):continue
        try:
            src=direct_source(c)
            if not src:continue
            url,ext,ident=src;asset=record_asset(c,url,ext,ident);items.append(asset);existing.add(c['workId']);success+=1;outcomes.append({'workId':c['workId'],'title':c['title'],'status':'downloaded','source':'exact','localUrl':asset['localUrl'],'size':asset['size']})
            print(f'exact {success}/{TARGET}: {c["title"]}',flush=True)
        except Exception as e:outcomes.append({'workId':c['workId'],'title':c['title'],'status':'failed-exact','error':str(e)[:200]})
    # parallel Arabic Archive.org resolution for unresolved work records
    candidates=[c for c in chunks if c['workId'] not in existing and c['title'] and re.search(r'[\u0600-\u06ff]',c['title']) and c['kind'] not in ('institution','media-resource','web-resource') and 'rights-restricted' not in (c['rightsStatus']+' '+c['localStatus']).casefold()]
    candidates.sort(key=lambda c:c['entryNumber'])
    resolved=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        futs={ex.submit(search_one,c):c for c in candidates[:420]}
        for fut in concurrent.futures.as_completed(futs):
            c=futs[fut]
            try:r=fut.result()
            except Exception:r=None
            if r:resolved.append((c,r))
    resolved.sort(key=lambda x:(-x[1]['score'],x[0]['entryNumber']))
    for c,r in resolved:
        if success>=TARGET:break
        if c['workId'] in existing:continue
        try:
            ch=choose_archive(r['identifier'])
            if not ch:outcomes.append({'workId':c['workId'],'title':c['title'],'status':'no-file','archiveIdentifier':r['identifier']});continue
            url,ext=ch;asset=record_asset(c,url,ext,r['identifier']);items.append(asset);existing.add(c['workId']);success+=1;outcomes.append({'workId':c['workId'],'title':c['title'],'status':'downloaded','source':'archive-search','archiveIdentifier':r['identifier'],'matchedTitle':r['matchedTitle'],'score':r['score'],'localUrl':asset['localUrl'],'size':asset['size']})
            print(f'search {success}/{TARGET}: {c["title"]}',flush=True)
        except Exception as e:outcomes.append({'workId':c['workId'],'title':c['title'],'status':'failed-search','error':str(e)[:200]})
    idx['items']=items;idx['count']=len(items);idx['currentBatchCount']=success;idx['generatedAt']=now();INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.write_text(json.dumps({'generatedAt':now(),'target':TARGET,'downloaded':success,'resolvedCandidates':len(resolved),'items':outcomes},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'downloaded':success,'target':TARGET,'resolvedCandidates':len(resolved)},ensure_ascii=False))
if __name__=='__main__':main()
