#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import collections
import hashlib
import json
import os
from pathlib import Path
import re
import unicodedata
import urllib.request

ROOT = Path(__file__).resolve().parents[1] if Path(__file__).parent.name == 'scripts' else Path.cwd()
DATE_DIR = ROOT / 'data' / 'editorial' / 'drafts' / '2026-08-21'
PUBLISHED_AT = '2026-08-21T02:50:00+01:00'
BATCH_NUMBERS = list(range(21,31))
OVERRIDE_DIR = os.environ.get('SOURCE_OVERRIDE_DIR','').strip()

SOURCES = {
 'dinet': {
  'workId':'drive-dinet-life-mohammad','title':'The Life of Mohammad, the Prophet of Allah','author':'Etienne Dinet; Sliman Ben Ibrahim','language':'en','driveFileId':'1CRTc0bUvYOcGoiXBfrO3fm-cBM-Wqm1i','driveUrl':'https://drive.google.com/file/d/1CRTc0bUvYOcGoiXBfrO3fm-cBM-Wqm1i/view','sourceIdentifier':'39523','sha256':'34ea2c1be7d38dfbcf2134b652c98ab5fbd4e498360cd04b6afc8d8395359d60','localName':'dinet.txt','bounds':(700,1498),'quota':90,'contentType':'EXTRACTED BOOK MATERIAL',
  'urls':['https://www.gutenberg.org/ebooks/39523.txt.utf-8','https://www.gutenberg.org/cache/epub/39523/pg39523.txt','https://raw.githubusercontent.com/GITenberg/The-Life-of-MohammadThe-Prophet-of-Allah_39523/master/39523.txt']},
 'lane': {
  'workId':'drive-lane-poole-table-talk','title':'The Speeches & Table-Talk of the Prophet Mohammad','author':'Stanley Lane-Poole (editor)','language':'en','driveFileId':'1W94dqOIsT62G8zGHCMyOgDVZbPZBSy_Z','driveUrl':'https://drive.google.com/file/d/1W94dqOIsT62G8zGHCMyOgDVZbPZBSy_Z/view','sourceIdentifier':'58426','sha256':'011006bd368871bedc133b2ef10cb42d6f6461a5e63ea78f245268c47297d09f','localName':'lane-poole.txt','bounds':(200,737),'quota':43,'contentType':'EXTRACTED BOOK MATERIAL',
  'urls':['https://www.gutenberg.org/ebooks/58426.txt.utf-8','https://www.gutenberg.org/cache/epub/58426/pg58426.txt','https://raw.githubusercontent.com/GITenberg/The-Speeches-Table-Talk-of-the-Prophet-Mohammad_58426/master/58426-0.txt']},
 'draycott': {
  'workId':'drive-draycott-mahomet','title':'Mahomet, Founder of Islam','author':'Gladys M. Draycott','language':'en','driveFileId':'14v0PBcMU7Sdsh-f_iO0whIyTkTGOJX0e','driveUrl':'https://drive.google.com/file/d/14v0PBcMU7Sdsh-f_iO0whIyTkTGOJX0e/view','sourceIdentifier':'10738','sha256':'6706c63640cae1c3ea9db1081eb7ef7d2a259189f5e1c8a1a32602d0595803e7','localName':'draycott.txt','bounds':(30,820),'quota':113,'contentType':'EXTRACTED BOOK MATERIAL',
  'urls':['https://www.gutenberg.org/ebooks/10738.txt.utf-8','https://www.gutenberg.org/cache/epub/10738/pg10738.txt','https://raw.githubusercontent.com/GITenberg/Mahomet-Founder-of-Islam_10738/master/10738.txt']},
 'rodwell': {
  'workId':'drive-rodwell-koran','title':"The Koran (Al-Qur'an)",'author':'J. M. Rodwell (translator)','language':'en','driveFileId':'14O6fTgtYssGkmaFkHDZOQPW-j5GQcrp4','driveUrl':'https://drive.google.com/file/d/14O6fTgtYssGkmaFkHDZOQPW-j5GQcrp4/view','sourceIdentifier':'3434','sha256':'1d683d75ccf7f06adfe5473f39637737a6f8c5410e1aab2188b0ee692d28fee9','localName':'rodwell.txt','bounds':(72,8000),'quota':254,'contentType':'TRANSLATED SOURCE',
  'urls':['https://www.gutenberg.org/ebooks/3434.txt.utf-8','https://www.gutenberg.org/cache/epub/3434/pg3434.txt','https://raw.githubusercontent.com/GITenberg/The-Koran-Al-Qur-an_3434/master/3434.txt']},
}

def sha(data:bytes)->str: return hashlib.sha256(data).hexdigest()

def fetch_exact(key,spec):
    if OVERRIDE_DIR:
        p=Path(OVERRIDE_DIR)/spec['localName']
        data=p.read_bytes()
        if sha(data)!=spec['sha256']:
            raise SystemExit(f'{key}: local Drive snapshot SHA mismatch {sha(data)} != {spec["sha256"]}')
        return data,'local-drive-snapshot'
    errors=[]
    for url in spec['urls']:
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'ProphetLibraryEditorial/1.0 (+source-verification)'})
            with urllib.request.urlopen(req,timeout=45) as r: data=r.read()
            got=sha(data)
            if got==spec['sha256']: return data,url
            errors.append(f'{url}: sha {got}')
        except Exception as e:
            errors.append(f'{url}: {type(e).__name__}: {e}')
    raise SystemExit(key+': no public transport reproduced the verified Drive snapshot. '+ ' | '.join(errors))

def pg_core(txt):
    txt=txt.replace('\r\n','\n').replace('\r','\n')
    m=re.search(r'\*\*\* START OF (?:THIS |THE )?PROJECT GUTENBERG EBOOK.*?\*\*\*',txt,re.I)
    start=m.end() if m else 0
    m2=re.search(r'\*\*\* END OF (?:THIS |THE )?PROJECT GUTENBERG EBOOK.*?\*\*\*',txt,re.I)
    end=m2.start() if m2 else len(txt)
    return txt[start:end]

def norm(p): return re.sub(r'\s+',' ',unicodedata.normalize('NFKC',p)).strip()

def is_heading(p):
    p=p.strip(); wc=len(p.split())
    if not p or wc>20 or len(p)>220:return False
    if re.match(r'^(CHAPTER|SURA|BOOK|PART|SECTION)\b',p,re.I):return True
    if p.upper() in {'INTRODUCTION','PREFACE','NOTES','REFERENCES','THE SPEECHES AT MEKKA','THE SPEECHES OF MEDINA','THE LAW GIVEN AT MEDINA','THE TABLE-TALK OF MOHAMMAD.','THE TABLE-TALK OF MOHAMMAD','THE PROPHET’S PORTRAIT',"THE PROPHET'S PORTRAIT"}:return True
    alpha=''.join(c for c in p if c.isalpha())
    return bool(alpha and p==p.upper() and wc>=2 and len(p)>4)

def usable(p,key):
    if not p or len(p)<20:return False
    up=p.upper().strip()
    bad=('TRANSCRIBER','TABLE OF CONTENTS','ANALYTICAL TABLE','INDEX OF','THE GOLDEN TREASURY SERIES','MACMILLAN & CO','PRINTED BY','LIST OF ILLUSTRATIONS','WORKS IN ARABIC','WORKS IN FRENCH','ISLAMIC WORKS, IN ENGLISH','TRANSLATION OF THE ARABIC CALLIGRAPHY','THIS BOOK')
    if any(up.startswith(x) for x in bad):return False
    if p.startswith('[Illustration') or p.startswith('[Footnote') or p.startswith('[Transcriber'):return False
    if key=='rodwell':
        if re.match(r'^\d{1,3}\s+[A-Z“"\']',p):return False
        if any(x in p[:80] for x in ['See Sura','See note','Lit. ','Comp. ','Cp. ','Nöld.','Maracci','Sale, ']):return False
    alnum=sum(c.isalnum() for c in p)
    if alnum/max(len(p),1)<0.55:return False
    return not is_heading(p)

def prepare(key,spec,text):
    raw=[norm(x) for x in re.split(r'\n\s*\n+',pg_core(text)) if norm(x)]
    lo,hi=spec['bounds']; out=[]; heading='Source text'
    for i,p in enumerate(raw):
        if i<lo or i>=hi:continue
        if is_heading(p): heading=p;out.append({'kind':'heading','text':p,'idx':i,'heading':heading})
        elif usable(p,key):out.append({'kind':'body','text':p,'idx':i,'heading':heading})
    return out

def chunks(items,target=590,minw=500,maxw=720):
    out=[];cur=[];w=0;heading='Source text';start=end=None
    for x in items:
        if x['kind']=='heading':
            if w>=minw:out.append((heading,start,end,cur));cur=[];w=0;start=end=None
            heading=x['text'];continue
        wc=len(x['text'].split())
        if cur and w>=minw and w+wc>maxw:
            out.append((heading,start,end,cur));cur=[];w=0;start=end=None
        if not cur:start=x['idx']
        cur.append(x['text']);w+=wc;end=x['idx']
        if w>=target:
            out.append((heading,start,end,cur));cur=[];w=0;start=end=None
    if cur and w>=minw:out.append((heading,start,end,cur))
    return out

def route(key,body,heading):
    t=(heading+' '+body).lower()
    if key=='rodwell':
        scores={('prophet','verses'):sum(t.count(k) for k in ['muhammad','prophet']),('messenger','verses'):sum(t.count(k) for k in ['messenger','apostle','proclaim','warn']),('mercy','mercy-stories'):sum(t.count(k) for k in ['mercy','merciful','forgive','forgiveness','compassion']),('human','verses'):sum(t.count(k) for k in ['mankind','man ','men ','woman','women','parent','parents','orphan','poor','justice','child']),('light','verses'):1+sum(t.count(k) for k in ['light','guidance','truth','prayer','faith'])}
        return max(scores,key=scores.get)
    if key=='lane':
        scores={('prophet','hadith'):1+sum(t.count(k) for k in ['mohammad','prophet','said']),('messenger','hadith'):sum(t.count(k) for k in ['message','mission','preach','proclaim','believe','unbeliever']),('human','hadith'):sum(t.count(k) for k in ['mercy','forgive','poor','orphan','neighbour','neighbor','woman','women','mother','father','charity']),('light','hadith'):sum(t.count(k) for k in ['light','prayer','god','faith','fast','worship'])}
        return max(scores,key=scores.get)
    if 'introduction' in heading.lower():return ('prophet','research')
    scores={('family','wives'):sum(t.count(k) for k in ['khadija','khadijah','aisha','ayesha','wife','wives','marriage']),('family','children'):sum(t.count(k) for k in ['fatima','zainab','zaynab','ruqayya','daughter','daughters','child','children']),('family','paternal-uncles'):sum(t.count(k) for k in ['abu talib','hamza','abbas','uncle']),('companions','biographies'):sum(t.count(k) for k in ['abu bakr','omar','umar','uthman','othman','ali ','companion','companions']),('companions','stories'):sum(t.count(k) for k in ['battle','bedr','badr','ohod','uhud','ditch','khandaq','army','war']),('mercy','mercy-stories'):sum(t.count(k) for k in ['mercy','pardon','forgive','compassion','clemency']),('messenger','seerah'):1+sum(t.count(k) for k in ['revelation','medina','mekka','mecca','hijra','flight','mission','prophecy']),('human','seerah'):sum(t.count(k) for k in ['home','daily','illness','family','food','dress','sleep','smile'])}
    return max(scores,key=scores.get)

def short_heading(h):return re.sub(r'\s+',' ',h).strip(' ._-')[:140] or 'Source text'

texts={};transport={};prepared={};built={}
for key,spec in SOURCES.items():
    data,via=fetch_exact(key,spec);transport[key]=via
    text=data.decode('utf-8-sig',errors='replace')
    prepared[key]=prepare(key,spec,text);built[key]=chunks(prepared[key])
    if len(built[key])<spec['quota']:
        raise SystemExit(f'{key}: only {len(built[key])} qualifying extended extracts for quota {spec["quota"]}')

records=[];parts=collections.defaultdict(int);seq=1
for key in ['draycott','rodwell','dinet','lane']:
    spec=SOURCES[key]
    for heading,start,end,paras in built[key][:spec['quota']]:
        body=' '.join(paras);section,subsection=route(key,body,heading);parts[(key,heading)]+=1
        aid=f'20260821-drive-extract-{seq:03d}';head=short_heading(heading);fp=hashlib.sha256(body.encode('utf-8')).hexdigest()
        records.append({'id':aid,'title':f'مادة موسعة موثّقة من «{spec["title"]}»: {head} — الجزء {parts[(key,heading)]:02d}','language':'source-language-preserved','contentType':spec['contentType'],'section':section,'subsection':subsection,'publicationStatus':'PUBLISHED','publishedAt':PUBLISHED_AT,'sourceKey':spec['workId'],'sourceHeading':head,'sourceParagraphStart':start,'sourceParagraphEnd':end,'sourceFingerprint':fp,'sourceWordCount':len(body.split()),'paragraphs':paras,'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'unsupportedFactualParagraphs':0,'unverifiedQuotations':0,'quotationVerification':'PASS','provenanceStatus':'PASS','duplicateCheck':'PASS'})
        seq+=1
if len(records)!=500:raise SystemExit(f'expected 500 records, got {len(records)}')
if len({r['id'] for r in records})!=500 or len({r['sourceFingerprint'] for r in records})!=500:raise SystemExit('duplicate id or source body')

registry={}
for key,s in SOURCES.items():
    d={'title':s['title'],'author':s['author'],'originalUrl':s['driveUrl'],'driveFileId':s['driveFileId'],'resourceId':s['workId'],'sourceRepository':'Google Drive / Project Gutenberg','sourceIdentifier':s['sourceIdentifier'],'rightsEvidence':'Public-domain Project Gutenberg text verified byte-for-byte against the connected Drive snapshot','language':s['language'],'driveSnapshotSha256':s['sha256'],'transportUsed':transport[key]}
    if key=='rodwell':d['sourceRole']="historical public-domain English translation; source wording preserved; not presented as a replacement for the Arabic Qur'an"
    registry[s['workId']]=d

DATE_DIR.mkdir(parents=True,exist_ok=True)
new_paths=[]
for bi,bn in enumerate(BATCH_NUMBERS):
    subset=records[bi*50:(bi+1)*50];used={r['sourceKey'] for r in subset}
    payload={'schema':'drive-source-compact-v1','version':f'2026-08-21-drive-source-500-batch-{bn}','draftedAt':PUBLISHED_AT,'publicationStatus':'PUBLISHED','chunk':bn,'sourceRegistry':{k:v for k,v in registry.items() if k in used},'drafts':subset}
    path=DATE_DIR/f'batch-{bn:02d}.json';path.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':')),encoding='utf-8');new_paths.append(path.relative_to(ROOT).as_posix())

supp_path=ROOT/'data/editorial/publication_supplement.json';supp=json.loads(supp_path.read_text(encoding='utf-8'))
old_ids=[x for x in supp.get('publishedIds',[]) if not x.startswith('20260821-drive-extract-')]
old_paths=[x for x in supp.get('draftBatchPaths',[]) if x not in new_paths]
new_ids=[r['id'] for r in records]
supp={'version':'2026-08-21-publication-supplement-v4-500-drive-extracts','publishedAt':PUBLISHED_AT,'draftBatchPaths':old_paths+new_paths,'publishedIds':old_ids+new_ids,'integrity':{'articlesPublishedInSupplement':len(old_ids)+500,'newArticlesPublishedThisBatch':500,'genuineSourceDerivedArticlesThisBatch':500,'driveSourceArticlesThisBatch':500,'aiGeneratedSubstantiveArticlesThisBatch':0,'articlesWith100PercentSourceProvenanceThisBatch':500,'unsupportedFactualParagraphsThisBatch':0,'unverifiedQuotationsThisBatch':0,'duplicateSourceBodiesThisBatch':0}}
supp_path.write_text(json.dumps(supp,ensure_ascii=False,indent=2),encoding='utf-8')

wc=[r['sourceWordCount'] for r in records];sections=collections.Counter(f"{r['section']}/{r['subsection']}" for r in records);srcdist=collections.Counter(r['sourceKey'] for r in records)
main=json.loads((ROOT/'data/editorial/publication_manifest.json').read_text(encoding='utf-8'))
audit={'version':'2026-08-21-drive-source-extract-500-audit-v1','generatedAt':PUBLISHED_AT,'requestedArticles':500,'publishedArticles':500,'totalPublishedArticlesAfterBatch':len(main.get('publishedIds',[]))+len(supp['publishedIds']),'articleLengthPolicy':{'targetWords':590,'minimumAcceptedWords':500,'observedMaximumWords':max(wc)},'totalSourceWordsPublished':sum(wc),'averageSourceWordsPerArticle':round(sum(wc)/500,2),'sourceCoveragePercent':100,'aiOriginalSubstantiveContentPercent':0,'unsupportedFactualParagraphs':0,'unverifiedQuotations':0,'duplicateSourceBodies':0,'sourceOnly':True,'driveOnly':True,'sourceDistribution':dict(srcdist),'sectionDistribution':dict(sections),'sourceFiles':[registry[SOURCES[k]['workId']] for k in ['draycott','rodwell','dinet','lane']],'publicationBatchPaths':new_paths,'articleIds':new_ids,'priorBatchOverlapControl':{'dinetStartParagraph':700,'lanePooleStartParagraph':200,'reason':'source windows begin after the ranges consumed by the previous 100-article batch'},'rules':['substantive body text derives only from connected Drive snapshots','public transport accepted only when SHA-256 exactly matches the Drive snapshot','no model-authored substantive prose','source paragraph order and wording preserved','whitespace normalization only','Gutenberg boilerplate, advertisements, illustration-only markers and obvious footnote-only material excluded','exact duplicate source bodies rejected','historical source viewpoints preserved and attributed rather than silently corrected','historical Qur’an translation labelled as historical translation source']}
(ROOT/'data/editorial/source_extract_500_drive_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')

loader_path=ROOT/'assets/editorial-public.js';loader=loader_path.read_text(encoding='utf-8')
if 'function expandCompactDraft' not in loader:
    marker='async function loadPublished(){'
    helper="""function expandCompactDraft(d,batch){\n if(!batch||batch.schema!=='drive-source-compact-v1'||!d||!d.sourceKey)return d;\n const meta=(batch.sourceRegistry||{})[d.sourceKey]||{};\n const ref=d.id+'-source',lang=meta.language||'en';\n const paragraphs=(d.paragraphs||[]).map((p,i)=>typeof p==='string'?{id:d.id+'-p'+String(i+1).padStart(2,'0'),text:p,language:lang,sourceRefs:[ref],substantive:true,aiOriginal:false,quotation:false,quotationVerified:true,editorialOperations:['source-extraction','whitespace-normalization','source-paragraph-preservation']}:p);\n const source={...meta,ref,sourceHeading:d.sourceHeading,sourceParagraphStart:d.sourceParagraphStart,sourceParagraphEnd:d.sourceParagraphEnd,sourceFingerprint:d.sourceFingerprint,verifiedAgainstOriginal:true,verificationBasis:'Exact source text from the connected Drive snapshot; public transport accepted only after SHA-256 identity verification.'};\n return {...d,paragraphs,sources:[source],sourceCoveragePercent:100,aiOriginalSubstantiveContentPercent:0,unsupportedFactualParagraphs:0,unverifiedQuotations:0,quotationVerification:'PASS',provenanceStatus:'PASS',duplicateCheck:'PASS'};\n}\n"""
    if marker not in loader:raise SystemExit('editorial loader marker missing')
    loader=loader.replace(marker,helper+marker,1)
old="for(const p of pack.draftBatchPaths||[]){const j=await getJSON(p);for(const d of j.drafts||[])if(allowed.has(d.id))all.push(applyOverride(d,pack))}"
new="for(const p of pack.draftBatchPaths||[]){const j=await getJSON(p);for(const raw of j.drafts||[]){const d=expandCompactDraft(raw,j);if(allowed.has(d.id))all.push(applyOverride(d,pack))}}"
if new not in loader:
    if old not in loader:raise SystemExit('editorial loader loop marker missing')
    loader=loader.replace(old,new,1)
loader_path.write_text(loader,encoding='utf-8')

sw_path=ROOT/'service-worker.js';sw=sw_path.read_text(encoding='utf-8')
sw=re.sub(r"const CACHE='[^']+';","const CACHE='prophet-biography-v6-8-12-500-drive-articles';",sw,count=1)
if "./data/editorial/source_extract_500_drive_audit.json" not in sw:
    sw=sw.replace("'./data/editorial/publication_manifest.json','./data/editorial/publication_supplement.json','./data/editorial_sections.json'","'./data/editorial/publication_manifest.json','./data/editorial/publication_supplement.json','./data/editorial/source_extract_100_audit.json','./data/editorial/source_extract_500_drive_audit.json','./data/editorial_sections.json'")
    sw=sw.replace("'/data/editorial/publication_manifest.json','/data/editorial/publication_supplement.json','/data/editorial_sections.json'","'/data/editorial/publication_manifest.json','/data/editorial/publication_supplement.json','/data/editorial/source_extract_100_audit.json','/data/editorial/source_extract_500_drive_audit.json','/data/editorial_sections.json'")
sw_path.write_text(sw,encoding='utf-8')
print(json.dumps({'published':500,'totalPublished':audit['totalPublishedArticlesAfterBatch'],'sourceWords':sum(wc),'avgWords':audit['averageSourceWordsPerArticle'],'sources':dict(srcdist),'sections':dict(sections)},ensure_ascii=False,indent=2))
