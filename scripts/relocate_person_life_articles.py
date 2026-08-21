#!/usr/bin/env python3
from __future__ import annotations
import json,re,shutil
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[1]
DRAFT_ROOT=ROOT/'data/editorial/drafts'
OUT=ROOT/'data/editorial/canonical_life_chapters.json'
PER_DIR=ROOT/'data/editorial/canonical-life'
AUDIT=ROOT/'data/editorial/person_life_relocation_audit.json'
LIFE_PATTERNS=[re.compile(r'سيرت(?:ه|ها)?\s*وحيات(?:ه|ها)?'),re.compile(r'سيرة\s+(?:وحياة\s+)?'),re.compile(r'من\s+سيرت(?:ه|ها)\s+وحيات(?:ه|ها)'),re.compile(r'\bbiograph(?:y|ies)\b',re.I),re.compile(r'\blife\s+(?:and\s+times\s+)?of\b',re.I),re.compile(r'\blife\s+biograph',re.I),re.compile(r'\bvie\s+de\b',re.I),re.compile(r'\bbiographie\b',re.I)]

def now():return datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
def read(path):
 try:return json.loads(path.read_text(encoding='utf-8'))
 except Exception:return None
def rows_of(payload):
 if isinstance(payload,list):return payload
 if isinstance(payload,dict):
  for k in ('drafts','items','articles'):
   if isinstance(payload.get(k),list):return payload[k]
 return []
def person_of(r):
 for k in ('relatedPerson','subject'):
  x=r.get(k)
  if isinstance(x,dict) and x.get('id'):return str(x['id']),str(x.get('name') or x.get('nameAr') or x['id'])
 for k in ('canonicalPersonId','subjectPerson','personId'):
  if r.get(k):return str(r[k]),str(r.get('canonicalPersonName') or r.get('nameAr') or r[k])
 return None
def title_of(r):
 t=r.get('title') or r.get('headline') or ''
 if isinstance(t,dict):return ' '.join(str(x) for x in t.values())
 return str(t)
def body_of(r):
 for k in ('body','content','text','articleBody','bodyAr'):
  v=r.get(k)
  if isinstance(v,str) and v.strip():return v.strip()
  if isinstance(v,list) and v:return '\n\n'.join(str(x) for x in v if str(x).strip())
 return ''
def language_of(r,body):
 x=str(r.get('language') or r.get('lang') or '').lower().strip()
 if x in ('ar','en','fr'):return x
 letters=re.findall(r'[A-Za-z\u0600-\u06ffÀ-ÿ]',body)
 if letters and sum('\u0600'<=c<='\u06ff' for c in letters)/len(letters)>=0.35:return 'ar'
 return 'en'
def life_intent(r):
 kind=' '.join(str(r.get(k) or '') for k in ('articleKind','editorialCategory','contentType','publicRole')).lower()
 if any(x in kind for x in ('biography','life-biograph','life-profile')):return True
 if r.get('biographyPlacement') is True:return True
 if r.get('consolidatedIntoCanonicalBiography') is True and r.get('articleKind')=='supporting-person-source':return True
 return any(p.search(title_of(r)) for p in LIFE_PATTERNS)
def canonical_url(pid,name):return f'person.html?id={quote(pid)}&name={quote(name)}'
def safe_name(pid):return re.sub(r'[^A-Za-z0-9._-]+','-',pid).strip('-') or 'person'

def main():
 files=sorted(DRAFT_ROOT.glob('**/*.json'));payloads={};groups=defaultdict(list);unresolved=[];scanned=0
 for path in files:
  payload=read(path)
  if payload is None:continue
  rows=rows_of(payload)
  if not rows:continue
  payloads[path]=payload
  for r in rows:
   if not isinstance(r,dict):continue
   scanned+=1
   if not life_intent(r):continue
   person=person_of(r)
   if not person:
    unresolved.append({'path':str(path.relative_to(ROOT)),'id':r.get('id'),'title':title_of(r)})
    continue
   groups[person[0]].append((path,r,person[1]))

 changed=set();people={};old_sections=Counter();total_words=0;lang_counts=Counter();total_chapters=0
 if PER_DIR.exists():shutil.rmtree(PER_DIR)
 PER_DIR.mkdir(parents=True,exist_ok=True)
 for pid,items in sorted(groups.items()):
  names=Counter(n for _,_,n in items);name=names.most_common(1)[0][0] if names else pid;curl=canonical_url(pid,name)
  ids=[];paths=set();words=0;chapters=[];person_langs=Counter()
  for path,r,_ in items:
   prev={'section':r.get('section'),'sections':r.get('sections'),'subsection':r.get('subsection'),'editorialCategory':r.get('editorialCategory'),'articleKind':r.get('articleKind'),'publicRole':r.get('publicRole')}
   if r.get('section'):old_sections[str(r['section'])]+=1
   body=body_of(r);wc=int(r.get('wordCount') or len(body.split()));lang=language_of(r,body);lang_counts[lang]+=1;person_langs[lang]+=1;words+=wc;total_words+=wc;total_chapters+=1
   chapter={'id':r.get('id'),'language':lang,'title':r.get('title'),'body':body,'wordCount':wc,'sources':r.get('sources') or r.get('sourceRefs') or r.get('references') or [],'provenance':r.get('provenance') or r.get('source') or {},'sourcePath':str(path.relative_to(ROOT)),'previousPlacement':prev}
   chapters.append(chapter);ids.append(r.get('id'));paths.add(chapter['sourcePath'])
   r['previousPlacement']=prev;r['section']='canonical-person-biography';r['sections']=[];r['subsection']='life-chapters';r['articleKind']='canonical-biography-chapter';r['editorialCategory']='canonical-biography';r['publicRole']='canonical-biography-chapter';r['biographyPlacement']=True;r['canonicalEditorialSlot']=True;r['publicListing']=False;r['relocatedToCanonicalBiography']=True;r['relocatedAt']=now();r['canonicalPersonId']=pid;r['canonicalPersonName']=name;r['canonicalPersonUrl']=curl
   rel=r.get('relatedPerson')
   if isinstance(rel,dict):rel['canonicalUrl']=curl;rel['canonicalBiography']=True
   changed.add(path)
  fn=safe_name(pid)+'.json';relfile=f'data/editorial/canonical-life/{fn}'
  (PER_DIR/fn).write_text(json.dumps({'schema':'canonical-person-life-chapters-v1','personId':pid,'personName':name,'canonicalUrl':curl,'chapterCount':len(chapters),'languageCounts':dict(person_langs),'chapters':chapters},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  people[pid]={'id':pid,'nameAr':name,'canonicalUrl':curl,'chapterCount':len(items),'languageCounts':dict(person_langs),'chapterIds':ids,'sourceBatchPaths':sorted(paths),'totalWords':words,'file':relfile}

 for path in sorted(changed):path.write_text(json.dumps(payloads[path],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 out={'schema':'canonical-life-chapters-index-v2','generatedAt':now(),'policy':{'onePersonOneBiography':True,'lifeBiographyArticlesLiveOnlyOnPersonPage':True,'thematicArticlesRemainInSections':True,'sourceProvenancePreserved':True,'localizedDisplayOnly':True,'perPersonLazyLoading':True},'personCount':len(people),'chapterCount':total_chapters,'languageCounts':dict(lang_counts),'people':people}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 remaining=[]
 for path in files:
  payload=payloads.get(path) or read(path)
  for r in rows_of(payload):
   if not isinstance(r,dict) or not life_intent(r) or not person_of(r):continue
   if r.get('section')!='canonical-person-biography' or r.get('publicListing') is not False:remaining.append({'path':str(path.relative_to(ROOT)),'id':r.get('id'),'title':title_of(r),'section':r.get('section')})
 missing_files=[pid for pid,p in people.items() if not (ROOT/p['file']).exists()]
 audit={'schema':'person-life-relocation-audit-v2','generatedAt':now(),'recordsScanned':scanned,'peopleAffected':len(people),'lifeRecordsRelocated':total_chapters,'totalRelocatedWords':total_words,'languageCounts':dict(lang_counts),'previousSectionCounts':dict(old_sections),'unresolvedLifeRecords':unresolved,'remainingLifeRecordsOutsidePersonPages':remaining,'missingPerPersonFiles':missing_files,'complete':len(remaining)==0 and len(missing_files)==0}
 AUDIT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(audit,ensure_ascii=False))
 if not audit['complete']:raise SystemExit('Relocation incomplete')
if __name__=='__main__':main()
