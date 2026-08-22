#!/usr/bin/env python3
from __future__ import annotations
import json,re,time,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data'/'public_catalog_all.generated.json'
CAND=ROOT/'private'/'acquisition_candidates.json'
DRIVE=ROOT/'data'/'drive_native_assets_20260822.json'
OUT=ROOT/'private'/'source_first_resolution.json'
UA='ProphetBiographyLibrary/7.1-source-first'
PRIORITY=['epub','txt','docx','doc','odt','rtf','html','md','xml','pdf']
ALLOW={'archive.org','www.archive.org','gutenberg.org','www.gutenberg.org','api.github.com','raw.githubusercontent.com','upload.wikimedia.org','commons.wikimedia.org','wikisource.org','en.wikisource.org','fr.wikisource.org','ar.wikisource.org'}

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def host_ok(url):
    try:return urllib.parse.urlparse(url).hostname in ALLOW
    except Exception:return False

def get_json(url):
    if not host_ok(url): raise RuntimeError('domain-not-allowlisted')
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)

def normalize(s):
    s=str(s or '').lower().strip();s=re.sub(r'[\u064b-\u065f\u0670]','',s);s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ة','ه');s=re.sub(r'\b(المجلد|الجزء|volume|vol|part|cover)\b.*$','',s);return re.sub(r'[^\w\u0600-\u06ff]+',' ',s).strip()

def fmt_of(url,name=''):
    x=(name or urllib.parse.urlparse(url).path).lower()
    for f in PRIORITY:
        if x.endswith('.'+f):return f
    return ''

def archive_identifier(url):
    p=urllib.parse.urlparse(url).path.strip('/').split('/')
    if len(p)>=2 and p[0] in {'details','download','metadata'}:return p[1]
    return ''

def archive_native(url):
    ident=archive_identifier(url)
    if not ident:return []
    try:m=get_json('https://archive.org/metadata/'+urllib.parse.quote(ident))
    except Exception:return []
    out=[]
    for f in m.get('files',[]):
        n=str(f.get('name') or '');fmt=fmt_of('',n)
        if fmt in PRIORITY:out.append({'format':fmt,'url':'https://archive.org/download/'+urllib.parse.quote(ident)+'/'+urllib.parse.quote(n),'name':n,'source':'archive-metadata'})
    return sorted(out,key=lambda x:PRIORITY.index(x['format']))

def gutenberg_native(url):
    m=re.search(r'/(?:ebooks|epub)/(\d+)',url)
    if not m:return []
    i=m.group(1)
    return [{'format':'epub','url':f'https://www.gutenberg.org/ebooks/{i}.epub3.images','name':f'{i}.epub','source':'gutenberg'},{'format':'txt','url':f'https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt','name':f'pg{i}.txt','source':'gutenberg'}]

def discover_web(row):
    urls=[]
    for k in ('sources','sourceUrls'):
        v=row.get(k)
        if isinstance(v,list):urls.extend(str(x) for x in v if x)
    for k in ('source','sourceUrl','verifiedSource','candidateSource','downloadUrl'):
        if row.get(k):urls.append(str(row[k]))
    found=[]
    for u in dict.fromkeys(urls):
        f=fmt_of(u)
        if f in PRIORITY:found.append({'format':f,'url':u,'name':u.rsplit('/',1)[-1],'source':'direct'})
        if 'archive.org' in u:found+=archive_native(u)
        if 'gutenberg.org' in u:found+=gutenberg_native(u)
    uniq={(x['format'],x['url']):x for x in found}
    return sorted(uniq.values(),key=lambda x:PRIORITY.index(x['format']))

def drive_map():
    d=load(DRIVE,{'items':[]});out={}
    for x in d.get('items',[]):
        if x.get('derivative'):continue
        n=normalize(x.get('title'))
        if not n:continue
        out.setdefault(n,[]).append({'format':x.get('format','epub'),'driveId':x.get('driveId'),'name':x.get('title'),'size':x.get('size'),'source':'google-drive-native','url':f"https://drive.google.com/file/d/{x.get('driveId')}/view"})
    return out

def main():
    cat=load(CAT,{'items':[]});cand=load(CAND,{'items':[]});cmap={str(x.get('workId') or x.get('catalogueId') or ''):x for x in cand.get('items',[]) if isinstance(x,dict)};dmap=drive_map()
    rows=[];native=0;drive_native=0;needs_pdf=0
    for x in cat.get('items',[]):
        if x.get('access')=='PUBLIC_FULL_TEXT':continue
        wid=str(x.get('id') or '');merged=dict(x);merged.update(cmap.get(wid,{}));found=[]
        title_key=normalize(x.get('title'))
        for k,v in dmap.items():
            if title_key and (title_key==k or title_key in k or k in title_key):found.extend(v)
        found+=discover_web(merged)
        uniq={}
        for z in found:
            key=(z.get('format'),z.get('driveId') or z.get('url'));uniq[key]=z
        found=sorted(uniq.values(),key=lambda z:PRIORITY.index(z.get('format')) if z.get('format') in PRIORITY else 99)
        preferred=next((z for z in found if z.get('format')!='pdf'),None)
        if preferred:
            native+=1;drive_native+=1 if preferred.get('source')=='google-drive-native' else 0;state='NATIVE_TEXT_FOUND'
        elif found:
            needs_pdf+=1;preferred=found[0];state='PDF_FOUND_NATIVE_SEARCH_EXHAUSTED'
        else:state='NO_SOURCE_FOUND_NATIVE_SEARCH_COMPLETE'
        rows.append({'id':wid,'title':x.get('title'),'author':x.get('author'),'previousAccess':x.get('access'),'state':state,'preferred':preferred,'candidates':found[:20],'nativeSearchCompleted':True,'ocrAllowed':state!='NATIVE_TEXT_FOUND'})
    out={'schema':'source-first-resolution-v2','generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'priority':PRIORITY,'remainingScanned':len(rows),'nativeTextFound':native,'driveNativeMatched':drive_native,'pdfOnlyAfterNativeSearch':needs_pdf,'items':rows}
    save(OUT,out);print(json.dumps({k:out[k] for k in ('remainingScanned','nativeTextFound','driveNativeMatched','pdfOnlyAfterNativeSearch')},ensure_ascii=False))

if __name__=='__main__':main()
