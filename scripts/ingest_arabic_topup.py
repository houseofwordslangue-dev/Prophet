#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import base64,gzip,hashlib,json,os,re,unicodedata,urllib.parse,urllib.request
from pathlib import Path
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'data/recovery/arabic_topup_batch.json'
CAT=ROOT/'data/catalogue/professional_catalogue.json.gz.b64'
INDEX=ROOT/'data/ingested_library.json'
REPORT=ROOT/'data/recovery/arabic_topup_batch_report.json'
MAX=int(os.getenv('ARABIC_TOPUP_MAX_FILE_BYTES',str(95*1024*1024)))
TARGET=int(os.getenv('ARABIC_TOPUP_TARGET','49'))
UA='ProphetArabicTopup/1.0'

def now(): return datetime.now(timezone.utc).isoformat()
def getj(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode('utf-8','replace'))
def norm(s):
    s=unicodedata.normalize('NFKD',s or '')
    s=''.join(c for c in s if not unicodedata.combining(c)).casefold().replace('ـ','')
    return ' '.join(re.sub(r'[^\w\u0600-\u06ff]+',' ',s).split())
def sim(a,b):
    A={x for x in norm(a).split() if len(x)>1};B={x for x in norm(b).split() if len(x)>1}
    return len(A&B)/len(A|B) if A and B else 0.0
def load_catalogue():
    raw=base64.b64decode(''.join(CAT.read_text(encoding='utf-8').split()))
    data=json.loads(gzip.decompress(raw).decode('utf-8'))
    out=[]
    def walk(x):
        if isinstance(x,dict):
            if x.get('id') and (x.get('titleAr') or x.get('originalTitle')):out.append(x)
            for v in x.values():walk(v)
        elif isinstance(x,list):
            for v in x:walk(v)
    walk(data);return out

def years(s):return [int(x) for x in re.findall(r'(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)',str(s or ''))]
def catalogue_safe(r):
    rights=' '.join(str(r.get(k,'')) for k in ('rightsStatus','publicNotes','availabilityStatus')).casefold()
    if any(x in rights for x in ('public domain','public-domain','cc0','creative commons','open license','open-license')):return True
    if r.get('eligibleForFullTextCopy') is True:return True
    yd=years(r.get('authorDates'))
    if yd and max(yd)<=1955:return True
    yw=years(r.get('workDate'))
    if yw and min(yw)<=1850:return True
    return False

def ia_publicish(md):
    txt=' '.join(str(md.get(k,'')) for k in ('rights','licenseurl','description')).casefold()
    if any(x in txt for x in ('public domain','creativecommons.org/publicdomain','cc0','no known copyright')):return True
    yy=years(md.get('date') or md.get('year'))
    return bool(yy and min(yy)<=1930)

def archive_search(title,author):
    queries=[f'title:("{title}") AND creator:("{author}")' if author else f'title:("{title}")', f'"{title}" {author}'.strip(), title]
    best=[]
    for q in queries:
        params=[('q',q),('fl[]','identifier'),('fl[]','title'),('fl[]','creator'),('fl[]','date'),('fl[]','year'),('fl[]','rights'),('fl[]','licenseurl'),('rows','50'),('output','json'),('sort[]','downloads desc')]
        try:docs=getj('https://archive.org/advancedsearch.php?'+urllib.parse.urlencode(params)).get('response',{}).get('docs',[])
        except Exception:continue
        for d in docs:
            dt=d.get('title','');cr=d.get('creator','')
            if isinstance(dt,list):dt=' '.join(map(str,dt))
            if isinstance(cr,list):cr=' '.join(map(str,cr))
            ts=sim(title,str(dt));a=sim(author,str(cr)) if author else 0
            score=ts*.9+a*.1
            if norm(title)==norm(str(dt)):score=max(score,.98)
            best.append((score,d,str(dt)))
        if best:break
    best.sort(key=lambda x:x[0],reverse=True)
    for score,d,dt in best:
        if score>=.42:return str(d.get('identifier','')),dt,score,d
    return '','',0.0,{}

def choose(identifier,work_safe,search_doc=None):
    meta=getj('https://archive.org/metadata/'+urllib.parse.quote(identifier,safe=''))
    md=meta.get('metadata',{}) if isinstance(meta,dict) else {}
    if str(md.get('is_dark','')).lower() in ('true','1'):return None
    public=ia_publicish(md) or ia_publicish(search_doc or {})
    choices=[]
    for f in meta.get('files',[]):
        if not isinstance(f,dict):continue
        n=str(f.get('name',''));low=n.casefold();fmt=str(f.get('format','')).casefold()
        try:size=int(f.get('size') or 0)
        except:size=0
        if size and size>MAX:continue
        if low.endswith('_djvu.txt') or low.endswith('.txt') or 'full text' in fmt:rank=0;ext='.txt'
        elif low.endswith('.epub') or 'epub' in fmt:rank=1;ext='.epub'
        elif (low.endswith('.pdf') or 'pdf' in fmt) and public:rank=2;ext='.pdf'
        else:continue
        if size and size<1500:continue
        if not (work_safe or public):continue
        choices.append((rank,size or MAX,n,ext))
    if not choices:return None
    choices.sort(key=lambda x:(x[0],x[1]));_,size,n,ext=choices[0]
    return f'https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(n)}',ext

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

def ingest(c,identifier,matched,score,doc,work_safe):
    chosen=choose(identifier,work_safe,doc)
    if not chosen:return {**c,'status':'no-file','archiveIdentifier':identifier,'matchedTitle':matched}
    url,ext=chosen;seed=hashlib.sha1(url.encode()).hexdigest()[:12]
    rel=Path('library/works')/c['workId']/'editions'/f'ed-{seed}'/f'original{ext}'
    size,sha=download(url,ROOT/rel)
    return {**c,'status':'downloaded','archiveIdentifier':identifier,'matchedTitle':matched,'score':score,'sourceUrl':url,'localUrl':'/'+rel.as_posix(),'size':size,'sha256':sha,'ext':ext,'editionId':f'ed-{seed}'}

def main():
    cfg=json.loads(CFG.read_text(encoding='utf-8'));catalogue=load_catalogue()
    idx=json.loads(INDEX.read_text(encoding='utf-8'));items=idx.get('items',[]);existing={str(x.get('workId')) for x in items if isinstance(x,dict)}
    recs=[];success=0
    # exact retained identifiers first
    for c in cfg.get('exactSeeds',[]):
        if success>=TARGET:break
        if c['workId'] in existing:continue
        try:o=ingest(c,c['archiveIdentifier'],c['title'],1.0,{},True)
        except Exception as e:o={**c,'status':'failed','error':str(e)[:240]}
        recs.append(o)
        if o.get('status')=='downloaded':success+=1;existing.add(c['workId'])
    # then Arabic catalogue records, safest/oldest-looking first
    candidates=[]
    for r in catalogue:
        title=str(r.get('titleAr') or '').strip();author=str(r.get('authorAr') or '').strip()
        if not title or not re.search(r'[\u0600-\u06ff]',title):continue
        wid=str(r.get('id') or '')
        if not wid or wid in existing:continue
        if str(r.get('recordLevel','work')).startswith(('institution','media','web')):continue
        if 'rights-restricted' in str(r.get('rightsStatus','')).casefold():continue
        safe=catalogue_safe(r)
        # prioritize records known safe, then older classical work records
        candidates.append((0 if safe else 1,wid,title,author,r,safe))
    candidates.sort(key=lambda x:(x[0],int(x[4].get('entryNumber') or 999999)))
    for _,wid,title,author,r,safe in candidates:
        if success>=TARGET:break
        c={'workId':wid,'title':title,'author':author}
        try:
            ident,matched,score,doc=archive_search(title,author)
            if not ident:o={**c,'status':'unresolved'}
            else:o=ingest(c,ident,matched,score,doc,safe)
        except Exception as e:o={**c,'status':'failed','error':str(e)[:240]}
        recs.append(o)
        if o.get('status')=='downloaded':
            success+=1;existing.add(wid)
            ext=o.pop('ext');ed=o.pop('editionId')
            mime={'txt':'text/plain','epub':'application/epub+zip','pdf':'application/pdf'}[ext.lstrip('.')]
            items.append({'id':f'{wid}:{ed}','workId':wid,'editionId':ed,'titleOriginal':title,'titleAr':title,'author':author,'language':'ar','subjects':['المصادر والدراسات'],'siteSections':['المصادر والدراسات'],'format':ext.lstrip('.'),'mimeType':mime,'size':o['size'],'sha256':o['sha256'],'localUrl':o['localUrl'],'readerUrl':o['localUrl'],'sourceUrl':o['sourceUrl'],'archiveIdentifier':o['archiveIdentifier'],'capabilities':{'readable':True,'searchable':ext=='.txt','listenable':ext=='.txt','watchable':False},'searchMode':'fulltext-browser' if ext=='.txt' else 'reader-search','listenMode':'browser-tts' if ext=='.txt' else 'none','watchMode':'none','publishedAsset':True,'recoveredAt':now()})
            print(f'downloaded topup {success}/{TARGET}: {title}',flush=True)
    # exact-seed downloaded records need index entries too
    indexed={str(x.get('workId')) for x in items if isinstance(x,dict)}
    for o in recs:
        if o.get('status')!='downloaded' or o['workId'] in indexed:continue
        ext=o.pop('ext');ed=o.pop('editionId');wid=o['workId'];title=o['title'];author=o.get('author','')
        mime={'txt':'text/plain','epub':'application/epub+zip','pdf':'application/pdf'}[ext.lstrip('.')]
        items.append({'id':f'{wid}:{ed}','workId':wid,'editionId':ed,'titleOriginal':title,'titleAr':title,'author':author,'language':'ar','subjects':['المصادر والدراسات'],'siteSections':['المصادر والدراسات'],'format':ext.lstrip('.'),'mimeType':mime,'size':o['size'],'sha256':o['sha256'],'localUrl':o['localUrl'],'readerUrl':o['localUrl'],'sourceUrl':o['sourceUrl'],'archiveIdentifier':o['archiveIdentifier'],'capabilities':{'readable':True,'searchable':ext=='.txt','listenable':ext=='.txt','watchable':False},'searchMode':'fulltext-browser' if ext=='.txt' else 'reader-search','listenMode':'browser-tts' if ext=='.txt' else 'none','watchMode':'none','publishedAsset':True,'recoveredAt':now()});indexed.add(wid)
    idx['items']=items;idx['count']=len(items);idx['currentBatchCount']=success;idx['generatedAt']=now();INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.write_text(json.dumps({'generatedAt':now(),'target':TARGET,'downloaded':success,'attempted':len(recs),'items':recs},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
