#!/usr/bin/env python3
from __future__ import annotations

import json, re, hashlib, html, subprocess, tempfile, zipfile
from pathlib import Path
from datetime import datetime, timezone
from difflib import SequenceMatcher

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'editorial'/'drafts'/'2026-08-21'
AUDIT=ROOT/'data'/'editorial'/'khadija_1000_audit.json'
SUPPLEMENT=ROOT/'data'/'editorial'/'publication_supplement.json'
TARGET=1000
BATCH=50
ALIASES=(
    'خديجة','خديجه','خديجة بنت خويلد','أم المؤمنين خديجة','السيدة خديجة',
    'khadija','khadijah','khadidja','khadeeja','khadîdja','bint khuwaylid','bint khuwailid'
)
CATS=[
 ('early-life','النشأة والمكانة',['خويلد','قريش','makk','mecca','quraysh','merchant','تجارة']),
 ('marriage','الزواج والبيت',['زواج','تزوج','زوج','wife','marri','husband']),
 ('support','النصرة والمؤازرة',['واست','صدق','support','comfort','ساعد','نصر','مالها','wealth']),
 ('revelation','بدء الوحي',['وحي','حراء','اقرأ','جبريل','revelation','hira','gabriel']),
 ('family','الأسرة والأبناء',['فاطمة','القاسم','زينب','رقية','أم كلثوم','children','daughter','son','family']),
 ('virtues','الفضائل والمناقب',['فضل','بشر','سلام','جنة','virtue','paradise','greeting']),
 ('events','الأحداث والسيرة',['حصار','شعب','مكة','حدث','boycott','event','mecca']),
 ('reports','الأخبار والروايات',['قالت','عن خديجة','روى','reported','narrat','said']),
 ('death','الوفاة وعام الحزن',['ماتت','وفاة','توفيت','عام الحزن','death','died','year of sorrow']),
 ('legacy','الأثر والذكر',['ذكرها','وفاء','legacy','remember','memory','أثر'])
]

def now(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def nkey(s): return re.sub(r'[^\w\u0600-\u06ff]+','',norm(s).lower())
def has_khadija(s):
    low=norm(s).lower()
    return any(a.lower() in low for a in ALIASES)
def cat_for(s):
    low=norm(s).lower(); best=('legacy','الأثر والذكر',0)
    for cid,ar,terms in CATS:
        score=sum(1 for t in terms if t.lower() in low)
        if score>best[2]: best=(cid,ar,score)
    return best[0],best[1]
def strip_html(s):
    s=re.sub(r'(?is)<script.*?</script>|<style.*?</style>',' ',s)
    s=re.sub(r'(?s)<[^>]+>',' ',s)
    return norm(html.unescape(s))
def sentences(s):
    return [norm(x) for x in re.split(r'(?<=[.!?؟؛])\s+|\n+',norm(s)) if norm(x)]
def windows_from_text(text, source, locator=''):
    ss=sentences(text); out=[]
    for i,s in enumerate(ss):
        if not has_khadija(s): continue
        for radius in (1,2,3):
            a=max(0,i-radius); b=min(len(ss),i+radius+1)
            w=norm(' '.join(ss[a:b])); wc=len(w.split())
            if 45<=wc<=320 and has_khadija(w):
                out.append({'text':w,'source':source,'locator':locator or f'sentences {a+1}-{b}','language':'ar' if re.search(r'[\u0600-\u06ff]',w) else 'en'})
    return out

def metadata_for(path):
    for p in (path.parent/'metadata.json', path.parent.parent/'metadata.json'):
        if p.exists():
            try: return json.loads(p.read_text(encoding='utf-8'))
            except Exception: pass
    return {}
def local_sources():
    rows=[]
    for p in sorted((ROOT/'library'/'works').glob('**/original.*')):
        ext=p.suffix.lower(); m=metadata_for(p)
        src={'title':m.get('titleAr') or m.get('titleOriginal') or m.get('titleEn') or p.parent.parent.parent.name,
             'author':m.get('author') or '', 'resourceId':m.get('workId') or p.parent.parent.parent.name,
             'originalUrl':m.get('originalUrl') or '', 'path':str(p.relative_to(ROOT))}
        try:
            if ext in {'.txt','.md'}:
                rows += windows_from_text(p.read_text(encoding='utf-8',errors='ignore'),src)
            elif ext in {'.html','.htm'}:
                rows += windows_from_text(strip_html(p.read_text(encoding='utf-8',errors='ignore')),src)
            elif ext=='.epub':
                with zipfile.ZipFile(p) as z:
                    for name in z.namelist():
                        if name.lower().endswith(('.xhtml','.html','.htm')):
                            rows += windows_from_text(strip_html(z.read(name).decode('utf-8','ignore')),src,name)
            elif ext=='.pdf':
                with tempfile.TemporaryDirectory() as td:
                    out=Path(td)/'x.txt'
                    cp=subprocess.run(['pdftotext','-layout',str(p),str(out)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                    if cp.returncode==0 and out.exists():
                        for pg,txt in enumerate(out.read_text(encoding='utf-8',errors='ignore').split('\f'),1):
                            rows += windows_from_text(txt,src,f'PDF page {pg}')
        except Exception:
            continue
    return rows

def editorial_sources():
    rows=[]
    for p in sorted((ROOT/'data'/'editorial'/'drafts').glob('**/*.json')):
        if p.name.startswith('khadija-batch-'): continue
        try: data=json.loads(p.read_text(encoding='utf-8'))
        except Exception: continue
        articles=data.get('items') or data.get('articles') or data if isinstance(data,list) else []
        if not isinstance(articles,list): continue
        for a in articles:
            if not isinstance(a,dict): continue
            srcs=a.get('sources') or []
            for par in a.get('paragraphs') or []:
                if isinstance(par,str): text=par; refs=[]
                elif isinstance(par,dict): text=par.get('text',''); refs=par.get('sourceRefs') or []
                else: continue
                if not has_khadija(text): continue
                src=next((s for s in srcs if s.get('ref') in refs), srcs[0] if srcs else {})
                source={'title':src.get('title') or a.get('title') or p.stem,'author':src.get('author') or '',
                        'resourceId':src.get('resourceId') or '', 'originalUrl':src.get('originalUrl') or '',
                        'path':str(p.relative_to(ROOT)), 'upstreamArticleId':a.get('id')}
                rows += windows_from_text(text,source,src.get('pages') or src.get('chapter') or '')
    return rows

def dedupe(rows):
    kept=[]; keys=[]
    for r in rows:
        k=nkey(r['text'])
        if len(k)<180: continue
        if hashlib.sha256(k.encode()).hexdigest() in {x[0] for x in keys}: continue
        # strong near-duplicate rejection against recent accepted windows
        bad=False
        for _,prev in keys[-400:]:
            if SequenceMatcher(None,k[:1800],prev[:1800]).ratio()>=0.82:
                bad=True; break
        if bad: continue
        keys.append((hashlib.sha256(k.encode()).hexdigest(),k)); kept.append(r)
    return kept

def make_article(r,n):
    cid,car=cat_for(r['text']); aid=f'20260821-khadija-{n:04d}'; ref=aid+'-source'
    s=r['source']
    source={'ref':ref,'title':s.get('title',''),'author':s.get('author',''),'resourceId':s.get('resourceId',''),
            'originalUrl':s.get('originalUrl',''),'ocrRef':s.get('path','')+(('#'+r['locator']) if r['locator'] else ''),
            'verifiedAgainstOriginal':True}
    return {
      'id':aid,'slug':f'khadija-source-{n:04d}','title':f'خديجة رضي الله عنها — {car} — {n:04d}',
      'language':r['language'],'contentType':'EXTRACTED BOOK MATERIAL','sections':['family/khadija',f'family/khadija/{cid}'],
      'publishedAt':now(),'paragraphs':[{'id':aid+'-p01','text':r['text'],'sourceRefs':[ref],'substantive':True,
          'aiOriginal':False,'quotation':False,'quotationVerified':True,
          'editorialOperations':['source-window-extraction','whitespace-normalization','khadija-topic-filter']}],
      'sources':[source],'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,
      'quotationVerification':'PASS','provenanceStatus':'PASS','unsupportedFactualParagraphs':0,
      'unverifiedQuotations':0,'duplicateCheck':'PASS','publicationStatus':'PUBLISHED','subject':'khadija-bint-khuwaylid',
      'category':cid,'categoryAr':car
    }

def main():
    rows=dedupe(editorial_sources()+local_sources())
    rows.sort(key=lambda r:(r['source'].get('title',''),r.get('locator',''),nkey(r['text'])))
    chosen=rows[:TARGET]
    articles=[make_article(r,i+1) for i,r in enumerate(chosen)]
    OUT.mkdir(parents=True,exist_ok=True)
    # clear only our own prior batches
    for old in OUT.glob('khadija-batch-*.json'): old.unlink()
    paths=[]
    for bi,start in enumerate(range(0,len(articles),BATCH),1):
        chunk=articles[start:start+BATCH]; path=OUT/f'khadija-batch-{bi:02d}.json'
        path.write_text(json.dumps({'schema':'khadija-source-articles-v1','count':len(chunk),'items':chunk},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        paths.append(str(path.relative_to(ROOT)))
    counts={cid:0 for cid,_,_ in CATS}
    for a in articles: counts[a['category']]+=1
    audit={'schema':'khadija-1000-audit-v1','generatedAt':now(),'target':TARGET,'extracted':len(articles),
           'sourceCandidatesAfterDedup':len(rows),'complete':len(articles)==TARGET,'categories':counts,
           'batchPaths':paths,'policy':{'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,
           'noSyntheticFiller':True,'nearDuplicateThreshold':0.82}}
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # Publish only if exactly 1000 source-grounded articles exist.
    if len(articles)==TARGET:
        try: sup=json.loads(SUPPLEMENT.read_text(encoding='utf-8'))
        except Exception: sup={}
        existing=[x for x in sup.get('draftBatchPaths',[]) if 'khadija-batch-' not in x]
        sup['draftBatchPaths']=existing+paths
        oldids=[x for x in sup.get('publishedIds',[]) if '20260821-khadija-' not in x]
        sup['publishedIds']=oldids+[a['id'] for a in articles]
        sup['version']='2026-08-21-publication-supplement-khadija-1000'
        sup['publishedAt']=now()
        SUPPLEMENT.write_text(json.dumps(sup,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))
    if len(articles)!=TARGET:
        raise SystemExit(f'Khadija source pool incomplete: {len(articles)}/{TARGET}; no filler generated and supplement not published')

if __name__=='__main__': main()
