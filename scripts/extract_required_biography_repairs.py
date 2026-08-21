#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'data/editorial/required_biographies.json'
OUT=ROOT/'data/editorial/person_biography_repairs_raw.json'
TARGETS=['fatima-al-zahra','muhammad-ibn-abdullah','abu-bakr','umar','uthman','abu-hurayra','bilal','salman','khalid','saad-ibn-abi-waqqas','abu-ubayda','talha','zubayr','abdurrahman-ibn-awf','saeed-ibn-zayd','musab-ibn-umayr','ammar-ibn-yasir','khabbab-ibn-al-aratt','abdullah-ibn-masud','muadh-ibn-jabal','zaid-ibn-thabit','zaid-ibn-haritha','abu-dharr','al-miqdad','uthman-ibn-mazun','abu-darda','abu-musa-al-ashari','hudhayfa-ibn-al-yaman','jabir-ibn-abdullah']

def compact(v,depth=0):
    if depth>4:return None
    if isinstance(v,dict):
        out={}
        for k,x in v.items():
            if k.lower() in {'body','fulltext','raw','content'} and isinstance(x,str) and len(x)>1200:x=x[:1200]
            y=compact(x,depth+1)
            if y not in (None,'',[],{}):out[k]=y
        return out
    if isinstance(v,list):return [compact(x,depth+1) for x in v[:20]]
    if isinstance(v,str):return v[:4000]
    return v

doc=json.loads(SRC.read_text(encoding='utf-8'))
people=doc.get('people') or {}
rows={}
for pid in TARGETS:
    x=people.get(pid)
    if x is not None:rows[pid]=compact(x)
print('schema',doc.get('schema'),'people_type',type(people).__name__,'people_count',len(people))
print('targets_found',len(rows),'targets_missing',[x for x in TARGETS if x not in rows])
for pid,x in rows.items():
    print('\n###',pid)
    print(json.dumps(x,ensure_ascii=False)[:12000])
OUT.write_text(json.dumps({'schema':'person-biography-repairs-raw-v1','count':len(rows),'people':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
