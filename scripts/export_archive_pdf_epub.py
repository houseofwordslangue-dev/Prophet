#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import argparse, json, os, re, time, unicodedata, urllib.parse
from pathlib import Path
import requests

UA='ProphetArchiveDriveExporter/1.0'
S=requests.Session(); S.headers.update({'User-Agent':UA,'Accept':'application/json'})

def norm(s):
    s=unicodedata.normalize('NFKD',str(s or ''))
    s=''.join(c for c in s if not unicodedata.combining(c)).casefold()
    s=s.replace('ـ',' ')
    return ' '.join(re.sub(r'[^\w\u0600-\u06ff]+',' ',s).split())

def toks(s): return {x for x in norm(s).split() if len(x)>1}
def sim(a,b):
    A,B=toks(a),toks(b)
    return len(A&B)/len(A|B) if A and B else 0.0

def exact_identifier(url):
    m=re.search(r'archive\.org/(?:details|download)/([^/?#]+)',url or '')
    return urllib.parse.unquote(m.group(1)) if m else ''

def search_candidates(title,author):
    q=f'title:"{title}" AND mediatype:texts'
    params={'q':q,'fl[]':['identifier','title','creator','date','year','rights','licenseurl'],'rows':12,'output':'json','sort[]':'downloads desc'}
    try:
        r=S.get('https://archive.org/advancedsearch.php',params=params,timeout=45); r.raise_for_status()
        docs=r.json().get('response',{}).get('docs',[])
    except Exception:
        return []
    scored=[]
    for d in docs:
        dt=d.get('title',''); dc=d.get('creator','')
        if isinstance(dt,list):dt=' '.join(map(str,dt))
        if isinstance(dc,list):dc=' '.join(map(str,dc))
        ts=sim(title,dt); aus=sim(author,dc) if author else 0.0
        score=ts*.88+aus*.12
        if norm(title)==norm(dt): score=max(score,.98)
        if ts>=.54 or score>=.58: scored.append((score,d))
    scored.sort(key=lambda x:x[0],reverse=True)
    return [d for _,d in scored[:3]]

def metadata(identifier):
    r=S.get('https://archive.org/metadata/'+urllib.parse.quote(identifier,safe=''),timeout=60); r.raise_for_status(); return r.json()

def downloadable_files(meta):
    md=meta.get('metadata',{}) or {}
    if str(md.get('is_dark','')).lower() in {'true','1'}: return []
    out=[]
    for f in meta.get('files',[]) or []:
        if not isinstance(f,dict): continue
        name=str(f.get('name','')); low=name.casefold()
        if not (low.endswith('.pdf') or low.endswith('.epub')): continue
        if low.endswith('_lcp.epub') or 'encrypted' in str(f.get('format','')).casefold(): continue
        if str(f.get('private','')).lower() in {'true','1'}: continue
        try:size=int(f.get('size') or 0)
        except:size=0
        if size and size<1024: continue
        out.append((name,size,str(f.get('format',''))))
    return out

def clean_name(s): return re.sub(r'[^\w.()\-\u0600-\u06ff]+','_',s).strip('_')[:180]

def download(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.part')
    with S.get(url,stream=True,timeout=(45,600),allow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp,'wb') as o:
            for b in r.iter_content(1024*1024):
                if b:o.write(b)
    tmp.replace(path)
    return path.stat().st_size

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--chunk',required=True); ap.add_argument('--out',required=True); args=ap.parse_args()
    src=Path(args.chunk); out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    rows=json.loads(src.read_text(encoding='utf-8')).get('items',[])
    report={'chunk':src.name,'works':0,'matchedItems':0,'downloaded':0,'failed':0,'files':[],'unresolved':[]}
    seen=set()
    for row in rows:
        if not isinstance(row,list) or len(row)<13: continue
        work=str(row[0]); title=str(row[3] or ''); author=str(row[5] or ''); source=str(row[12] or '')
        if not title: continue
        report['works']+=1
        ids=[]
        ex=exact_identifier(source)
        if ex: ids.append(ex)
        for d in search_candidates(title,author):
            ident=str(d.get('identifier') or '')
            if ident and ident not in ids: ids.append(ident)
        matched=False
        for ident in ids[:4]:
            try: meta=metadata(ident)
            except Exception as e:
                report['failed']+=1; report['files'].append({'workId':work,'title':title,'identifier':ident,'status':'metadata-failed','error':str(e)[:180]}); continue
            files=downloadable_files(meta)
            if not files: continue
            matched=True; report['matchedItems']+=1
            for fname,size,fmt in files:
                key=(ident,fname)
                if key in seen: continue
                seen.add(key)
                ext='.epub' if fname.casefold().endswith('.epub') else '.pdf'
                dest=out/ext[1:]/clean_name(work)/clean_name(ident)/(clean_name(fname) or ('file'+ext))
                url='https://archive.org/download/'+urllib.parse.quote(ident,safe='')+'/'+urllib.parse.quote(fname,safe='/')
                try:
                    got=download(url,dest); report['downloaded']+=1
                    report['files'].append({'workId':work,'title':title,'author':author,'identifier':ident,'archiveFile':fname,'format':ext[1:].upper(),'bytes':got,'sourceUrl':url,'localPath':dest.as_posix(),'status':'downloaded'})
                except Exception as e:
                    report['failed']+=1; report['files'].append({'workId':work,'title':title,'identifier':ident,'archiveFile':fname,'sourceUrl':url,'status':'download-failed','error':str(e)[:240]})
        if not matched: report['unresolved'].append({'workId':work,'title':title,'author':author})
        time.sleep(.15)
    (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('chunk','works','matchedItems','downloaded','failed')},ensure_ascii=False))
if __name__=='__main__': main()
