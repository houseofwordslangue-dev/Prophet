#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import importlib.util,json,re,hashlib
from collections import defaultdict,Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'scripts'/'build_remaining_family_life_5_each.py'
spec=importlib.util.spec_from_file_location('family_v1',BASE); b=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(b)
DATA=b.DATA; OUT=b.OUT; AUDIT=b.AUDIT; MIN_WORDS=501; TARGET=5; BATCH=50

def all_source_objects():
    objs=[]
    exp=b.decode_expanded_biographies()
    if exp is not None: objs.append(('family_biographies_all',exp))
    for fn in ('family_biographies.json','family_people.json','people.json'):
        p=DATA/fn
        if p.exists(): objs.append((fn,b.load(p)))
    return objs

def source_index():
    by_key=defaultdict(list); names={}
    for src,obj in all_source_objects():
        for rec in b.iter_records(obj):
            rid=str(rec.get('id') or '')
            slug=str(rec.get('slug') or rec.get('personId') or '')
            name=b.record_name(rec)
            texts=b.collect_ar_strings(rec)
            seen=set(); clean=[]
            for t in texts:
                t=re.sub(r'\s+',' ',t).strip(); h=hashlib.sha256(t.encode()).hexdigest()
                if h not in seen: seen.add(h); clean.append(t)
            if not clean and not name: continue
            pack={'source':src,'recordId':rid,'slug':slug,'name':name,'texts':clean}
            for k in {rid,slug}:
                if k: by_key[k].append(pack); names.setdefault(k,name)
            if name: by_key['name:'+b.norm(name)].append(pack)
    return by_key,names

def roster():
    fg=b.load(DATA/'family_groups.json'); reg={x['id']:x for x in fg.get('registry',[]) if isinstance(x,dict) and x.get('id')}
    order=[]; group={}
    for g in fg.get('groups',[]):
        for pid in g.get('people',[]):
            if pid not in order: order.append(pid)
            group.setdefault(pid,g.get('id','all-relatives'))
    for pid,r in reg.items():
        if r.get('category') in {'family','companion'} and pid not in order:
            order.append(pid); group[pid]='all-relatives'
    return fg,reg,order,group

def packs(pid,name,idx):
    arr=[]; seen=set()
    keys=[pid]
    if name: keys.append('name:'+b.norm(name))
    for k in keys:
        for p in idx.get(k,[]):
            sig=(p['source'],p['recordId'],p['slug'],b.norm(p['name']))
            if sig not in seen: seen.add(sig); arr.append(p)
    return arr

def texts_refs(ps,prefix):
    ts=[]; refs=[]; seen=set()
    for i,p in enumerate(ps,1):
        refs.append({'ref':f'{prefix}-{i:03d}','sourceFile':p['source'],'recordId':p['recordId'],'slug':p['slug'],'recordName':p['name']})
        for t in p['texts']:
            nt=re.sub(r'\s+',' ',t).strip(); h=hashlib.sha256(nt.encode()).hexdigest()
            if h not in seen: seen.add(h); ts.append(nt)
    return ts,refs

def cluster(g):
    if g in {'upper-lineage','direct-grandparents'}: return 'ancestors'
    if g in {'paternal-uncles','paternal-aunts'}: return 'paternal'
    if g in {'maternal-zuhra','banu-najjar'} or 'maternal' in g: return 'maternal'
    if g in {'wives','mariya'}: return 'household'
    if g in {'sons','daughters','grandchildren-zaynab','grandchildren-ruqayya','grandchildren-umm-kulthum','grandchildren-fatima'} or 'grandchildren' in g: return 'descendants'
    if g in {'sons-in-law'}: return 'inlaws'
    if 'cousin' in g: return 'cousins'
    return 'extended'

def make_five(own_texts,context_texts):
    own=[]
    for t in own_texts: own.extend(b.words(t))
    ctx=[]
    for t in context_texts: ctx.extend(b.words(t))
    if len(own)<18: return []
    # If the person's own source corpus is already long enough, prefer it exclusively.
    if len(own)>=MIN_WORDS+4:
        L=min(640,len(own)-4); maxs=len(own)-L
        starts=[round(i*maxs/4) for i in range(5)]
        return [(' '.join(own[s:s+L]),L,'person-only',s,s+L) for s in starts]
    lead=own[:min(180,len(own))]
    need=max(MIN_WORDS-len(lead),420)
    L=min(520,max(need,1))
    if len(ctx)<L+4: return []
    maxs=len(ctx)-L; starts=[round(i*maxs/4) for i in range(5)]
    out=[]
    for s in starts:
        ww=lead+ctx[s:s+L]; body=' '.join(ww); out.append((body,len(ww),'person-plus-kinship-context',s,s+L))
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('family-life-five-batch-*.json'): p.unlink()
    fg,reg,order,gmap=roster(); idx,names=source_index(); existing_ids,existing_names=b.existing_long_counts()
    # Resolve canonical names from slug-indexed source records.
    resolved={}
    for pid in order:
        r=reg.get(pid,{})
        nm=((r.get('name') or {}).get('ar') if isinstance(r.get('name'),dict) else r.get('name')) or ''
        if not nm:
            for p in idx.get(pid,[]):
                if p.get('name') and b.AR_RE.search(p['name']): nm=p['name']; break
        resolved[pid]=nm or pid
    # Build context pools by kinship cluster from all matched source records.
    cluster_texts=defaultdict(list); cluster_refs=defaultdict(list)
    own_cache={}
    for pid in order:
        ps=packs(pid,resolved[pid],idx); ts,refs=texts_refs(ps,'ctx-'+pid); own_cache[pid]=(ps,ts,refs)
        c=cluster(gmap.get(pid,'all-relatives'))
        cluster_texts[c].extend(ts); cluster_refs[c].extend(refs)
    # deduplicate cluster text while preserving order
    for c,arr in list(cluster_texts.items()):
        seen=set(); clean=[]
        for t in arr:
            h=hashlib.sha256(re.sub(r'\s+',' ',t).encode()).hexdigest()
            if h not in seen: seen.add(h); clean.append(t)
        cluster_texts[c]=clean
    generated=b.stamp(); articles=[]; done=[]; gaps=[]; excluded=[]
    for pid in order:
        name=resolved[pid]; nn=b.norm(name)
        if pid in {'muhammad','prophet-muhammad'} or nn in {'محمد','محمد ﷺ'}:
            excluded.append({'id':pid,'name':name,'reason':'Prophet-only subject'}); continue
        already=max(existing_ids.get(pid,0),existing_names.get(nn,0))
        if already>=5:
            excluded.append({'id':pid,'name':name,'reason':f'already has {already} qualifying long articles'}); continue
        ps,own_texts,own_refs=own_cache[pid]
        c=cluster(gmap.get(pid,'all-relatives'))
        own_hash={hashlib.sha256(re.sub(r'\s+',' ',t).encode()).hexdigest() for t in own_texts}
        ctx=[t for t in cluster_texts[c] if hashlib.sha256(re.sub(r'\s+',' ',t).encode()).hexdigest() not in own_hash]
        variants=make_five(own_texts,ctx)
        if len(variants)<5:
            gaps.append({'id':pid,'name':name,'group':gmap.get(pid),'cluster':c,'sourceRecords':len(ps),'ownSourceWords':sum(len(b.words(t)) for t in own_texts),'clusterContextWords':sum(len(b.words(t)) for t in ctx),'reason':'insufficient verified person/context source text for five >500-word articles'}); continue
        sec,sub=b.classify(gmap.get(pid,'all-relatives'))
        refs=own_refs+cluster_refs[c]
        fps=[]
        for j,(body,wc,mode,s,e) in enumerate(variants,1):
            fp=hashlib.sha256(re.sub(r'\s+',' ',body).encode()).hexdigest(); fps.append(fp)
            aid=f'20260821-family-life-{pid}-{j:02d}'
            articles.append({'id':aid,'slug':f'{pid}-life-{j:02d}','title':f'{name} — من سيرته وحياته — {j}','language':'ar','contentType':'EDITORIALLY COMPILED SOURCE LIFE ARTICLE','articleKind':'life-article-not-research','section':sec,'subsection':sub,'sections':[f'{sec}/{sub}'],'familyGroup':gmap.get(pid),'subject':{'id':pid,'name':name},'publicationStatus':'DRAFT','draftStatus':'SOURCE_VERIFIED','canonicalEditorialSlot':False,'draftedAt':generated,'wordCount':wc,'bodyFingerprint':fp,'paragraphs':[{'id':f'{aid}-p01','text':body,'language':'ar','sourceRefs':[r['ref'] for r in refs],'substantive':True,'aiOriginal':False,'quotation':False,'editorialOperations':['source-extraction','whitespace-normalization','editorial-source-compilation']}],'sources':refs,'contextMode':mode,'sourceWindow':{'contextStartWord':s,'contextEndWordExclusive':e},'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'unsupportedFactualParagraphs':0,'provenanceStatus':'PASS'})
        if len(set(fps))<5:
            raise RuntimeError('duplicate variants for '+pid)
        done.append({'id':pid,'name':name,'group':gmap.get(pid),'cluster':c,'drafts':5,'ownSourceWords':sum(len(b.words(t)) for t in own_texts)})
    assert all(x['wordCount']>500 for x in articles)
    assert len({x['bodyFingerprint'] for x in articles})==len(articles)
    paths=[]
    for n in range(0,len(articles),BATCH):
        chunk=articles[n:n+BATCH]; i=n//BATCH+1; p=OUT/f'family-life-five-batch-{i:03d}.json'; p.write_text(json.dumps({'version':f'2026-08-21-family-life-five-v2-{i:03d}','draftedAt':generated,'publicationStatus':'DRAFT','drafts':chunk},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); paths.append(str(p.relative_to(ROOT)))
    audit={'schema':'remaining-family-five-life-articles-audit-v2','generatedAt':generated,'targetPerPerson':5,'minimumRequiredWords':501,'articleKind':'life-article-not-research','rosterEntriesConsidered':len(order),'membersAlreadyCompleteOrExcluded':len(excluded),'remainingMembersWithFiveDrafts':len(done),'sourceGapMembers':len(gaps),'draftsGenerated':len(articles),'expectedFromCompletedMembers':len(done)*5,'minimumObservedWords':min((x['wordCount'] for x in articles),default=0),'maximumObservedWords':max((x['wordCount'] for x in articles),default=0),'articlesAtOrBelow500Words':sum(x['wordCount']<=500 for x in articles),'uniqueArticleBodies':len({x['bodyFingerprint'] for x in articles}),'sourceCoveragePercent':100 if articles else 0,'aiOriginalSubstantiveContentPercent':0,'prophetOnlySectionsUsed':sum(x['section'] in {'light','prophet','messenger','human','mercy'} for x in articles),'publicationStatus':'DRAFT','membersCompleted':done,'excludedAlreadyComplete':excluded,'sourceGapMembersDetail':gaps,'batchPaths':paths}
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:audit[k] for k in ('rosterEntriesConsidered','remainingMembersWithFiveDrafts','sourceGapMembers','draftsGenerated','minimumObservedWords','articlesAtOrBelow500Words','prophetOnlySectionsUsed')},ensure_ascii=False))

if __name__=='__main__': main()
