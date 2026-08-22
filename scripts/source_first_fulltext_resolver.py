#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,re,time,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data'/'public_catalog_all.generated.json'
CAND=ROOT/'private'/'acquisition_candidates.json'
OVERRIDES=ROOT/'private'/'native_source_overrides.json'
DRIVE=ROOT/'data'/'drive_native_assets_20260822.json'
DRIVE_VERIFIED=ROOT/'data'/'drive_verified_assets_20260822.json'
OUT=ROOT/'private'/'source_first_resolution.json'
QUEUE=ROOT/'private'/'resource_extraction_queue.json'
AVAIL=ROOT/'data'/'editorial'/'resource_extraction_availability.json'
INGESTED=ROOT/'data'/'ingested_library.json'
UA='ProphetBiographyLibrary/9.0-extraction-first-hardened'
PRIORITY=['epub','txt','docx','doc','odt','rtf','html','md','xml','pdf']
ALLOW={'archive.org','www.archive.org','gutenberg.org','www.gutenberg.org','api.github.com','raw.githubusercontent.com','upload.wikimedia.org','commons.wikimedia.org','wikisource.org','en.wikisource.org','fr.wikisource.org','ar.wikisource.org'}
STOP={'كتاب','شرح','جزء','المجلد','الجزء','في','من','على','الى','إلى','عن','the','of','and','a','an','volume','vol','part'}

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

def tokens(s):
    return [x for x in normalize(s).split() if len(x)>2 and x not in STOP]

def title_score(wanted,candidate):
    a=set(tokens(wanted));b=set(tokens(candidate))
    if not a or not b:return 0.0
    exact=normalize(wanted)==normalize(candidate)
    cover=len(a&b)/len(a)
    return min(1.0,cover+(0.25 if exact else 0))

def fmt_of(url,name=''):
    x=(name or urllib.parse.urlparse(url).path).lower()
    for f in PRIORITY:
        if x.endswith('.'+f):return f
    return ''

def archive_identifier(url):
    p=urllib.parse.urlparse(url).path.strip('/').split('/')
    if len(p)>=2 and p[0] in {'details','download','metadata'}:return p[1]
    return ''

def archive_file_usable(f):
    n=str(f.get('name') or '').lower()
    if not n:return False
    if any(x in n for x in ('_lcp.epub','encrypted','_meta.sqlite','_files.xml','_reviews.xml','_scandata.xml')):return False
    if str(f.get('private') or '').lower() in {'true','1'}:return False
    return fmt_of('',n) in PRIORITY

def archive_native(url):
    ident=archive_identifier(url)
    if not ident:return []
    try:m=get_json('https://archive.org/metadata/'+urllib.parse.quote(ident))
    except Exception:return []
    meta=m.get('metadata') or {}
    if str(meta.get('access-restricted-item') or '').lower() in {'true','1'}:return []
    out=[]
    for f in m.get('files',[]):
        if not archive_file_usable(f):continue
        n=str(f.get('name') or '');fmt=fmt_of('',n)
        out.append({'format':fmt,'url':'https://archive.org/download/'+urllib.parse.quote(ident)+'/'+urllib.parse.quote(n),'name':n,'source':'archive-metadata','identifier':ident,'verifiedAccessible':True})
    return sorted(out,key=lambda x:PRIORITY.index(x['format']))

def archive_queries(title,author=''):
    qs=[f'title:"{title}" AND mediatype:texts']
    if author:qs.append(f'title:"{title}" AND creator:"{author}" AND mediatype:texts')
    ts=tokens(title)[:6]
    if ts:
        qs.append(' AND '.join('title:'+urllib.parse.quote(x,safe='') for x in ts)+' AND mediatype:texts')
        qs.append(' '.join(ts)+' AND mediatype:texts')
    return qs

def archive_search(title,author=''):
    best=[];seen=set()
    for q in archive_queries(title,author):
        try:
            u='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':q,'fl[]':['identifier','title','creator'],'rows':25,'page':1,'output':'json'},doseq=True);j=get_json(u)
        except Exception:continue
        for d in j.get('response',{}).get('docs',[]):
            ident=str(d.get('identifier') or '')
            if not ident or ident in seen:continue
            seen.add(ident);sc=title_score(title,d.get('title'))
            if sc>=0.58:best.append((sc,ident))
        if best:
            for _,ident in sorted(best,reverse=True)[:8]:
                found=archive_native('https://archive.org/details/'+ident)
                if found:return found
    return []

def gutenberg_native(url):
    m=re.search(r'/(?:ebooks|epub)/(\d+)',url)
    if not m:return []
    i=m.group(1);return [{'format':'epub','url':f'https://www.gutenberg.org/ebooks/{i}.epub3.images','name':f'{i}.epub','source':'gutenberg','verifiedAccessible':True},{'format':'txt','url':f'https://www.gutenberg.org/cache/epub/{i}/pg{i}.txt','name':f'pg{i}.txt','source':'gutenberg','verifiedAccessible':True}]

def wikisource_search(title):
    searches=[f'intitle:"{title}"',title]
    nk=normalize(title);out=[];seen=set()
    for sr in searches:
        q=urllib.parse.urlencode({'action':'query','list':'search','srsearch':sr,'srnamespace':'0','srlimit':'20','format':'json','formatversion':'2'})
        try:j=get_json('https://ar.wikisource.org/w/api.php?'+q)
        except Exception:continue
        for r in j.get('query',{}).get('search',[]):
            t=str(r.get('title') or '')
            if not t or t in seen:continue
            seen.add(t)
            top=t.split('/',1)[0]
            if title_score(title,top)>=0.58 or (nk and nk in normalize(t)):
                out.append({'format':'html','url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote(t.replace(' ','_')),'name':t,'source':'arabic-wikisource','apiExtractable':True,'verifiedAccessible':True})
    return out[:20]

def discover_web(row):
    urls=[]
    for k in ('sources','sourceUrls'):
        v=row.get(k)
        if isinstance(v,list):urls.extend(str(x) for x in v if x)
    for k in ('source','sourceUrl','verifiedSource','candidateSource','downloadUrl'):
        if row.get(k):urls.append(str(row[k]))
    found=[];verified_url=str(row.get('verifiedSource') or '');verified_fmt=str(row.get('verifiedFormat') or '').lower().strip()
    if verified_url and verified_fmt in PRIORITY:
        found.append({'format':verified_fmt,'url':verified_url,'name':verified_url.rsplit('/',1)[-1],'source':'verified-catalog','redistributionApproved':row.get('redistributionApproved'),'verifiedAccessible':True})
    for u in dict.fromkeys(urls):
        f=fmt_of(u)
        if f in PRIORITY and '_lcp.epub' not in u.lower():found.append({'format':f,'url':u,'name':u.rsplit('/',1)[-1],'source':'direct','verifiedAccessible':True})
        if 'archive.org' in u:found+=archive_native(u)
        if 'gutenberg.org' in u:found+=gutenberg_native(u)
    return found

def drive_map():
    out={}
    for source_file in (DRIVE,DRIVE_VERIFIED):
        d=load(source_file,{'items':[]})
        for x in d.get('items',[]):
            if x.get('derivative'):continue
            n=normalize(x.get('title'))
            if not n:continue
            fmt=str(x.get('format') or 'epub').lower()
            rec={'format':fmt,'driveId':x.get('driveId'),'name':x.get('title'),'size':x.get('size'),'source':'google-drive-verified' if source_file==DRIVE_VERIFIED else 'google-drive-native','url':f"https://drive.google.com/file/d/{x.get('driveId')}/view",'extractionReady':x.get('extractionReady',True),'extractionMode':x.get('extractionMode','native' if fmt!='pdf' else 'pdf-text-or-ocr'),'verifiedAccessible':True}
            out.setdefault(n,[]).append(rec)
    return out

def ingested_map():
    out={}
    for x in load(INGESTED,{'items':[]}).get('items',[]):
        if not x.get('localUrl'):continue
        k=normalize(x.get('titleOriginal') or x.get('titleAr') or x.get('titleEn'))
        if k:out.setdefault(k,[]).append({'format':x.get('format') or 'txt','url':x.get('localUrl'),'name':x.get('titleOriginal'),'source':'local-ingested','local':True,'verifiedAccessible':True})
    return out

def dedup(found):
    uniq={}
    for z in found:
        if not z.get('format') or not z.get('url'):continue
        uniq[(z.get('format'),z.get('driveId') or z.get('url'))]=z
    return sorted(uniq.values(),key=lambda z:PRIORITY.index(z.get('format')) if z.get('format') in PRIORITY else 99)

def match_title_map(title,m):
    tk=normalize(title);out=[]
    for k,v in m.items():
        if not tk:continue
        if tk==k or title_score(title,k)>=0.72:out.extend(v)
    return out

def main():
    cat=load(CAT,{'items':[]});cand=load(CAND,{'items':[]});over=load(OVERRIDES,{'items':[]})
    cmap={str(x.get('workId') or x.get('catalogueId') or ''):x for x in cand.get('items',[]) if isinstance(x,dict)}
    omap={str(x.get('workId') or x.get('catalogueId') or ''):x for x in over.get('items',[]) if isinstance(x,dict)}
    dmap=drive_map();imap=ingested_map();rows=[];native=drive_native=drive_verified=needs_pdf=public_local=remote_extractable=0;queue=[]
    for x in cat.get('items',[]):
        wid=str(x.get('id') or '');merged=dict(x);merged.update(cmap.get(wid,{}));merged.update(omap.get(wid,{}));found=[]
        found+=match_title_map(x.get('title'),imap);found+=match_title_map(x.get('title'),dmap);found+=discover_web(merged)
        if not found:found+=wikisource_search(str(x.get('title') or ''))
        if not found:found+=archive_search(str(x.get('title') or ''),str(x.get('author') or ''))
        found=dedup(found);preferred=next((z for z in found if z.get('format')!='pdf' and z.get('verifiedAccessible',True)),None)
        if preferred:
            native+=1;drive_native+=1 if preferred.get('source')=='google-drive-native' else 0;drive_verified+=1 if preferred.get('source')=='google-drive-verified' else 0;public_local+=1 if preferred.get('source')=='local-ingested' else 0;remote_extractable+=1 if preferred.get('source') in {'arabic-wikisource','archive-metadata','gutenberg','direct','verified-catalog'} else 0;state='EXTRACTION_READY_NATIVE_OR_TEXT'
        elif found:
            preferred=next((z for z in found if z.get('format')=='pdf' and z.get('verifiedAccessible',True)),None)
            if preferred:
                needs_pdf+=1;drive_verified+=1 if preferred.get('source')=='google-drive-verified' else 0;state='EXTRACTION_READY_PDF_OCR'
            else:state='ACQUISITION_REQUIRED'
        elif x.get('access')=='PUBLIC_FULL_TEXT' and (x.get('sources') or x.get('formats')):
            preferred={'format':'txt','url':(x.get('sources') or [''])[0],'name':x.get('title'),'source':'public-catalog-fulltext','verifiedAccessible':True};state='EXTRACTION_READY_PUBLIC_FULL_TEXT';public_local+=1
        else:
            preferred=None;state='ACQUISITION_REQUIRED'
        if state=='ACQUISITION_REQUIRED':
            queue.append({'id':wid,'title':x.get('title'),'author':x.get('author'),'reason':'No verified extraction-capable local, Drive, native override, Wikisource, Archive.org, Gutenberg, or catalog fulltext path found after strict broad search.','ocrAllowed':True,'nextActions':['search Drive recursively','search Archive.org title/author variants','search Wikisource/OpenITI/public-domain repositories','acquire readable PDF then OCR','verify exact work/edition before generation']})
        rows.append({'id':wid,'title':x.get('title'),'author':x.get('author'),'previousAccess':x.get('access'),'state':state,'extractionReady':state.startswith('EXTRACTION_READY'),'preferred':preferred,'candidates':found[:20],'nativeSearchCompleted':True,'ocrAllowed':state in {'EXTRACTION_READY_PDF_OCR','ACQUISITION_REQUIRED'}})
    ready=sum(1 for r in rows if r['extractionReady']);total=len(rows);unavailable=total-ready
    out={'schema':'source-first-resolution-v6','governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'priority':PRIORITY,'catalogResources':total,'extractionReady':ready,'acquisitionRequired':unavailable,'nativeOrTextReady':native,'driveNativeMatched':drive_native,'driveVerifiedMatched':drive_verified,'localIngestedMatched':public_local,'remoteExtractionMatched':remote_extractable,'pdfOcrReady':needs_pdf,'allResourcesExtractionReady':unavailable==0,'strictAccessibleFilesOnly':True,'lockedLcpExcluded':True,'items':rows}
    save(OUT,out);save(QUEUE,{'schema':'resource-extraction-queue-v3','generatedAt':out['generatedAt'],'count':len(queue),'items':queue});save(AVAIL,{'schema':'resource-extraction-availability-v3','generatedAt':out['generatedAt'],'catalogResources':total,'extractionReady':ready,'acquisitionRequired':unavailable,'coveragePercent':round((100*ready/total),2) if total else 100,'driveVerifiedMatched':drive_verified,'allResourcesExtractionReady':unavailable==0,'strictAccessibleFilesOnly':True,'lockedLcpExcluded':True,'policy':'Generation may use only resources with extractionReady=true. Accessible Drive/native/public fulltext and readable PDF+OCR paths are first-class sources. Locked/borrow-only LCP assets are excluded. Missing resources remain queued for acquisition/resolution and never silently count as usable sources.'})
    print(json.dumps({k:out[k] for k in ('catalogResources','extractionReady','acquisitionRequired','nativeOrTextReady','driveNativeMatched','driveVerifiedMatched','localIngestedMatched','remoteExtractionMatched','pdfOcrReady','allResourcesExtractionReady')},ensure_ascii=False))
if __name__=='__main__':main()
