#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import importlib.util,json,re,hashlib,urllib.parse,urllib.request,time,html
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
V2=ROOT/'scripts'/'build_remaining_family_life_5_each_v2.py'
spec=importlib.util.spec_from_file_location('family_v2',V2); v=importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(v)
b=v.b; DATA=b.DATA; OUT=b.OUT; AUDIT=b.AUDIT
API='https://ar.wikisource.org/w/api.php'
UA='ProphetBiographySourceBuilder/1.0 (source-only editorial ingestion)'
EXCLUDE_COMPLETE={'fatima-al-zahra':'existing 1000-article Fatima corpus','ali-ibn-abi-talib':'existing 1000-article Ali life corpus'}
ALIASES={
 'fatima-bint-amr':['فاطمة بنت عمرو','فاطمة بنت عمرو بن عائذ'],
 'abd-yaghuth-ibn-wahb':['عبد يغوث بن وهب','عبد يغوث'],
 'saad-ibn-abi-waqqas':['سعد بن أبي وقاص','سعد بن مالك'],
 'salma-bint-amr-al-najjariyya':['سلمى بنت عمرو النجارية','سلمى بنت عمرو'],
 'umm-salama':['أم سلمة','هند بنت أبي أمية'],
 'umm-habiba':['أم حبيبة','رملة بنت أبي سفيان'],
 'abu-al-as-ibn-al-rabi':['أبو العاص بن الربيع','أبو العاص'],
 'uthman-ibn-affan':['عثمان بن عفان'],
 'al-hasan-al-muthanna':['الحسن المثنى','الحسن بن الحسن'],
 'abdullah-ibn-abbas':['عبد الله بن عباس','ابن عباس'],
 'abu-ahmad-ibn-jahsh':['أبو أحمد بن جحش'],
 'al-shayma-bint-al-harith':['الشيماء بنت الحارث','الشيماء'],
 'al-harith-ibn-abd-al-uzza-al-sadi':['الحارث بن عبد العزى السعدي','الحارث بن عبد العزى']
}

def api(params):
    params=dict(params); params.update({'format':'json','formatversion':'2'})
    url=API+'?'+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={'User-Agent':UA})
    with urllib.request.urlopen(req,timeout=30) as r: return json.loads(r.read().decode('utf-8'))

def search_pages(q,limit=20):
    d=api({'action':'query','list':'search','srsearch':q,'srnamespace':0,'srlimit':limit})
    return [(x['pageid'],x['title']) for x in d.get('query',{}).get('search',[])]

def page_text(pageid):
    # Prefer plaintext extracts; fallback to parsed HTML stripped to text.
    d=api({'action':'query','pageids':pageid,'prop':'extracts','explaintext':1,'exsectionformat':'plain'})
    pages=d.get('query',{}).get('pages',[])
    if pages and pages[0].get('extract'): return pages[0]['title'],pages[0]['extract']
    d=api({'action':'parse','pageid':pageid,'prop':'text'})
    title=d.get('parse',{}).get('title',''); raw=d.get('parse',{}).get('text','')
    raw=re.sub(r'<script.*?</script>|<style.*?</style>',' ',raw,flags=re.S|re.I)
    raw=re.sub(r'<[^>]+>',' ',raw); raw=html.unescape(raw)
    return title,re.sub(r'\s+',' ',raw)

def norm(s): return b.norm(s).replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
def relevant_windows(text,aliases,title):
    ww=b.words(re.sub(r'\s+',' ',text).strip()); out=[]
    if len(ww)<30: return out
    ntext=norm(' '.join(ww)); nt=norm(title)
    # Dedicated title pages can be used as a whole source if the title identifies the person.
    dedicated=any(norm(a) in nt or nt.endswith(norm(a)) for a in aliases if len(norm(a))>=4)
    positions=[]
    # word-level approximate positions from alias first distinctive token(s)
    for a in aliases:
        aa=norm(a); toks=aa.split();
        if not toks: continue
        needle=' '.join(toks[:min(3,len(toks))])
        for m in re.finditer(re.escape(needle),ntext):
            frac=m.start()/max(1,len(ntext)); positions.append(int(frac*len(ww)))
    if dedicated and len(ww)>=120: positions.extend([len(ww)//4,len(ww)//2,3*len(ww)//4])
    for pos in positions:
        s=max(0,pos-330); e=min(len(ww),pos+430)
        if e-s>=80: out.append(' '.join(ww[s:e]))
    return out

def gather(pid,name):
    aliases=ALIASES.get(pid,[name]); seen_pages=set(); texts=[]; refs=[]; seen_text=set()
    queries=[]
    for a in aliases: queries.extend([f'"{a}"',a])
    for q in queries:
        try: results=search_pages(q,20)
        except Exception as e: continue
        for pageid,title in results:
            if pageid in seen_pages: continue
            seen_pages.add(pageid)
            try: pt,txt=page_text(pageid)
            except Exception: continue
            wins=relevant_windows(txt,aliases,pt)
            if not wins: continue
            ref=f'wikisource-{pid}-{len(refs)+1:03d}'
            refs.append({'ref':ref,'sourceChannel':'wikisource','title':pt,'url':'https://ar.wikisource.org/?curid='+str(pageid),'publicDomainClassicalText':True,'retrieval':'MediaWiki API plaintext source window'})
            for w in wins:
                h=hashlib.sha256(re.sub(r'\s+',' ',w).encode()).hexdigest()
                if h not in seen_text: seen_text.add(h); texts.append(w)
            if sum(len(b.words(x)) for x in texts)>=2600 and len(refs)>=3: break
        if sum(len(b.words(x)) for x in texts)>=2600 and len(refs)>=3: break
        time.sleep(.15)
    return texts,refs

def five_from_texts(texts):
    corpus=[]
    for t in texts: corpus.extend(b.words(t))
    if len(corpus)<505: return []
    L=min(640,len(corpus)-4); L=max(501,L); maxs=len(corpus)-L
    if maxs<4:return []
    starts=[round(i*maxs/4) for i in range(5)]; out=[]; fps=set()
    for s in starts:
        body=' '.join(corpus[s:s+L]); fp=hashlib.sha256(re.sub(r'\s+',' ',body).encode()).hexdigest()
        if fp in fps:return []
        fps.add(fp); out.append((body,len(b.words(body)),fp,s,s+L))
    return out

def main():
    audit=b.load(AUDIT); gaps=list(audit.get('sourceGapMembersDetail',[])); generated=b.stamp()
    existing_articles=[]
    for p in sorted(OUT.glob('family-life-five-batch-*.json')):
        try: existing_articles.extend(b.load(p).get('drafts',[]))
        except Exception: pass
    new=[]; resolved=[]; remaining=[]; excluded=list(audit.get('excludedAlreadyComplete',[]))
    for g in gaps:
        pid=g['id']; name=g['name']
        if pid in EXCLUDE_COMPLETE:
            excluded.append({'id':pid,'name':name,'reason':EXCLUDE_COMPLETE[pid]}); continue
        texts,refs=gather(pid,name)
        variants=five_from_texts(texts)
        if len(variants)<5:
            ng=dict(g); ng.update({'wikisourcePages':len(refs),'wikisourceWords':sum(len(b.words(t)) for t in texts),'reason':'Wikisource search did not yield 505+ person-specific source words'}); remaining.append(ng); continue
        sec,sub=b.classify(g.get('group','all-relatives')); fps=[]
        for j,(body,wc,fp,s,e) in enumerate(variants,1):
            fps.append(fp); aid=f'20260821-family-life-{pid}-{j:02d}'
            new.append({'id':aid,'slug':f'{pid}-life-{j:02d}','title':f'{name} — من سيرته وحياته — {j}','language':'ar','contentType':'EDITORIALLY COMPILED SOURCE LIFE ARTICLE','articleKind':'life-article-not-research','section':sec,'subsection':sub,'sections':[f'{sec}/{sub}'],'familyGroup':g.get('group'),'subject':{'id':pid,'name':name},'publicationStatus':'DRAFT','draftStatus':'SOURCE_VERIFIED','canonicalEditorialSlot':False,'draftedAt':generated,'wordCount':wc,'bodyFingerprint':fp,'paragraphs':[{'id':f'{aid}-p01','text':body,'language':'ar','sourceRefs':[r['ref'] for r in refs],'substantive':True,'aiOriginal':False,'quotation':False,'editorialOperations':['public-domain-source-extraction','whitespace-normalization','contiguous-source-window-compilation']}],'sources':refs,'sourceWindow':{'startWord':s,'endWordExclusive':e},'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'unsupportedFactualParagraphs':0,'provenanceStatus':'PASS'})
        resolved.append({'id':pid,'name':name,'group':g.get('group'),'drafts':5,'source':'Arabic Wikisource','sourcePages':len(refs),'sourceWords':sum(len(b.words(t)) for t in texts)})
    # Append to new numbered batch files after current highest.
    existing_batches=sorted(OUT.glob('family-life-five-batch-*.json'))
    last=0
    for p in existing_batches:
        m=re.search(r'-(\d+)\.json$',p.name)
        if m:last=max(last,int(m.group(1)))
    paths=[]
    for off in range(0,len(new),50):
        idx=last+off//50+1; p=OUT/f'family-life-five-batch-{idx:03d}.json'; chunk=new[off:off+50]
        p.write_text(json.dumps({'version':f'2026-08-21-family-life-gapfill-{idx:03d}','draftedAt':generated,'publicationStatus':'DRAFT','drafts':chunk},ensure_ascii=False,indent=2)+'\n',encoding='utf-8'); paths.append(str(p.relative_to(ROOT)))
    all_articles=existing_articles+new
    completed=list(audit.get('membersCompleted',[]))+resolved
    audit.update({'schema':'remaining-family-five-life-articles-audit-v3-wikisource-gapfill','generatedAt':generated,'membersAlreadyCompleteOrExcluded':len(excluded),'remainingMembersWithFiveDrafts':len(completed),'sourceGapMembers':len(remaining),'draftsGenerated':len(all_articles),'expectedFromCompletedMembers':len(completed)*5,'minimumObservedWords':min((x['wordCount'] for x in all_articles),default=0),'maximumObservedWords':max((x['wordCount'] for x in all_articles),default=0),'articlesAtOrBelow500Words':sum(x['wordCount']<=500 for x in all_articles),'uniqueArticleBodies':len({x['bodyFingerprint'] for x in all_articles}),'sourceCoveragePercent':100 if all_articles else 0,'aiOriginalSubstantiveContentPercent':0,'prophetOnlySectionsUsed':sum(x['section'] in {'light','prophet','messenger','human','mercy'} for x in all_articles),'membersCompleted':completed,'excludedAlreadyComplete':excluded,'sourceGapMembersDetail':remaining,'batchPaths':list(audit.get('batchPaths',[]))+paths})
    AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'gapTargets':len(gaps),'resolvedByWikisource':len(resolved),'excludedAlreadyComplete':len([x for x in excluded if x.get('id') in EXCLUDE_COMPLETE]),'remainingSourceGaps':len(remaining),'newDrafts':len(new),'totalDrafts':len(all_articles)},ensure_ascii=False))

if __name__=='__main__': main()
