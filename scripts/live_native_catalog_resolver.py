#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json,re,time,urllib.parse,urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'data'/'public_catalog_all.generated.json'
CAND=ROOT/'private'/'acquisition_candidates.json'
OUT=ROOT/'private'/'live_native_catalog_resolution.json'
UA='ProphetBiographyLibrary/7.2-live-native-resolution'
PRIORITY=['epub','txt','html','xml','md','pdf']

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def get_json(url):
    req=urllib.request.Request(url,headers={'User-Agent':UA,'Accept':'application/json'})
    with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)

def norm(s):
    s=str(s or '').lower();s=re.sub(r'[\u064b-\u065f\u0670]','',s)
    for a,b in [('أ','ا'),('إ','ا'),('آ','ا'),('ى','ي'),('ة','ه')]:s=s.replace(a,b)
    return re.sub(r'[^\w\u0600-\u06ff]+',' ',s).strip()

def toks(s):return {x for x in norm(s).split() if len(x)>1}
def similar(a,b):
    a,b=norm(a),norm(b)
    if not a or not b:return False
    if a==b or a in b or b in a:return True
    ta,tb=toks(a),toks(b)
    return bool(ta and tb and len(ta&tb)/max(1,min(len(ta),len(tb)))>=0.67)

def fmt(name):
    n=str(name or '').lower().split('?')[0]
    for f in PRIORITY:
        if n.endswith('.'+f):return f
    return ''

def archive_files(identifier):
    try:m=get_json('https://archive.org/metadata/'+urllib.parse.quote(identifier))
    except Exception:return []
    out=[]
    for f in m.get('files',[]):
        name=str(f.get('name') or '');ft=fmt(name)
        if ft:
            out.append({'format':ft,'url':'https://archive.org/download/'+urllib.parse.quote(identifier)+'/'+urllib.parse.quote(name),'name':name,'source':'internet-archive','identifier':identifier})
    return sorted(out,key=lambda x:PRIORITY.index(x['format']))

def archive_search(title,author=''):
    if not title:return []
    q='title:("'+str(title).replace('"',' ')+'") AND mediatype:(texts)'
    url='https://archive.org/advancedsearch.php?'+urllib.parse.urlencode({'q':q,'fl[]':['identifier','title','creator'],'rows':6,'page':1,'output':'json'},doseq=True)
    try:d=get_json(url)
    except Exception:return []
    out=[]
    for doc in d.get('response',{}).get('docs',[]):
        rt=str(doc.get('title') or '')
        if not similar(title,rt):continue
        ident=str(doc.get('identifier') or '')
        if not ident:continue
        creator=doc.get('creator') or ''
        if isinstance(creator,list):creator=' '.join(map(str,creator))
        confidence='title-author-match' if (not author or not creator or similar(author,creator) or bool(toks(author)&toks(creator))) else 'title-match'
        for x in archive_files(ident):
            x['matchedTitle']=rt;x['confidence']=confidence;out.append(x)
    return out

def wikisource_search(title):
    if not title:return []
    url='https://ar.wikisource.org/w/api.php?'+urllib.parse.urlencode({'action':'query','list':'search','srsearch':'intitle:"'+str(title).replace('"',' ')+'"','srlimit':6,'format':'json','utf8':1})
    try:d=get_json(url)
    except Exception:return []
    out=[]
    for hit in d.get('query',{}).get('search',[]):
        t=str(hit.get('title') or '')
        if not similar(title,t):continue
        out.append({'format':'html','url':'https://ar.wikisource.org/wiki/'+urllib.parse.quote(t.replace(' ','_')),'name':t,'source':'arabic-wikisource','matchedTitle':t,'confidence':'title-match'})
    return out

def main():
    cat=load(CAT,{'items':[]});cand=load(CAND,{'items':[]})
    queue=[x for x in cat.get('items',[]) if x.get('access')!='PUBLIC_FULL_TEXT']
    existing=cand.get('items',[]) if isinstance(cand.get('items'),list) else []
    by_id={str(x.get('workId') or x.get('catalogueId') or ''):x for x in existing if isinstance(x,dict)}
    resolved=[];updated=0
    for row in queue:
        wid=str(row.get('id') or '');title=row.get('title') or '';author=row.get('author') or ''
        found=archive_search(title,author)+wikisource_search(title)
        uniq={(x['format'],x['url']):x for x in found}
        found=sorted(uniq.values(),key=lambda x:PRIORITY.index(x['format']))
        if not found:continue
        preferred=next((x for x in found if x['format']!='pdf'),found[0])
        resolved.append({'id':wid,'title':title,'author':author,'preferred':preferred,'candidates':found[:20]})
        item=by_id.get(wid)
        if item is None:
            item={'workId':wid,'title':title,'author':author};existing.append(item);by_id[wid]=item
        urls=list(item.get('sourceUrls') or [])
        for x in found:
            if x['url'] not in urls:urls.append(x['url'])
        item['sourceUrls']=urls
        item['verifiedSource']=preferred['url']
        item['verifiedFormat']=preferred['format']
        item['liveCatalogResolved']=True
        item['liveCatalogResolvedAt']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        updated+=1
    cand['items']=existing;save(CAND,cand)
    out={'schema':'live-native-catalog-resolution-v1','generatedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'unresolvedScanned':len(queue),'resolvedCount':len(resolved),'candidateRecordsUpdated':updated,'items':resolved}
    save(OUT,out)
    print(json.dumps({k:out[k] for k in ('unresolvedScanned','resolvedCount','candidateRecordsUpdated')},ensure_ascii=False))

if __name__=='__main__':main()
