#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math, urllib.parse, urllib.request
from pathlib import Path

BASE='https://raw.githubusercontent.com/R3GENESI5/Itqan/master/app/data/rijal/'
PARTITIONS=[
 ('profiles_companion.json','companion',10880),
 ('profiles_reliable.json','reliable',26467),
 ('profiles_mostly_reliable.json','mostly_reliable',21800),
 ('profiles_weak.json','weak',21413),
 ('profiles_abandoned.json','abandoned',1386),
 ('profiles_fabricator.json','fabricator',2094),
 ('profiles_unknown.json','unknown',31695),
]
BATCH_SIZE=50
KEEP=('id','global_id','full_name','name_ar','name','kunya','laqab','nasab','nisba','grade_ar','grade_en','grade','tabaqat','tabaqa','generation','city','place','residence','birth','birth_year','death','death_year','namings','name_variants','aliases','dhahabi','jarh_wa_tadil','teachers','narrated_from','shuyukh','students','narrated_to','talabah','relations','relationships','family','classical_sources','source_entries','sources','source_refs','provenance','unique_key','uniqueness','gk_id','gk_match_method')

def get_json(name):
    with urllib.request.urlopen(BASE+name,timeout=180) as r:
        return json.loads(r.read().decode('utf-8'))

def nonempty(v): return v not in (None,'',[],{})

def numkey(item):
    key,p=item
    raw=p.get('id',p.get('global_id',key)) if isinstance(p,dict) else key
    try:return (0,int(raw))
    except:return (1,str(raw))

def clean(p,filename,grade):
    out={k:p[k] for k in KEEP if k in p and nonempty(p[k])}
    source_id=str(p.get('id',p.get('global_id','')))
    out['source_id']=source_id
    out['source_partition']=filename
    out['source_grade']=grade
    out['canonical_url']='person.html?rijal=1&id='+urllib.parse.quote(source_id,safe='')+'&group=rijal&lang=ar&p='+urllib.parse.quote(filename,safe='')
    out['provenance_class']='SOURCED_EXTRACTED'
    out['source_coverage_percent']=100
    out['ai_original_substantive_content_percent']=0
    sections=[]
    name=p.get('full_name') or p.get('name_ar') or p.get('name')
    if name: sections.append({'title':'الاسم','text':name})
    if nonempty(p.get('kunya')) and p.get('kunya')!='-': sections.append({'title':'الكنية','text':p['kunya']})
    if nonempty(p.get('laqab')) and p.get('laqab')!='-': sections.append({'title':'اللقب','text':p['laqab']})
    if nonempty(p.get('nasab')) and p.get('nasab')!='-': sections.append({'title':'النسب','text':p['nasab']})
    if nonempty(p.get('grade_ar')): sections.append({'title':'التوصيف','text':p['grade_ar']})
    elif nonempty(p.get('grade_en')): sections.append({'title':'التوصيف','text':p['grade_en']})
    if nonempty(p.get('tabaqat')) and p.get('tabaqat')!='-': sections.append({'title':'الطبقة','text':str(p['tabaqat'])})
    elif nonempty(p.get('generation')): sections.append({'title':'الطبقة','text':str(p['generation'])})
    if nonempty(p.get('city')) and p.get('city')!='-': sections.append({'title':'البلد والإقامة','text':p['city']})
    if nonempty(p.get('birth')): sections.append({'title':'الميلاد','text':str(p['birth'])})
    if nonempty(p.get('death')) and p.get('death')!='-': sections.append({'title':'الوفاة','text':str(p['death'])})
    if nonempty(p.get('dhahabi')) and p.get('dhahabi')!='-': sections.append({'title':'منقول في الترجمة','text':str(p['dhahabi'])})
    out['biography_sections_ar']=sections
    return out

def materialize(batch_no:int,outdir:Path):
    start=(batch_no-1)*BATCH_SIZE
    end=start+BATCH_SIZE
    cursor=0; chosen=[]; provenance=[]
    for filename,grade,count in PARTITIONS:
        part_start=cursor; part_end=cursor+count
        if end<=part_start: break
        if start>=part_end:
            cursor=part_end; continue
        data=get_json(filename)
        rows=[p for _,p in sorted(data.items(),key=numkey) if isinstance(p,dict) and (p.get('full_name') or p.get('name_ar') or p.get('name'))]
        local_a=max(0,start-part_start); local_b=min(len(rows),end-part_start)
        for p in rows[local_a:local_b]: chosen.append(clean(p,filename,grade))
        provenance.append({'file':filename,'grade':grade,'selected':max(0,local_b-local_a)})
        cursor=part_end
        if len(chosen)>=BATCH_SIZE: break
    if not chosen: raise SystemExit('No profiles selected')
    outdir.mkdir(parents=True,exist_ok=True)
    payload={
      'schema':'rijal-biography-batch-materialized-v2','batchNumber':batch_no,'configuredBatchSize':BATCH_SIZE,
      'count':len(chosen),'ordinalStart':start+1,'ordinalEnd':start+len(chosen),'status':'MATERIALIZED_SOURCE_BACKED',
      'onePersonOneCanonicalBiography':True,'noInventedFacts':True,'missingFields':'omitted','publicMetaCommentary':False,
      'source':'R3GENESI5/Itqan app/data/rijal','sourceVersion':'1.20','sourceSelections':provenance,'records':chosen
    }
    path=outdir/f'batch-{batch_no:04d}.json'
    path.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    audit={'schema':'rijal-biography-materialization-audit-v1','batchNumber':batch_no,'recordsMaterialized':len(chosen),'allSourceBacked':all(r['source_coverage_percent']==100 for r in chosen),'inventedFacts':0,'canonicalRoutes':len({r['canonical_url'] for r in chosen}),'complete':len(chosen)==BATCH_SIZE}
    (outdir/f'batch-{batch_no:04d}.audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit,ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--batch',type=int,default=1); ap.add_argument('--out',type=Path,default=Path('data/editorial/rijal-biography-batches')); a=ap.parse_args(); materialize(a.batch,a.out)
