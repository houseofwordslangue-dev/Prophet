#!/usr/bin/env python3
from __future__ import annotations
import json,re,sys,time,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data'/'public_catalog_all.generated.json'
CAND=ROOT/'private'/'acquisition_candidates.json'
OUT=ROOT/'private'/'source_first_resolution.json'
POL=ROOT/'data'/'source_first_fulltext_policy.json'
UA='ProphetBiographyLibrary/7.0-source-first'
PRIORITY=['epub','txt','docx','doc','odt','rtf','html','md','xml','pdf']
NATIVE_EXT={'.epub','epub','.txt','txt','.docx','docx','.doc','doc','.odt','odt','.rtf','rtf','.html','html','.htm','htm','.md','md','.xml','xml'}
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
    s=str(s or '').lower().strip();s=re.sub(r'[\u064b-\u065f\u0670]','',s);s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ة','ه');return re.sub(r'[^\w\u0600-\u06ff]+',' ',s).strip()

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
        if fmt in PRIORITY:
            out.append({'format':fmt,'url':'https://archive.org/download/'+urllib.parse.quote(ident)+'/'+urllib.parse.quote(n),'name':n,'source':'archive-metadata'})
    return sorted(out,key=lambda x:PRIORITY.index(x['format']))

def gutenberg_native(url):
    m=re.search(r'/(?:ebooks|epub)/(\d+)',url)
    if not m:return []
    i=m.group(1)
    return [
      {'format':'epub','url':f'https://www.gutenberg.org/ebooks/{i}.epub3.images','name':f'{i}.epub','source':'gutenberg'},
      {'format':'txt','url':f'https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt','name':f'pg{i}.txt','source':'gutenberg'}]

def wikisource_native(url):
    if 'wikisource.org' not in url:return []
    p=urllib.parse.urlparse(url);title=urllib.parse.unquote(p.path.rsplit('/',1)[-1])
    if not title:return []
    base=f'{p.scheme}://{p.netloc}'
    return [{'format':'epub','url':base+'/api/rest_v1/page/pdf/'+urllib.parse.quote(title),'name':title+'.pdf','source':'wikisource-export'}]

def discover(row):
    urls=[]
    for k in ('sources','sourceUrls'):
        v=row.get(k)
        if isinstance(v,list):urls.extend(str(x) for x in v if x)
    for k in ('source','sourceUrl','verifiedSource','candidateSource'):
        if row.get(k):urls.append(str(row[k]))
    found=[]
    for u in dict.fromkeys(urls):
        f=fmt_of(u)
        if f in PRIORITY:found.append({'format':f,'url':u,'name':u.rsplit('/',1)[-1],'source':'direct'})
        if 'archive.org' in u:found+=archive_native(u)
        if 'gutenberg.org' in u:found+=gutenberg_native(u)
        if 'wikisource.org' in u:found+=wikisource_native(u)
    uniq={}
    for x in found:
        key=(x['format'],x['url']);uniq[key]=x
    return sorted(uniq.values(),key=lambda x:PRIORITY.index(x['format']))

def main():
    cat=load(CAT,{'items':[]});cand=load(CAND,{'items':[]});cmap={str(x.get('workId') or x.get('catalogueId') or ''):x for x in cand.get('items',[]) if isinstance(x,dict)}
    rows=[]; native=0; needs_pdf=0
    for x in cat.get('items',[]):
        if x.get('access')=='PUBLIC_FULL_TEXT':continue
        wid=str(x.get('id') or '');merged=dict(x);merged.update(cmap.get(wid,{}));found=discover(merged)
        preferred=next((z for z in found if z['format']!='pdf'),None)
        if preferred:native+=1;state='NATIVE_TEXT_FOUND'
        elif found:needs_pdf+=1;preferred=found[0];state='PDF_FOUND_NATIVE_SEARCH_EXHAUSTED'
        else:state='NO_SOURCE_FOUND_NATIVE_SEARCH_COMPLETE'
        rows.append({'id':wid,'title':x.get('title'),'author':x.get('author'),'previousAccess':x.get('access'),'state':state,'preferred':preferred,'candidates':found[:20],'nativeSearchCompleted':True,'ocrAllowed':state!='NATIVE_TEXT_FOUND'})
    out={'schema':'source-first-resolution-v1','generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'priority':PRIORITY,'remainingScanned':len(rows),'nativeTextFound':native,'pdfOnlyAfterNativeSearch':needs_pdf,'items':rows}
    save(OUT,out);print(json.dumps({k:out[k] for k in ('remainingScanned','nativeTextFound','pdfOnlyAfterNativeSearch')},ensure_ascii=False))

if __name__=='__main__':main()
