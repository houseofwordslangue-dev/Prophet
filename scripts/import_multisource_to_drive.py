# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
"""Multi-source importer for Prophet-Library-Ingestion.

Designed for Google Colab + mounted Google Drive.
Sources:
- Masaha: explicit/seed book and group URLs, EPUB preferred, PDF fallback.
- Wikisource: title discovery in ar/en/fr and WS Export EPUB.
- Project Gutenberg: Gutendex discovery, EPUB preferred (use download URLs returned by catalog).
- OpenITI: optional text import for exact URI overrides.
- Internet Archive remains handled by the existing archive importer.
"""
from __future__ import annotations
import argparse, hashlib, html, json, re, time, unicodedata, zipfile
from difflib import SequenceMatcher
from pathlib import Path
from urllib.parse import quote, quote_plus, urljoin, urlparse
import requests
try:
    from bs4 import BeautifulSoup
except Exception:
    BeautifulSoup = None
try:
    from google.colab import drive
except Exception:
    drive = None

REPO_RAW = "https://raw.githubusercontent.com/houseofwordslangue-dev/Prophet/main"
REPO_API = "https://api.github.com/repos/houseofwordslangue-dev/Prophet/contents/data/catalogue"
CONFIG_URL = f"{REPO_RAW}/data/multisource_import_config.json"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Prophet-Library-Ingestion/2.0 (+research-library-import)"})

def now(): return time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
def norm(s):
    s=unicodedata.normalize('NFKD',s or '')
    s=''.join(c for c in s if unicodedata.category(c)!='Mn')
    s=re.sub(r'[\u064B-\u065F\u0670\u0640]','',s)
    s=s.casefold().replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ة','ه')
    s=re.sub(r'[^\w\u0600-\u06FF]+',' ',s,flags=re.UNICODE)
    return re.sub(r'\s+',' ',s).strip()
def similarity(a,b):
    a,b=norm(a),norm(b)
    return SequenceMatcher(None,a,b).ratio() if a and b else 0.0
def sha256(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for ch in iter(lambda:f.read(1024*1024),b''): h.update(ch)
    return h.hexdigest()
def valid_epub(p):
    try:
        p=Path(p)
        if p.stat().st_size<1024 or not zipfile.is_zipfile(p): return False
        with zipfile.ZipFile(p) as z:
            ns=set(z.namelist())
            return 'META-INF/container.xml' in ns and any(n.lower().endswith(('.xhtml','.html','.htm')) for n in ns)
    except Exception: return False
def valid_pdf(p):
    try:
        with open(p,'rb') as f: return Path(p).stat().st_size>1024 and f.read(5)==b'%PDF-'
    except Exception: return False
def valid_text(p):
    try: return Path(p).stat().st_size>1000 and len(Path(p).read_text('utf-8',errors='ignore'))>1000
    except Exception: return False
def existing(dest):
    ep=[p for p in Path(dest).glob('*.epub') if valid_epub(p)]
    if ep: return 'epub',ep
    tx=[p for p in Path(dest).glob('*.txt') if valid_text(p)]
    if tx: return 'text',tx
    pd=[p for p in Path(dest).glob('*.pdf') if valid_pdf(p)]
    if pd: return 'pdf',pd
    return None,[]
def download(url,out,timeout=(30,300)):
    out=Path(out); tmp=out.with_suffix(out.suffix+'.part')
    with SESSION.get(url,stream=True,timeout=timeout,allow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp,'wb') as f:
            for ch in r.iter_content(1024*1024):
                if ch: f.write(ch)
    tmp.replace(out); return out
def find_books_root():
    for p in [Path('/content/drive/MyDrive/Prophet-Library-Ingestion/books'),Path('/content/drive/My Drive/Prophet-Library-Ingestion/books')]:
        if p.is_dir(): return p
    for p in Path('/content/drive').rglob('Prophet-Library-Ingestion'):
        if (p/'books').is_dir(): return p/'books'
    raise FileNotFoundError('Prophet-Library-Ingestion/books not found')
def fetch_json(url):
    r=SESSION.get(url,timeout=60); r.raise_for_status(); return r.json()
def load_config(): return fetch_json(CONFIG_URL)
def load_catalogue():
    rows=[]
    for f in fetch_json(REPO_API):
        if not f.get('name','').startswith('chunk-') or not f['name'].endswith('.json'): continue
        for a in fetch_json(f['download_url']).get('items',[]):
            if not a or len(a)<8: continue
            rows.append({'catalogue_id':a[0],'ordinal':a[1],'section':a[2],'title_ar':a[3] or '', 'title_en':a[4] or '', 'author_ar':a[5] or '', 'author_en':a[6] or '', 'kind':a[7] or '', 'rights':a[8] if len(a)>8 else '', 'status':a[10] if len(a)>10 else ''})
    return rows
def write_provenance(dest,source,rec):
    with open(Path(dest)/f'{source}_source.json','w',encoding='utf-8') as f: json.dump(rec,f,ensure_ascii=False,indent=2)
def unique_out(dest,stem,ext):
    p=Path(dest)/(stem+ext); i=2
    while p.exists(): p=Path(dest)/(f'{stem}-{i}'+ext); i+=1
    return p
def extract_links(page_url):
    r=SESSION.get(page_url,timeout=60,allow_redirects=True); r.raise_for_status(); txt=r.text; links=[]
    if BeautifulSoup:
        soup=BeautifulSoup(txt,'html.parser')
        for a in soup.find_all('a',href=True): links.append((a.get_text(' ',strip=True),urljoin(r.url,a['href'])))
    for m in re.finditer(r'''(?:href|src)=["']([^"']+)["']''',txt,re.I): links.append(('',urljoin(r.url,html.unescape(m.group(1)))))
    return r.url,txt,links

# Masaha
def masaha_candidates(page_url):
    final,txt,links=extract_links(page_url); epub=[]; pdf=[]; book_pages=[]
    for label,u in links:
        ul=u.lower(); ll=label.lower()
        if '.epub' in ul or 'epub' in ll: epub.append(u)
        elif '.pdf' in ul or re.search(r'\bpdf\b',ll): pdf.append(u)
        if re.search(r'/book/\d+$',urlparse(u).path): book_pages.append(u)
    for raw in re.findall(r'https?:\\?/\\?/[^"\'\s<>]+',txt):
        u=raw.replace('\\/','/')
        if '.epub' in u.lower(): epub.append(u)
        elif '.pdf' in u.lower(): pdf.append(u)
    return final,list(dict.fromkeys(epub)),list(dict.fromkeys(pdf)),list(dict.fromkeys(book_pages))
def masaha_import(item,dest):
    urls=item.get('urls',[])
    if item.get('group_url'):
        try:
            _,_,_,bps=masaha_candidates(item['group_url']); urls=list(dict.fromkeys(urls+bps))
        except Exception: pass
    imported=[]; errors=[]
    for idx,url in enumerate(urls,1):
        try:
            final,eps,pdfs,_=masaha_candidates(url); choices=[('epub',u) for u in eps]+[('pdf',u) for u in pdfs]
            if not choices: raise RuntimeError('No EPUB/PDF link discovered on page')
            fmt,u=choices[0]; ext='.epub' if fmt=='epub' else '.pdf'; out=unique_out(dest,f'masaha-volume-{idx:02d}',ext)
            download(u,out); ok=valid_epub(out) if fmt=='epub' else valid_pdf(out)
            if not ok: out.unlink(missing_ok=True); raise RuntimeError('Downloaded file failed validation')
            imported.append({'page_url':final,'download_url':u,'format':fmt,'filename':out.name,'bytes':out.stat().st_size,'sha256':sha256(out)})
            time.sleep(0.7)
        except Exception as e: errors.append({'url':url,'error':f'{type(e).__name__}: {e}'})
    if imported:
        rec={'catalogue_id':item['catalogue_id'],'title':item.get('title'),'source':'Masaha','source_home':'https://www.masaha.org/','publication_rights':'review-source-terms','imported_at':now(),'files':imported,'errors':errors}
        write_provenance(dest,'masaha',rec); return {'status':'IMPORTED','files':imported,'errors':errors}
    return {'status':'NO_IMPORT','errors':errors}

# Wikisource
def ws_search(lang,title,limit=5):
    api=f'https://{lang}.wikisource.org/w/api.php'; params={'action':'query','list':'search','srsearch':title,'srnamespace':'0','srlimit':limit,'format':'json','utf8':1}
    r=SESSION.get(api,params=params,timeout=60); r.raise_for_status(); return [x['title'] for x in r.json().get('query',{}).get('search',[])]
def ws_export_url(lang,page,fmt='epub'): return 'https://ws-export.wmcloud.org/?'+f'lang={quote_plus(lang)}&page={quote_plus(page)}&format={quote_plus(fmt)}'
def wikisource_import(cat,dest,min_score=.84):
    queries=[]
    if cat.get('title_ar'): queries.append(('ar',cat['title_ar']))
    if cat.get('title_en'): queries.extend([('en',cat['title_en']),('fr',cat['title_en'])])
    best=None
    for lang,q in queries:
        try:
            for t in ws_search(lang,q):
                sc=similarity(q,t)
                if not best or sc>best[0]: best=(sc,lang,t,q)
        except Exception: continue
    if not best or best[0]<min_score: return {'status':'NO_MATCH','best':best}
    sc,lang,page,q=best; u=ws_export_url(lang,page,'epub'); out=unique_out(dest,f'wikisource-{lang}','.epub')
    try:
        download(u,out,timeout=(30,360))
        if not valid_epub(out): out.unlink(missing_ok=True); return {'status':'EXPORT_FAILED','page':page,'score':sc,'url':u}
        rec={'catalogue_id':cat['catalogue_id'],'source':'Wikisource','language':lang,'page':page,'page_url':f'https://{lang}.wikisource.org/wiki/{quote(page.replace(" ","_"))}','download_url':u,'license_note':'Wikisource text/page licensing applies; preserve attribution/share-alike where required','match_score':sc,'filename':out.name,'bytes':out.stat().st_size,'sha256':sha256(out),'imported_at':now()}
        write_provenance(dest,'wikisource',rec); return {'status':'IMPORTED',**rec}
    except Exception as e:
        out.unlink(missing_ok=True); return {'status':'ERROR','error':f'{type(e).__name__}: {e}','page':page,'score':sc}

# Project Gutenberg
def gutenberg_search(title):
    r=SESSION.get('https://gutendex.com/books',params={'search':title},timeout=60); r.raise_for_status(); return r.json().get('results',[])
def gutenberg_import(cat,dest,min_score=.88):
    candidates=[]
    for q in [cat.get('title_en'),cat.get('title_ar')]:
        if not q: continue
        try:
            for b in gutenberg_search(q): candidates.append((similarity(q,b.get('title','')),q,b))
        except Exception: pass
    if not candidates: return {'status':'NO_MATCH'}
    candidates.sort(key=lambda x:x[0],reverse=True); sc,q,b=candidates[0]
    if sc<min_score: return {'status':'NO_MATCH','best_title':b.get('title'),'score':sc}
    fm=b.get('formats',{}) or {}; prefs=[k for k in fm if 'application/epub+zip' in k and 'noimages' not in k]; prefs += [k for k in fm if 'application/epub+zip' in k]; prefs += [k for k in fm if k.startswith('text/html')]
    if not prefs: return {'status':'NO_DOWNLOAD','book_id':b.get('id')}
    u=fm[prefs[0]]; ext='.epub' if 'epub' in prefs[0] else '.html'; out=unique_out(dest,f'gutenberg-{b.get("id")}',ext)
    try:
        download(u,out)
        if ext=='.epub' and not valid_epub(out): raise RuntimeError('Invalid EPUB')
        rec={'catalogue_id':cat['catalogue_id'],'source':'Project Gutenberg','book_id':b.get('id'),'title':b.get('title'),'authors':b.get('authors'),'subjects':b.get('subjects'),'languages':b.get('languages'),'download_url':u,'format':prefs[0],'match_score':sc,'filename':out.name,'bytes':out.stat().st_size,'sha256':sha256(out),'rights_note':'Check ebook header and local jurisdiction; Project Gutenberg trademark/redistribution terms apply','imported_at':now()}
        write_provenance(dest,'gutenberg',rec); return {'status':'IMPORTED',**rec}
    except Exception as e:
        out.unlink(missing_ok=True); return {'status':'ERROR','error':f'{type(e).__name__}: {e}'}

# OpenITI exact overrides
def openiti_import_override(item,dest):
    u=item.get('raw_url')
    if not u: return {'status':'NO_OVERRIDE'}
    out=unique_out(dest,'openiti','.txt')
    try:
        download(u,out)
        if not valid_text(out): raise RuntimeError('OpenITI text failed validation')
        rec={'catalogue_id':item['catalogue_id'],'source':'OpenITI','raw_url':u,'license':'CC BY-NC-SA 4.0 (per OpenITI releases)','filename':out.name,'bytes':out.stat().st_size,'sha256':sha256(out),'imported_at':now()}
        write_provenance(dest,'openiti',rec); return {'status':'IMPORTED',**rec}
    except Exception as e:
        out.unlink(missing_ok=True); return {'status':'ERROR','error':f'{type(e).__name__}: {e}'}

def main(force=False,max_auto=150,sources=None):
    if drive is not None:
        try: drive.mount('/content/drive',force_remount=False)
        except Exception: pass
    root=find_books_root(); cfg=load_config(); cats=load_catalogue(); sources=set(sources or cfg.get('enabled_sources',['masaha','wikisource','gutenberg','openiti']))
    report={'started_at':now(),'books_root':str(root),'sources':sorted(sources),'items':[]}
    if 'masaha' in sources:
        for item in cfg.get('masaha',{}).get('items',[]):
            cid=item['catalogue_id']; dest=root/cid; dest.mkdir(parents=True,exist_ok=True); fmt,ex=existing(dest)
            if fmt=='epub' and not force: report['items'].append({'catalogue_id':cid,'source':'masaha','status':'SKIPPED_VALID_EPUB_EXISTS','existing':[p.name for p in ex]}); continue
            report['items'].append({'catalogue_id':cid,'source':'masaha',**masaha_import(item,dest)})
    if 'openiti' in sources:
        for item in cfg.get('openiti',{}).get('items',[]):
            cid=item['catalogue_id']; dest=root/cid; dest.mkdir(parents=True,exist_ok=True); fmt,ex=existing(dest)
            if fmt in ('epub','text') and not force: report['items'].append({'catalogue_id':cid,'source':'openiti','status':'SKIPPED_VALID_TEXT_OR_EPUB_EXISTS'}); continue
            report['items'].append({'catalogue_id':cid,'source':'openiti',**openiti_import_override(item,dest)})
    n=0
    for cat in cats:
        if n>=max_auto: break
        if cat['kind'] in ('institution','media-channel','video','video-series','web','catalogue'): continue
        dest=root/cat['catalogue_id']; dest.mkdir(parents=True,exist_ok=True); fmt,ex=existing(dest)
        if fmt=='epub' and not force: continue
        res=None
        if 'wikisource' in sources:
            res=wikisource_import(cat,dest,float(cfg.get('wikisource',{}).get('min_match_score',0.84)))
            if res.get('status')=='IMPORTED': report['items'].append({'catalogue_id':cat['catalogue_id'],'source':'wikisource',**res}); n+=1; continue
        if 'gutenberg' in sources:
            res2=gutenberg_import(cat,dest,float(cfg.get('gutenberg',{}).get('min_match_score',0.88)))
            if res2.get('status')=='IMPORTED': report['items'].append({'catalogue_id':cat['catalogue_id'],'source':'gutenberg',**res2}); n+=1; continue
        if res and res.get('status') not in ('NO_MATCH',): report['items'].append({'catalogue_id':cat['catalogue_id'],'source':'wikisource',**res})
        time.sleep(float(cfg.get('request_delay_seconds',0.35)))
    report['finished_at']=now(); st=root.parent/'status'; st.mkdir(parents=True,exist_ok=True); rp=st/'multisource_import_report.json'; rp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Report:',rp); counts={}
    for x in report['items']: counts[x.get('status','?')]=counts.get(x.get('status','?'),0)+1
    print(json.dumps(counts,ensure_ascii=False,indent=2)); return report

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--force',action='store_true'); ap.add_argument('--max-auto',type=int,default=150); ap.add_argument('--sources',nargs='*'); a=ap.parse_args(); main(force=a.force,max_auto=a.max_auto,sources=a.sources)
