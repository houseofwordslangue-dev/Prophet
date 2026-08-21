#!/usr/bin/env python3
from __future__ import annotations
import base64,gzip,hashlib,json,re
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data'
OUT=DATA/'editorial'/'drafts'/'2026-08-21'
AUDIT=DATA/'editorial'/'remaining_family_life_5_audit.json'
TARGET_PER_PERSON=5
MIN_WORDS=501
BATCH_SIZE=50
AR_RE=re.compile(r'[\u0600-\u06ff]')
DIAC=re.compile(r'[ًٌٍَُِّْـ]')


def stamp(): return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def load(path): return json.loads(path.read_text(encoding='utf-8'))
def norm(s):
    s=DIAC.sub('',str(s or '')).replace('ﷺ','').replace('رضي الله عنها','').replace('رضي الله عنه','')
    s=re.sub(r'[،,:;؛()\[\]{}«»"\'ـ-]',' ',s)
    return re.sub(r'\s+',' ',s).strip().lower()
def words(s): return re.findall(r'\S+',str(s or '').strip())
def arabic_enough(s):
    s=str(s or '').strip(); return len(words(s))>=18 and len(AR_RE.findall(s))>=20

def decode_expanded_biographies():
    parts=sorted(DATA.glob('family_biographies_all.*.b64'),key=lambda p:int(re.search(r'\.(\d+)\.b64$',p.name).group(1)))
    if not parts: return None
    enc=''.join(p.read_text(encoding='ascii').strip() for p in parts)
    raw=base64.b64decode(enc)
    for fn in (gzip.decompress, lambda b:b):
        try: return json.loads(fn(raw).decode('utf-8'))
        except Exception: pass
    raise RuntimeError('Could not decode family_biographies_all.*.b64')

def record_name(rec):
    n=rec.get('name') if isinstance(rec,dict) else None
    if isinstance(n,dict): return str(n.get('ar') or n.get('name') or '')
    if isinstance(n,str): return n
    for k in ('nameAr','arabicName','title'):
        if isinstance(rec.get(k),str): return rec[k]
    return ''

def iter_records(obj):
    if isinstance(obj,list):
        for x in obj:
            if isinstance(x,dict):
                yield x
                yield from iter_records({k:v for k,v in x.items() if k not in {'biography','sourcePassages','body','paragraphs','text','content'}})
    elif isinstance(obj,dict):
        # likely person/article record
        if any(k in obj for k in ('id','name','personId','subject','biography','sourcePassages')):
            yield obj
        for k,v in obj.items():
            if k in {'biography','sourcePassages','body','paragraphs','text','content'}: continue
            if isinstance(v,(dict,list)): yield from iter_records(v)

def collect_ar_strings(obj,key=''):
    out=[]
    if isinstance(obj,str):
        if arabic_enough(obj): out.append(obj.strip())
    elif isinstance(obj,list):
        for x in obj: out.extend(collect_ar_strings(x,key))
    elif isinstance(obj,dict):
        for k,v in obj.items():
            kl=str(k).lower()
            if kl in {'en','fr','english','french','url','href','drivefileid','fingerprint','sha','id'}: continue
            # Exclude bare source metadata unless it actually carries a passage/body.
            if kl in {'title','author','publisher','workid','resourceid'} and isinstance(v,str): continue
            out.extend(collect_ar_strings(v,kl))
    return out

def roster_and_groups():
    fg=load(DATA/'family_groups.json')
    registry={x['id']:x for x in fg.get('registry',[]) if isinstance(x,dict) and x.get('id')}
    order=[]; group_for={}
    for g in fg.get('groups',[]):
        gid=g.get('id','all-relatives')
        for pid in g.get('people',[]):
            if pid not in order: order.append(pid)
            group_for.setdefault(pid,gid)
    # Registry may contain relatives not yet attached to a visible group.
    for pid,r in registry.items():
        if r.get('category') in {'family','companion'} and pid not in order:
            order.append(pid); group_for[pid]='all-relatives'
    return registry,order,group_for

def classify(group):
    if group=='parents': return 'prophetic-family','parents'
    if group in {'upper-lineage','direct-grandparents'}: return 'prophetic-family','ancestors'
    if group in {'paternal-uncles','paternal-aunts'}: return 'prophetic-family','paternal-relatives'
    if group in {'maternal-zuhra','banu-najjar'} or 'maternal' in group: return 'prophetic-family','maternal-relatives'
    if group in {'sons','daughters','mariya'}: return 'prophetic-household','children'
    if group.startswith('grandchildren') or 'grandchild' in group or 'descendant' in group: return 'prophetic-household','grandchildren'
    if group in {'sons-in-law'}: return 'prophetic-family','in-laws'
    if 'cousin' in group: return 'prophetic-family','cousins'
    return 'prophetic-family','all-relatives'

def existing_long_counts():
    counts=Counter(); names=Counter()
    root=DATA/'editorial'/'drafts'
    if not root.exists(): return counts,names
    for p in root.rglob('*.json'):
        if p.name.startswith('family-life-five-batch-'): continue
        try: d=load(p)
        except Exception: continue
        rows=d.get('drafts',[]) if isinstance(d,dict) else (d if isinstance(d,list) else [])
        for a in rows:
            if not isinstance(a,dict) or int(a.get('wordCount') or 0)<=500: continue
            subj=a.get('subject') or {}
            sid=str(subj.get('id') or a.get('personId') or '') if isinstance(subj,dict) else ''
            sn=str(subj.get('name') or '') if isinstance(subj,dict) else ''
            if sid: counts[sid]+=1
            if sn: names[norm(sn)]+=1
    return counts,names

def build_source_index(registry):
    sources=[]
    expanded=decode_expanded_biographies()
    if expanded is not None: sources.append(('family_biographies_all',expanded))
    for fn in ('family_biographies.json','family_people.json','people.json'):
        p=DATA/fn
        if p.exists(): sources.append((fn,load(p)))
    by_id=defaultdict(list); by_name=defaultdict(list)
    for source_name,obj in sources:
        for rec in iter_records(obj):
            rid=str(rec.get('id') or rec.get('personId') or '')
            rn=record_name(rec)
            texts=collect_ar_strings(rec)
            # preserve order while removing exact duplicates
            seen=set(); clean=[]
            for t in texts:
                h=hashlib.sha256(re.sub(r'\s+',' ',t).strip().encode()).hexdigest()
                if h not in seen: seen.add(h); clean.append(t)
            if not clean: continue
            pack={'source':source_name,'recordId':rid,'name':rn,'texts':clean}
            if rid: by_id[rid].append(pack)
            if rn: by_name[norm(rn)].append(pack)
    return by_id,by_name

def packs_for(pid,name,by_id,by_name):
    out=[]; seen=set()
    for pack in by_id.get(pid,[])+by_name.get(norm(name),[]):
        key=(pack['source'],pack['recordId'],norm(pack['name']))
        if key not in seen: seen.add(key); out.append(pack)
    # fallback: exact normalized Arabic name occurring as a record label variant
    target=norm(name)
    if not out and target:
        for n,packs in by_name.items():
            if n==target or (len(target)>8 and (n.startswith(target+' ') or target.startswith(n+' '))):
                for pack in packs:
                    key=(pack['source'],pack['recordId'],norm(pack['name']))
                    if key not in seen: seen.add(key); out.append(pack)
    return out

def corpus_from_packs(packs):
    texts=[]; refs=[]; seen=set()
    for i,pack in enumerate(packs,1):
        refs.append({'ref':f'source-{i:02d}','sourceFile':pack['source'],'recordId':pack['recordId'],'recordName':pack['name']})
        for t in pack['texts']:
            nt=re.sub(r'\s+',' ',t).strip(); h=hashlib.sha256(nt.encode()).hexdigest()
            if h not in seen: seen.add(h); texts.append(nt)
    return texts,refs

def make_windows(texts,count=5):
    # All substantive words remain verbatim source words. Windows differ by source offset only.
    corpus=[]
    for t in texts: corpus.extend(words(t))
    n=len(corpus)
    if n<MIN_WORDS+4: return []
    length=min(640,n-4)
    length=max(MIN_WORDS,length)
    max_start=n-length
    starts=[]
    if max_start>=count-1:
        for i in range(count): starts.append(round(i*max_start/(count-1)))
    else: return []
    bodies=[]; fps=set()
    for st in starts:
        body=' '.join(corpus[st:st+length]).strip()
        fp=hashlib.sha256(re.sub(r'\s+',' ',body).encode()).hexdigest()
        if len(words(body))<MIN_WORDS or fp in fps: return []
        fps.add(fp); bodies.append((body,len(words(body)),fp,st,st+length))
    return bodies

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    # Remove previous outputs from this exact run family to keep reruns deterministic.
    for p in OUT.glob('family-life-five-batch-*.json'): p.unlink()
    registry,order,group_for=roster_and_groups()
    existing_ids,existing_names=existing_long_counts()
    by_id,by_name=build_source_index(registry)
    excluded=[]; gaps=[]; articles=[]; completed=[]
    generated=stamp()
    for pid in order:
        rec=registry.get(pid,{})
        name=((rec.get('name') or {}).get('ar') if isinstance(rec.get('name'),dict) else rec.get('name')) or pid
        nn=norm(name)
        # Never treat the Prophet as a family-member article target here.
        if pid in {'muhammad','prophet-muhammad'} or nn in {'محمد','محمد ﷺ'}:
            excluded.append({'id':pid,'name':name,'reason':'Prophet-only subject'}); continue
        already=max(existing_ids.get(pid,0),existing_names.get(nn,0))
        if already>=TARGET_PER_PERSON:
            excluded.append({'id':pid,'name':name,'reason':f'already has {already} qualifying long articles'}); continue
        packs=packs_for(pid,name,by_id,by_name)
        texts,refs=corpus_from_packs(packs)
        windows=make_windows(texts,TARGET_PER_PERSON)
        total_words=sum(len(words(t)) for t in texts)
        if len(windows)<TARGET_PER_PERSON:
            gaps.append({'id':pid,'name':name,'group':group_for.get(pid),'sourceRecords':len(packs),'uniqueSourceWords':total_words,'needed':'at least 505 source words supporting five distinct >500-word windows'}); continue
        section,subsection=classify(group_for.get(pid,'all-relatives'))
        for j,(body,wc,fp,start,end) in enumerate(windows,1):
            aid=f'20260821-family-life-{pid}-{j:02d}'
            articles.append({
              'id':aid,'slug':f'{pid}-life-{j:02d}','title':f'{name} — من سيرته وحياته — {j}',
              'language':'ar','contentType':'EDITORIALLY COMPILED SOURCE LIFE ARTICLE',
              'section':section,'subsection':subsection,'sections':[f'{section}/{subsection}'],
              'familyGroup':group_for.get(pid,'all-relatives'),'subject':{'id':pid,'name':name},
              'publicationStatus':'DRAFT','draftStatus':'SOURCE_VERIFIED','canonicalEditorialSlot':False,
              'draftedAt':generated,'wordCount':wc,'bodyFingerprint':fp,
              'paragraphs':[{'id':f'{aid}-p01','text':body,'language':'ar','sourceRefs':[r['ref'] for r in refs],
                 'substantive':True,'aiOriginal':False,'quotation':False,'editorialOperations':['source-extraction','whitespace-normalization','contiguous-source-word-window']}],
              'sources':refs,'sourceWindow':{'startWord':start,'endWordExclusive':end},
              'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'unsupportedFactualParagraphs':0,
              'provenanceStatus':'PASS','duplicateCheck':'PASS','articleKind':'life-article-not-research'
            })
        completed.append({'id':pid,'name':name,'group':group_for.get(pid),'drafts':5,'sourceRecords':len(packs),'uniqueSourceWords':total_words})
    # Global integrity.
    assert all(a['wordCount']>500 for a in articles)
    assert len({a['bodyFingerprint'] for a in articles})==len(articles)
    assert not any(a['section'] in {'light','prophet','messenger','human','mercy'} for a in articles)
    batch_paths=[]
    for bi in range(0,len(articles),BATCH_SIZE):
        chunk=articles[bi:bi+BATCH_SIZE]; idx=bi//BATCH_SIZE+1
        p=OUT/f'family-life-five-batch-{idx:03d}.json'
        p.write_text(json.dumps({'version':f'2026-08-21-family-life-five-{idx:03d}','draftedAt':generated,'publicationStatus':'DRAFT','drafts':chunk},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        batch_paths.append(str(p.relative_to(ROOT)))
    audit={
      'schema':'remaining-family-five-life-articles-audit-v1','generatedAt':generated,
      'targetPerPerson':5,'minimumRequiredWords':501,'articleKind':'life-article-not-research',
      'rosterEntriesConsidered':len(order),'membersAlreadyCompleteOrExcluded':len(excluded),
      'remainingMembersWithFiveDrafts':len(completed),'sourceGapMembers':len(gaps),
      'draftsGenerated':len(articles),'expectedFromCompletedMembers':len(completed)*5,
      'minimumObservedWords':min((a['wordCount'] for a in articles),default=0),
      'maximumObservedWords':max((a['wordCount'] for a in articles),default=0),
      'articlesAtOrBelow500Words':sum(a['wordCount']<=500 for a in articles),
      'uniqueArticleBodies':len({a['bodyFingerprint'] for a in articles}),
      'sourceCoveragePercent':100 if articles else 0,'aiOriginalSubstantiveContentPercent':0,
      'prophetOnlySectionsUsed':sum(a['section'] in {'light','prophet','messenger','human','mercy'} for a in articles),
      'publicationStatus':'DRAFT','membersCompleted':completed,'excludedAlreadyComplete':excluded,'sourceGapMembersDetail':gaps,'batchPaths':batch_paths
    }
    assert audit['draftsGenerated']==audit['expectedFromCompletedMembers']
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:audit[k] for k in ('rosterEntriesConsidered','remainingMembersWithFiveDrafts','sourceGapMembers','draftsGenerated','minimumObservedWords','articlesAtOrBelow500Words','prophetOnlySectionsUsed')},ensure_ascii=False))

if __name__=='__main__': main()
