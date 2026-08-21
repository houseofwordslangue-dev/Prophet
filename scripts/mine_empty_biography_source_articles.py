#!/usr/bin/env python3
from __future__ import annotations
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/editorial/empty_biography_source_candidates.json'
TARGETS={
'fatima-al-zahra':'فاطمة الزهراء','prophet-muhammad':'محمد ﷺ','abu-bakr':'أبو بكر الصديق','umar':'عمر بن الخطاب','uthman':'عثمان بن عفان','abu-hurayra':'أبو هريرة','bilal':'بلال بن رباح','salman':'سلمان الفارسي','khalid':'خالد بن الوليد','saad-ibn-abi-waqqas':'سعد بن أبي وقاص','abu-ubayda':'أبو عبيدة عامر بن الجراح','talha':'طلحة بن عبيد الله','zubayr':'الزبير بن العوام','abdurrahman-ibn-awf':'عبد الرحمن بن عوف','saeed-ibn-zayd':'سعيد بن زيد','musab-ibn-umayr':'مصعب بن عمير','ammar-ibn-yasir':'عمار بن ياسر','khabbab-ibn-al-aratt':'خباب بن الأرت','abdullah-ibn-masud':'عبد الله بن مسعود','muadh-ibn-jabal':'معاذ بن جبل','zaid-ibn-thabit':'زيد بن ثابت','zaid-ibn-haritha':'زيد بن حارثة','abu-dharr':'أبو ذر الغفاري','al-miqdad':'المقداد بن عمرو','uthman-ibn-mazun':'عثمان بن مظعون','abu-darda':'أبو الدرداء الأنصاري','abu-musa-al-ashari':'أبو موسى الأشعري','hudhayfa-ibn-al-yaman':'حذيفة بن اليمان','jabir-ibn-abdullah':'جابر بن عبد الله'}
ALIASES={'prophet-muhammad':['muhammad-ibn-abdullah','prophet-muhammad'],'umar':['umar','umar-ibn-al-khattab'],'uthman':['uthman','uthman-ibn-affan'],'bilal':['bilal','bilal-ibn-rabah'],'salman':['salman','salman-al-farisi'],'khalid':['khalid','khalid-ibn-al-walid'],'abu-ubayda':['abu-ubayda','abu-ubayda-ibn-al-jarrah'],'talha':['talha','talha-ibn-ubaydullah'],'zubayr':['zubayr','al-zubayr-ibn-al-awwam'],'abdurrahman-ibn-awf':['abdurrahman-ibn-awf','abd-al-rahman-ibn-awf']}
def norm(s):
 s=str(s or '');s=re.sub(r'[ًٌٍَُِّْـ]','',s);s=s.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي');return re.sub(r'[^\u0600-\u06ffA-Za-z0-9]+',' ',s).strip().lower()
def words(s):return len([x for x in re.split(r'\s+',str(s or '').strip()) if x])
def flatten_text(v,depth=0):
 if depth>5:return ''
 if isinstance(v,str):return v
 if isinstance(v,list):return '\n'.join(flatten_text(x,depth+1) for x in v)
 if isinstance(v,dict):
  keys=['body','content','text','articleBody','bodyAr','arabic','ar','paragraphs','sections']
  parts=[flatten_text(v[k],depth+1) for k in keys if k in v]
  return '\n'.join(x for x in parts if x)
 return ''
def identity_blob(d):
 vals=[]
 for k in ['id','title','name','nameAr','subjectPerson','personId','person','slug','subsection','section','category']:
  if k in d: vals.append(flatten_text(d[k]) if isinstance(d[k],(dict,list)) else str(d[k]))
 rp=d.get('relatedPerson')
 if isinstance(rp,dict):vals.extend(str(x) for x in rp.values())
 return ' '.join(vals)
def source_signal(d):
 blob=json.dumps({k:d.get(k) for k in ['sources','source','provenance','sourceRefs','references','sourceFragments','sourceCoveragePercent','aiOriginalSubstantiveContentPercent','status'] if k in d},ensure_ascii=False)
 score=0
 if any(k in d for k in ['sources','source','sourceRefs','references','sourceFragments']):score+=2
 if 'source' in blob.lower() or 'مصدر' in blob:score+=1
 if d.get('sourceCoveragePercent')==100:score+=2
 if d.get('aiOriginalSubstantiveContentPercent')==0:score+=1
 if str(d.get('status','')).upper()=='PUBLISHED':score+=1
 return score
def iter_dicts(v):
 if isinstance(v,dict):
  yield v
  for x in v.values():yield from iter_dicts(x)
 elif isinstance(v,list):
  for x in v:yield from iter_dicts(x)
def main():
 candidates={k:[] for k in TARGETS};files=list((ROOT/'data/editorial').rglob('*.json'))
 for path in files:
  if path.name in {OUT.name,'empty_biographies_audit.json','required_biographies.json'}:continue
  try:doc=json.loads(path.read_text(encoding='utf-8'))
  except Exception:continue
  for d in iter_dicts(doc):
   text=flatten_text(d);wc=words(text)
   if wc<120:continue
   ident=identity_blob(d);ni=norm(ident);score0=source_signal(d)
   for pid,name in TARGETS.items():
    aliases=ALIASES.get(pid,[pid]);explicit=any(a.lower() in str(ident).lower() for a in aliases);namehit=norm(name) in ni
    # Avoid generic Muhammad matches unless explicit person ID or full Prophet title is present.
    if pid=='prophet-muhammad' and not explicit and norm('محمد ﷺ') not in ni and norm('النبي محمد') not in ni:continue
    if not (explicit or namehit):continue
    score=score0+(8 if explicit else 0)+(4 if namehit else 0)+min(wc//250,4)
    candidates[pid].append({'score':score,'wordCount':wc,'path':str(path.relative_to(ROOT)),'recordId':d.get('id'),'title':d.get('title'),'sourceSignal':score0,'explicitIdentity':explicit,'nameMatch':namehit,'textPreview':text[:700]})
 for pid in candidates:
  uniq={}
  for x in candidates[pid]:
   key=(x['path'],x.get('recordId'),x.get('title'))
   if key not in uniq or x['score']>uniq[key]['score']:uniq[key]=x
  candidates[pid]=sorted(uniq.values(),key=lambda x:(x['score'],x['wordCount']),reverse=True)[:20]
 summary={pid:{'nameAr':TARGETS[pid],'candidateCount':len(rows),'best':rows[0] if rows else None} for pid,rows in candidates.items()}
 out={'schema':'empty-biography-source-candidates-v1','filesScanned':len(files),'targetCount':len(TARGETS),'targetsWithCandidates':sum(bool(v) for v in candidates.values()),'targetsWithoutCandidates':[pid for pid,v in candidates.items() if not v],'summary':summary,'candidates':candidates}
 OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'filesScanned':len(files),'targetsWithCandidates':out['targetsWithCandidates'],'targetsWithoutCandidates':out['targetsWithoutCandidates'],'counts':{k:len(v) for k,v in candidates.items()}},ensure_ascii=False))
if __name__=='__main__':main()
