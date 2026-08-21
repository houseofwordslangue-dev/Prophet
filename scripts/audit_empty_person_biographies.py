#!/usr/bin/env python3
from __future__ import annotations
import base64,gzip,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/editorial/empty_biographies_audit.json'
def load(path,fallback):
    try:return json.loads((ROOT/path).read_text(encoding='utf-8'))
    except Exception:return fallback
def norm(s):
    s=str(s or '');s=re.sub(r'[ًٌٍَُِّْـ]','',s);return re.sub(r'\s+',' ',s).strip().lower()
def name_ar(p):
    n=p.get('name') or {}
    if isinstance(n,dict):return n.get('ar') or n.get('en') or p.get('nameAr') or p.get('id') or ''
    return p.get('nameAr') or str(n) or p.get('id') or ''
def load_chunks():
    try:
        b64=''.join((ROOT/f'data/family_biographies_all.{i}.b64').read_text(encoding='utf-8') for i in range(1,8))
        raw=gzip.decompress(base64.b64decode(re.sub(r'\s+','',b64))).decode('utf-8');return json.loads(raw)
    except Exception as e:return {'people':[],'error':str(e)}
def has_bio(v):
    if not isinstance(v,dict):return False
    for x in v.values():
        if isinstance(x,list) and any(str(y or '').strip() for y in x):return True
        if isinstance(x,str) and x.strip():return True
    return False
def apply_bio(p,b):
    bio=b.get('biography') or b.get('professionalBiography');src=b.get('sources') or b.get('professionalSources');att=b.get('attribution') or b.get('professionalAttribution');prov=b.get('provenance') or b.get('professionalProvenance');ctx=b.get('context') or b.get('relationshipContext')
    if has_bio(bio):p['professionalBiography']=bio
    if isinstance(src,list) and src:p['professionalSources']=src
    if isinstance(att,dict) and att:p['professionalAttribution']=att
    if str(prov or '').strip():p['professionalProvenance']=prov
    if str(ctx or '').strip():p['relationshipContext']=ctx
def assembled():
    a=load(Path('data/people.json'),{'people':[]});b=load(Path('data/family_people.json'),{'people':[]});g=load(Path('data/family_groups.json'),{'registry':[]});detailed=load(Path('data/family_biographies.json'),{'people':[]});required=load(Path('data/editorial/required_biographies.json'),{'people':{}});allb=load_chunks();mp={};names={}
    def add(p):
        if not isinstance(p,dict) or not p.get('id'):return
        q=dict(p);mp[q['id']]=q;nm=name_ar(q)
        if nm:names.setdefault(norm(nm),[]).append(q)
    for p in (a.get('people') or [])+(b.get('people') or [])+(g.get('registry') or []):add(p)
    for x in allb.get('people') or []:
        hits=names.get(norm(x.get('nameAr')),[])
        if len(hits)==1:p=hits[0]
        else:p={'id':x.get('id'),'name':{'ar':x.get('nameAr'),'en':x.get('nameAr'),'fr':x.get('nameAr')},'category':'family','sourcePassages':[]};mp[p['id']]=p
        apply_bio(p,x)
    for x in detailed.get('people') or []:
        p=mp.get(x.get('id'))
        if not p:
            hits=names.get(norm(x.get('nameAr')),[]);p=hits[0] if hits else None
        if p:apply_bio(p,x)
    req=required.get('people') or {};entries=((x.get('id'),x) for x in req) if isinstance(req,list) else req.items()
    for rid,x in entries:
        if not isinstance(x,dict):continue
        p=mp.get(rid or x.get('id'))
        if not p:
            nm=x.get('nameAr') or ((x.get('name') or {}).get('ar') if isinstance(x.get('name'),dict) else '');hits=names.get(norm(nm),[]);p=hits[0] if hits else None
        if p:apply_bio(p,x)
    return list(mp.values()),allb.get('error')
def nonempty_seq(v):
    if isinstance(v,str):return bool(v.strip())
    if isinstance(v,list):return any(str(x or '').strip() for x in v)
    return False
def rendered_has_content(p,lang):
    pb=p.get('professionalBiography') or {};bio=pb.get(lang) or pb.get('ar') or []
    if nonempty_seq(bio):return True,'professionalBiography'
    passages=[x for x in (p.get('sourcePassages') or []) if (x.get('language') or 'ar')==lang and str(x.get('text') or '').strip()];mentions=[x for x in passages if x.get('relation')!='authored-saying']
    if mentions:return True,'sourcePassages'
    return False,'empty'
def main():
    people,chunk_error=assembled();required=[];reference=[];langs=['ar','en','fr'];category_counts={}
    for p in people:
        cat=p.get('category') or 'unknown';category_counts[cat]=category_counts.get(cat,0)+1;missing=[l for l in langs if not rendered_has_content(p,l)[0]]
        if not missing:continue
        row={'id':p.get('id'),'nameAr':name_ar(p),'category':cat,'missingLanguages':missing,'hasProfessionalSources':bool(p.get('professionalSources')),'sourcePassageCount':len(p.get('sourcePassages') or [])}
        (reference if cat=='source-person' else required).append(row)
    audit={'schema':'empty-biographies-render-audit-v3','assembledPeople':len(people),'categoryCounts':category_counts,'chunkLoadError':chunk_error,'biographyRequiredEmptyCount':len(required),'referenceOnlyEmptyCount':len(reference),'biographyRequiredEmpty':required,'referenceOnlyEmpty':reference,'complete':len(required)==0}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(audit,ensure_ascii=False))
if __name__=='__main__':main()
