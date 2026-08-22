#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
"""Build a source-evidenced rijal generation audit and compact index.
Only explicit source generation/tabaqa fields are used. Dates, teacher/student
relations, target counts and chronology heuristics never assign a generation.
Conflicts are quarantined as unclassified rather than guessed.
"""
from __future__ import annotations
import argparse,datetime as dt,json,re,urllib.request
from collections import Counter
from pathlib import Path
from typing import Any,Iterable
DEFAULT_BASE='https://raw.githubusercontent.com/R3GENESI5/Itqan/master/app/data/rijal'
ARABIC_ORDINALS={'الأولى':1,'الثانية':2,'الثالثة':3,'الرابعة':4,'الخامسة':5,'السادسة':6,'السابعة':7,'الثامنة':8,'التاسعة':9,'العاشرة':10,'الحادية عشرة':11,'الثانية عشرة':12}
def fetch_json(url:str)->Any:
 req=urllib.request.Request(url,headers={'User-Agent':'Prophet-people-audit/2.0'});return json.load(urllib.request.urlopen(req,timeout=120))
def iter_profiles(payload:Any)->Iterable[tuple[str,dict[str,Any]]]:
 if isinstance(payload,dict):
  if isinstance(payload.get('profiles'),list):
   for i,x in enumerate(payload['profiles']):
    if isinstance(x,dict):yield str(x.get('id',i)),x
   return
  for k,v in payload.items():
   if isinstance(v,dict):yield str(k),v
 elif isinstance(payload,list):
  for i,x in enumerate(payload):
   if isinstance(x,dict):yield str(x.get('id',i)),x
def parse_layer(value:Any,allow_free_numeric:bool)->set[int]:
 out=set()
 if value in (None,'') or isinstance(value,bool):return out
 if isinstance(value,int):
  if 1<=value<=12:out.add(value)
  return out
 if isinstance(value,float) and value.is_integer():return parse_layer(int(value),allow_free_numeric)
 if isinstance(value,(list,tuple,set)):
  for p in value:out.update(parse_layer(p,allow_free_numeric))
  return out
 if isinstance(value,dict):
  for k in ('order','number','id','tabaqa_order','generation'):
   if k in value:out.update(parse_layer(value[k],True))
  return out
 text=str(value).strip()
 for label,n in ARABIC_ORDINALS.items():
  if text.startswith(label) or text.startswith('الطبقة '+label):out.add(n)
 if allow_free_numeric:
  m=re.fullmatch(r'\s*(1[0-2]|[1-9])(?:st|nd|rd|th)?(?:\s+Generation)?\s*',text,flags=re.I);b=re.search(r'\[(1[0-2]|[1-9])(?:st|nd|rd|th)?\s+Generation\]',text,flags=re.I)
  if m:out.add(int(m.group(1)))
  if b:out.add(int(b.group(1)))
 return out
def explicit_layer(p):
 evidence=[];layers=set()
 for field in ('tabaqa_order','generation','tabaqat'):
  v=p.get(field)
  if v in (None,'',[]):continue
  found=parse_layer(v,field!='tabaqat')
  if found:layers.update(found);evidence.append(field)
 return (next(iter(layers)),evidence,False) if len(layers)==1 else (None,evidence,len(layers)>1)
def bucket(layer):
 if layer==1:return 'companions_explicit_layer'
 if layer is not None and 2<=layer<=6:return 'tabiin'
 if layer is not None and 7<=layer<=9:return 'atba_al_tabiin'
 if layer is not None and 10<=layer<=12:return 'post_atba'
 return 'unclassified'
def conflict(grade,layer):return bool(layer is not None and ((grade=='companion' and layer!=1) or (grade!='companion' and layer==1)))
def slim(sf,key,grade,p,layer,klass,bad):
 v={'id':f"{sf.removeprefix('profiles_').removesuffix('.json')}:{key}",'source_file':sf,'source_key':key,'source_grade':grade,'name':p.get('full_name') or p.get('name') or p.get('name_ar') or key,'grade':p.get('grade_en') or p.get('grade') or grade,'tabaqa':p.get('tabaqat'),'tabaqa_order':layer,'generation_class':klass,'generation_conflict':bad or None,'city':p.get('city'),'death':p.get('death'),'kunya':p.get('kunya')};return {k:x for k,x in v.items() if x not in (None,'',[])}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--base-url',default=DEFAULT_BASE);ap.add_argument('--out',default='data/people/rijal-audit.json');ap.add_argument('--index-out',default='data/people/rijal-index.json');ap.add_argument('--expected-total',type=int,default=115735);ap.add_argument('--expected-companions',type=int,default=10880);a=ap.parse_args();base=a.base_url.rstrip('/');manifest=fetch_json(base+'/manifest.json');files=[f for f in manifest.get('files',[]) if f.get('type')=='profiles'];tot=Counter();layers=Counter();fields=Counter();sources={};index=[]
 for src in files:
  name=src['name'];grade=src.get('grade');payload=fetch_json(base+'/'+name);fc=Counter();observed=0
  for key,p in iter_profiles(payload):
   observed+=1;layer,evidence,field_bad=explicit_layer(p);status_bad=conflict(grade,layer);bad=field_bad or status_bad
   if field_bad:tot['field_generation_conflicts']+=1
   if status_bad:tot['source_status_conflicts']+=1
   if bad:tot['generation_conflicts']+=1
   klass='unclassified' if bad else bucket(layer);tot[klass]+=1;fc[klass]+=1
   if layer is not None:layers[str(layer)]+=1
   else:tot['without_explicit_layer']+=1
   for f in evidence:fields[f]+=1
   index.append(slim(name,key,grade,p,layer,klass,bad))
  sources[name]={'source_grade':grade,'manifest_count':src.get('count'),'observed_count':observed,'count_matches_manifest':src.get('count')==observed,'classifications':dict(sorted(fc.items()))};tot['all_profiles']+=observed
 companion=next((f for f in files if f.get('grade')=='companion'),{});partition=sum(tot[k] for k in ('tabiin','atba_al_tabiin','post_atba','companions_explicit_layer','unclassified'));checks={'total_matches_expected':tot['all_profiles']==a.expected_total,'total_matches_source_manifest':tot['all_profiles']==manifest.get('total_profiles'),'companion_manifest_matches_expected':companion.get('count')==a.expected_companions,'all_chunk_counts_match_manifest':all(v['count_matches_manifest'] for v in sources.values()),'classification_partition_matches_total':partition==tot['all_profiles'],'companion_chunk_not_counted_as_later_generation':all(sources.get('profiles_companion.json',{}).get('classifications',{}).get(k,0)==0 for k in ('tabiin','atba_al_tabiin','post_atba'))};audit={'schema_version':3,'governedBy':'MASTER-OVERRIDING-SITE-INSTRUCTION.md','generated_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'method':'explicit_source_generation_fields_with_conflict_quarantine','source':{'repository':'R3GENESI5/Itqan','base_url':base,'manifest_version':manifest.get('version'),'manifest_total':manifest.get('total_profiles'),'manifest_companions':companion.get('count')},'rules':{'companions':[1],'tabiin':[2,3,4,5,6],'atba_al_tabiin':[7,8,9],'post_atba':[10,11,12],'no_heuristic_inference':True,'conflicting_explicit_evidence':'unclassified'},'counts':{'all_profiles':tot['all_profiles'],'companions_manifest':companion.get('count'),'companions_explicit_layer_nonconflicting':tot['companions_explicit_layer'],'tabiin':tot['tabiin'],'atba_al_tabiin':tot['atba_al_tabiin'],'post_atba':tot['post_atba'],'unclassified':tot['unclassified'],'without_explicit_layer':tot['without_explicit_layer'],'generation_conflicts':tot['generation_conflicts']},'layer_counts_raw_before_conflict_quarantine':dict(sorted(layers.items(),key=lambda x:int(x[0]))),'evidence_field_counts':dict(sorted(fields.items())),'source_files':sources,'checks':checks,'complete':all(checks.values())};out=Path(a.out);idx=Path(a.index_out);out.parent.mkdir(parents=True,exist_ok=True);idx.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');idx.write_text(json.dumps({'schema_version':3,'count':len(index),'records':index},ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8');print(json.dumps(audit['counts'],ensure_ascii=False));return 0 if all(checks.values()) else 2
if __name__=='__main__':raise SystemExit(main())
