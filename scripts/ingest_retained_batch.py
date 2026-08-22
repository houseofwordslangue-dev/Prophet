#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
import hashlib, json, os, pathlib, urllib.parse, urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data' / 'recovery' / 'retained_batch_2.json'
INDEX = ROOT / 'data' / 'ingested_library.json'
REPORT = ROOT / 'data' / 'recovery' / 'retained_batch_2_report.json'
MAX = int(os.getenv('RECOVERY_MAX_FILE_BYTES', str(95*1024*1024)))
UA = {'User-Agent':'ProphetLibraryRecovery/2.0'}

def http_json(url):
    req=urllib.request.Request(url,headers={**UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode('utf-8','replace'))

def choose_archive(identifier):
    meta=http_json('https://archive.org/metadata/'+urllib.parse.quote(identifier,safe=''))
    choices=[]
    for f in meta.get('files',[]):
        name=str(f.get('name',''))
        try: size=int(f.get('size') or 0)
        except: size=0
        if not name or (size and size>MAX): continue
        low=name.lower(); fmt=str(f.get('format','')).lower()
        if low.endswith('_djvu.txt') or low.endswith('.txt') or 'full text' in fmt: rank=0
        elif low.endswith('.epub') or 'epub' in fmt: rank=1
        elif low.endswith('.pdf') or 'pdf' in fmt: rank=2
        else: continue
        if size and size<1024: continue
        choices.append((rank,size or MAX,name))
    if not choices: raise RuntimeError('no suitable downloadable derivative')
    choices.sort(key=lambda x:(x[0],x[1]))
    name=choices[0][2]
    return 'https://archive.org/download/'+urllib.parse.quote(identifier,safe='')+'/'+urllib.parse.quote(name), name

def resolve(url):
    p=urllib.parse.urlparse(url)
    if p.netloc.endswith('archive.org') and '/details/' in p.path:
        ident=p.path.split('/details/',1)[1].split('/',1)[0]
        return choose_archive(ident)[0]
    return url

def ext_for(url, ctype=''):
    p=urllib.parse.urlparse(url).path.lower()
    for e in ('.pdf','.epub','.txt','.html','.htm'):
        if p.endswith(e): return e
    if 'pdf' in ctype: return '.pdf'
    if 'epub' in ctype: return '.epub'
    if 'text/plain' in ctype: return '.txt'
    return '.bin'

def download(url,dest):
    req=urllib.request.Request(url,headers=UA)
    h=hashlib.sha256(); total=0
    tmp=dest.with_suffix(dest.suffix+'.part'); tmp.parent.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(req,timeout=90) as r, tmp.open('wb') as f:
        ctype=r.headers.get('Content-Type','')
        declared=r.headers.get('Content-Length')
        if declared and int(declared)>MAX: raise RuntimeError('oversized')
        while True:
            b=r.read(1024*1024)
            if not b: break
            total+=len(b)
            if total>MAX: raise RuntimeError('oversized')
            h.update(b); f.write(b)
    tmp.replace(dest)
    return total,h.hexdigest(),ctype

def main():
    batch=json.loads(MANIFEST.read_text(encoding='utf-8'))['items']
    idx=json.loads(INDEX.read_text(encoding='utf-8')) if INDEX.exists() else {'schema':'ingested-library-v2','items':[]}
    items=idx.setdefault('items',[])
    existing={x.get('workId'):x for x in items if isinstance(x,dict)}
    report=[]
    for rec in batch:
        try:
            source=resolve(rec['url'])
            e=ext_for(source)
            seed=hashlib.sha1(source.encode()).hexdigest()[:12]
            d=ROOT/'library'/'works'/rec['workId']/'editions'/('ed-'+seed)
            dest=d/('original'+e)
            size,sha,ctype=download(source,dest)
            if e=='.bin':
                e=ext_for(source,ctype)
                if e!='.bin':
                    new=d/('original'+e); dest.rename(new); dest=new
            local='/' + str(dest.relative_to(ROOT)).replace('\\','/')
            fmt=dest.suffix.lstrip('.')
            record={
              'id':f"{rec['workId']}:ed-{sha[:12]}", 'workId':rec['workId'], 'editionId':f"ed-{sha[:12]}",
              'titleOriginal':rec['title'], 'author':rec['author'], 'language':'ar',
              'subjects':['المصادر والدراسات'], 'siteSections':['المصادر والدراسات'],
              'format':fmt, 'mimeType':{'pdf':'application/pdf','txt':'text/plain','epub':'application/epub+zip','html':'text/html','htm':'text/html'}.get(fmt,'application/octet-stream'),
              'size':size, 'sha256':sha, 'localUrl':local, 'readerUrl':local,
              'sourceUrl':rec['url'], 'resolvedDownloadUrl':source,
              'capabilities':{'readable':fmt in ('pdf','txt','epub','html','htm'),'searchable':fmt in ('txt','html','htm','pdf'),'listenable':fmt in ('txt','html','htm'),'watchable':False},
              'searchMode':'reader-search', 'listenMode':'browser-tts' if fmt in ('txt','html','htm') else 'none', 'watchMode':'none',
              'publishedAsset':True, 'recoveryStatus':'retained-source-batch-2'
            }
            if rec['workId'] in existing:
                old=existing[rec['workId']]; items[items.index(old)]=record
            else: items.append(record)
            existing[rec['workId']]=record
            report.append({'workId':rec['workId'],'title':rec['title'],'status':'downloaded','size':size,'sha256':sha,'localUrl':local})
        except Exception as e:
            report.append({'workId':rec['workId'],'title':rec['title'],'status':'failed','error':str(e)[:300]})
    idx['count']=len(items); idx['currentBatchCount']=sum(1 for x in report if x['status']=='downloaded'); idx['generatedAt']=datetime.now(timezone.utc).isoformat()
    INDEX.write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    REPORT.write_text(json.dumps({'generatedAt':datetime.now(timezone.utc).isoformat(),'requested':len(batch),'downloaded':sum(1 for x in report if x['status']=='downloaded'),'failed':sum(1 for x in report if x['status']=='failed'),'items':report},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
