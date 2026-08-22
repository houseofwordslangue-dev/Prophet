#!/usr/bin/env python3
# GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
AUDIT=ROOT/'data/editorial/required_biographies_audit.json'
OUT=ROOT/'data/editorial/missing_biography_source_candidates.json'

def load(p,d):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d

def norm(s):
 s=str(s or '');s=re.sub(r'[ًٌٍَُِّْـ]','',s);s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي');return re.sub(r'[^\u0600-\u06ffA-Za-z0-9]+',' ',s).strip().lower()
def flatten(v,depth=0):
 if depth>5:return ''
 if isinstance(v,str):return v
 if isinstance(v,list):return '\n'.join(flatten(x,depth+1) for x in v)
 if isinstance(v,dict):return '\n'.join(flatten(v.get(k),depth+1) for k in ('title','name','nameAr','body','content','text','articleBody','bodyAr','arabic','ar','paragraphs','sections') if k in v)
 return ''
def iter_dicts(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from iter_dicts(x)
 elif isinstance(v,list):
  for x in v:yield from iter_dicts(x)
def source_signal(d):
 score=0
 if any(k in d for k in ('sources','source','sourceRefs','references','sourceFragments')):score+=2
 if d.get('sourceCoveragePercent')==100:score+=3
 if d.get('aiOriginalSubstantiveContentPercent')==0:score+=1
 if str(d.get('provenanceStatus') or '').upper()=='PASS':score+=2
 return score
def identity_blob(d):
 vals=[]
 for k in ('id','title','name','nameAr','subjectPerson','personId','person','slug','subsection','section','category'):
  if k in d:vals.append(flatten(d[k]) if isinstance(d[k],(dict,list)) else str(d[k]))
 rp=d.get('relatedPerson')
 if isinstance(rp,dict):vals.extend(str(x) for x in rp.values())
 sub=d.get('subject')
 if isinstance(sub,dict):vals.extend(str(x) for x in sub.values())
 return ' '.join(vals)
def main():
 audit=load(AUDIT,{})
 targets={str(x.get('id')):str(x.get('nameAr') or x.get('id')) for x in audit.get('missing',[]) if isinstance(x,dict) and x.get('id')}
 files=[p for p in (ROOT/'data').rglob('*.json') if p not in {AUDIT,OUT} and '/audits/' not in p.as_posix()]
 candidates={k:[] for k in targets}
 for path in files:
  try:doc=json.loads(path.read_text(encoding='utf-8'))
  except Exception:continue
  for d in iter_dicts(doc):
   text=flatten(d); wc=len(text.split())
   if wc<80:continue
   ident=identity_blob(d); ni=norm(ident); nt=norm(text[:2500])
   sig=source_signal(d)
   for pid,name in targets.items():
    explicit=pid.lower() in ident.lower()
    nh=norm(name); namehit=bool(nh and (nh in ni or nh in nt))
    if not (explicit or namehit):continue
    score=sig+(10 if explicit else 0)+(5 if namehit else 0)+min(wc//250,4)
    candidates[pid].append({'score':score,'wordCount':wc,'path':str(path.relative_to(ROOT)),'recordId':d.get('id'),'title':d.get('title'),'sourceSignal':sig,'explicitIdentity':explicit,'nameMatch':namehit,'textPreview':text[:900]})
 for pid,rows in candidates.items():
  uniq={}
  for x in rows:
   k=(x['path'],x.get('recordId'),x.get('title'))
   if k not in uniq or x['score']>uniq[k]['score']:uniq[k]=x
  candidates[pid]=sorted(uniq.values(),key=lambda x:(x['score'],x['wordCount']),reverse=True)[:25]
 out={'schema':'all-missing-biography-source-candidates-v1','targetCount':len(targets),'targetsWithCandidates':sum(bool(v) for v in candidates.values()),'targetsWithoutCandidates':[k for k,v in candidates.items() if not v],'targets':targets,'candidates':candidates,'governedBy':'MASTER_OVERRIDING_INSTRUCTION.md'}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'targetCount':out['targetCount'],'targetsWithCandidates':out['targetsWithCandidates'],'targetsWithoutCandidates':len(out['targetsWithoutCandidates'])},ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
