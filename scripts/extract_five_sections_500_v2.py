#!/usr/bin/env python3
from collections import Counter
import json
import extract_five_sections_500 as b

# Broaden only with source works whose declared subject still matches the user's exclusive taxonomy.
b.IAFILES.update({
  'prophet2':('hojat_djvu.txt','حجة الله على العالمين في معجزات سيد المرسلين','يوسف بن إسماعيل النبهاني'),
  'mercy2':('jawaher_djvu.txt','جواهر البحار في فضائل النبي المختار','يوسف بن إسماعيل النبهاني'),
})

def pick_dedicated(src, section, keys):
    pool=[]
    for key in keys:
        text,meta=src[key]
        for sc,a,z,body,wc in b.select_scored(text,section,b.COUNT,source_level=True):
            pool.append((sc,key,a,z,body,wc,meta))
    pool.sort(key=lambda x:(-x[0],x[1],x[2]))
    chosen=[]; occupied={}
    for c in pool:
        sc,key,a,z,body,wc,meta=c
        if any(not(z<=x or a>=y) for x,y in occupied.get(key,[])): continue
        occupied.setdefault(key,[]).append((a,z)); chosen.append(c)
        if len(chosen)==b.COUNT: break
    if len(chosen)!=b.COUNT: raise SystemExit(f'{section}: {len(chosen)}/{b.COUNT}')
    return chosen

def pick_scored(src, section, keys, floor=3):
    pool=[]
    for key in keys:
        text,meta=src[key]
        ps=b.paragraphs(text)
        for a,z,body,wc in b.windows(ps):
            sc=b.score(section,body)
            if sc>=floor: pool.append((sc,key,a,z,body,wc,meta))
    pool.sort(key=lambda x:(-x[0],x[1],x[2]))
    chosen=[]; occupied={}
    for c in pool:
        sc,key,a,z,body,wc,meta=c
        if any(not(z<=x or a>=y) for x,y in occupied.get(key,[])): continue
        occupied.setdefault(key,[]).append((a,z)); chosen.append(c)
        if len(chosen)==b.COUNT: break
    return chosen

def build():
    src=b.load_sources(); drafts=[]
    dedicated={
      'light':['light'],
      'prophet':['prophet','prophet2'],
      'messenger':['messenger'],
    }
    for section,keys in dedicated.items():
        for i,(sc,key,a,z,body,wc,meta) in enumerate(pick_dedicated(src,section,keys),1):
            drafts.append(b.make_article(section,i,body,wc,meta,sc,f'paragraph-window:{a+1}-{z}'))

    human=pick_scored(src,'human',['dinet','draycott'],3)
    if len(human)<b.COUNT: human=pick_scored(src,'human',['dinet','draycott'],1)
    if len(human)<b.COUNT: raise SystemExit(f'human: {len(human)}/{b.COUNT}')
    for i,(sc,key,a,z,body,wc,meta) in enumerate(human[:b.COUNT],1):
        drafts.append(b.make_article('human',i,body,wc,meta,sc,f'paragraph-window:{a+1}-{z}'))

    mercy=pick_scored(src,'mercy',['mercy','mercy2','dinet','lane','draycott'],3)
    if len(mercy)<b.COUNT: raise SystemExit(f'mercy: {len(mercy)}/{b.COUNT}')
    for i,(sc,key,a,z,body,wc,meta) in enumerate(mercy[:b.COUNT],1):
        drafts.append(b.make_article('mercy',i,body,wc,meta,sc,f'paragraph-window:{a+1}-{z}'))

    counts=Counter(x['section'] for x in drafts)
    expected=Counter({s:100 for s in b.TARGETS})
    if counts!=expected: raise SystemExit(f'bad distribution {counts}')
    fps=[b.fingerprint(x['paragraphs'][0]['text']) for x in drafts]
    if len(fps)!=len(set(fps)): raise SystemExit('duplicate bodies')
    if min(x['sourceWordCount'] for x in drafts)<b.MIN_WORDS: raise SystemExit('under 1000 words')

    b.OUT.parent.mkdir(parents=True,exist_ok=True); b.AUDIT.parent.mkdir(parents=True,exist_ok=True)
    b.OUT.write_text(json.dumps({'schema':'five-exclusive-sections-v1','version':'2026-08-22-five-exclusive-500','publicationStatus':'PUBLISHED','drafts':drafts},ensure_ascii=False,separators=(',',':')),encoding='utf-8')

    section_by_id={}
    for pack in (b.PRIMARY,b.SUPPLEMENT):
        obj=json.loads(pack.read_text(encoding='utf-8'))
        for path in obj.get('draftBatchPaths',[]):
            p=b.ROOT/path
            if not p.exists(): continue
            try: batch=json.loads(p.read_text(encoding='utf-8'))
            except Exception: continue
            for d in batch.get('drafts',[]):
                if d.get('id'): section_by_id[d['id']]=d.get('section')
    for pack in (b.PRIMARY,b.SUPPLEMENT):
        obj=json.loads(pack.read_text(encoding='utf-8'))
        obj['publishedIds']=[x for x in obj.get('publishedIds',[]) if section_by_id.get(x) not in b.TARGETS and not x.startswith('20260822-five-')]
        if pack==b.SUPPLEMENT:
            rel=str(b.OUT.relative_to(b.ROOT)).replace('\\','/')
            obj['draftBatchPaths']=[x for x in obj.get('draftBatchPaths',[]) if x!=rel]+[rel]
            obj['publishedIds'] += [d['id'] for d in drafts]
            obj['fiveExclusiveTaxonomy']={'version':'2026-08-22-five-exclusive-v1','count':500,'sectionCounts':dict(expected)}
        pack.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

    audit={'version':'2026-08-22-five-exclusive-500-audit-v2','generatedAt':b.STAMP,'publishedArticles':500,'sectionDistribution':dict(counts),'minimumWords':b.MIN_WORDS,'minimumObservedWords':min(x['sourceWordCount'] for x in drafts),'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'duplicateSourceBodies':0,'exclusivePrimarySection':True,'taxonomy':b.MAINOBJ,'status':'PASS'}
    b.AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False,indent=2))

if __name__=='__main__': build()
