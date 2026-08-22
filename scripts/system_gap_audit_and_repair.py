#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import argparse,json,re
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'data/audits/system_gap_audit.json';CANON='MASTER-OVERRIDING-SITE-INSTRUCTION.md';DEPRECATED={'MASTER_OVERRIDING_INSTRUCTION.md','MASTER-OVERRIDING-INSTRUCTION.md'};TEXT_EXT={'.py','.yml','.yaml','.md','.json','.html','.js','.css'};PLACEHOLDERS=('TODO','FIXME','COMING SOON','PLACEHOLDER','javascript:void(0)','href="#"');CONTROLLER='daily-generative-control.yml'
def load(p,d=None):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except Exception:return d
def governance_targets():
 for base in (ROOT/'scripts',ROOT/'.github/workflows',ROOT/'docs'):
  if base.exists():
   for p in base.rglob('*'):
    if p.is_file() and p.suffix.lower() in TEXT_EXT:yield p
 for p in ROOT.glob('AUTO_*.md'):yield p
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repair',action='store_true');a=ap.parse_args();repaired=[];stale=[];json_errors=[];placeholders=[];broken=[];retired=[]
 for p in governance_targets():
  if p.name in DEPRECATED or p.name==CANON:continue
  try:t=p.read_text(encoding='utf-8')
  except Exception:continue
  hit=[x for x in DEPRECATED if x in t]
  if hit:
   stale.append(str(p.relative_to(ROOT)))
   if a.repair:
    for x in hit:t=t.replace(x,CANON)
    p.write_text(t,encoding='utf-8');repaired.append(str(p.relative_to(ROOT)))
 # Self-heal workflow proliferation while preserving the retired files for audit/history.
 wfdir=ROOT/'.github/workflows';before=sorted(wfdir.glob('*.y*ml')) if wfdir.exists() else [];excess=[p for p in before if p.name!=CONTROLLER]
 if a.repair and excess:
  archive=ROOT/'docs/retired-workflows';archive.mkdir(parents=True,exist_ok=True)
  stamp=datetime.now(timezone.utc).strftime('%Y%m%d')
  for p in excess:
   dest=archive/(p.name+'.disabled')
   if dest.exists():dest=archive/(f'{p.stem}-{stamp}{p.suffix}.disabled')
   dest.write_bytes(p.read_bytes());p.unlink();retired.append({'from':str(p.relative_to(ROOT)),'to':str(dest.relative_to(ROOT))});repaired.append(str(p.relative_to(ROOT)))
 workflows=sorted(wfdir.glob('*.y*ml')) if wfdir.exists() else [];remaining_excess=[p.name for p in workflows if p.name!=CONTROLLER]
 for base in (ROOT/'data',ROOT/'private'):
  if base.exists():
   for p in base.rglob('*.json'):
    try:json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:json_errors.append({'path':str(p.relative_to(ROOT)),'error':type(e).__name__+': '+str(e)[:180]})
 public_names={p.name for p in ROOT.iterdir() if p.is_file()}
 for p in ROOT.glob('*.html'):
  try:t=p.read_text(encoding='utf-8')
  except Exception:continue
  up=t.upper()
  for token in PLACEHOLDERS:
   if token.upper() in up:placeholders.append({'path':p.name,'token':token})
  for attr,val in re.findall(r'\b(href|src)=["\']([^"\']+)["\']',t,re.I):
   v=val.strip()
   if not v or v.startswith(('#','mailto:','tel:','data:','javascript:')):continue
   sp=urlsplit(v)
   if sp.scheme or sp.netloc:continue
   target=sp.path.lstrip('/')
   if target and not (ROOT/target).exists() and target not in public_names:broken.append({'page':p.name,'attribute':attr.lower(),'target':target})
 bio=load(ROOT/'data/editorial/required_biographies_audit.json',{}) or {};ext=load(ROOT/'data/editorial/all_biographies_extension_audit.json',{}) or {};bg=load(ROOT/'data/editorial/biography_gap_repair_audit.json',{}) or {};completion=load(ROOT/'data/editorial/content_completion_state.json',{}) or {};tax=load(ROOT/'data/children/taxonomy.json',{}) or {};media=load(ROOT/'data/children/media-sources.json',{}) or {};pub=load(ROOT/'data/editorial/publication_manifest.json',{}) or {};catalog=load(ROOT/'data/public_catalog_all.generated.json',{}) or {};kids=load(ROOT/'data/children/completion_status.json',{}) or {};resolver=load(ROOT/'private/source_first_resolution.json',{}) or {}
 cat=Counter();items=(catalog.get('items') or catalog.get('resources') or []) if isinstance(catalog,dict) else []
 for x in items:
  if isinstance(x,dict):cat[str(x.get('availability') or x.get('status') or x.get('publicationStatus') or 'UNKNOWN')]+=1
 types=[str(x.get('id')) for x in tax.get('contentTypes',[]) if isinstance(x,dict)];story=[x for x in types if x in {'illustrated-stories','very-short-stories','animated-stories'}];subjects=[x for x in tax.get('subjects',[]) if isinstance(x,dict)];ages=[x for x in tax.get('ageGroups',[]) if isinstance(x,dict)]
 gaps=[]
 def gap(c,s,d):gaps.append({'code':c,'severity':s,'detail':d})
 if not (ROOT/CANON).exists():gap('MASTER_MISSING','HARD',CANON)
 if stale and not a.repair:gap('DEPRECATED_MASTER_REFERENCES','REPAIRABLE',stale[:100])
 if remaining_excess:gap('EXTRA_WORKFLOWS_NOTIFICATION_RISK','SYSTEM',remaining_excess)
 if json_errors:gap('INVALID_JSON','HARD',{'count':len(json_errors),'examples':json_errors[:50]})
 if broken:gap('BROKEN_LOCAL_LINKS','HARD',{'count':len(broken),'examples':broken[:100]})
 if placeholders:gap('PUBLIC_PLACEHOLDERS','REVIEW',{'count':len(placeholders),'examples':placeholders[:100]})
 if not completion:gap('CONTENT_COMPLETION_STATE_MISSING','RETRYABLE','Run content completion status')
 elif not completion.get('ARTICLE_FILL_COMPLETE'):gap('ARTICLE_TARGET_INCOMPLETE','CONTENT',{'underTargetSlots':len(completion.get('underTargetSlots') or []),'next':completion.get('nextTargetSlot')})
 if bio.get('missingCanonicalBiographyCount') not in (None,0):gap('MISSING_CANONICAL_BIOGRAPHIES','CONTENT',bio.get('missingCanonicalBiographyCount'))
 if int(ext.get('unresolvedCount') or 0)>0:gap('BIOGRAPHY_ENRICHMENT_UNRESOLVED','SOURCE',ext.get('unresolvedCount'))
 if int(bg.get('remainingLatinOnlyNameCount') or 0)>0:gap('ARABIC_PERSON_NAMES_LATIN_ONLY','LOCALIZATION',bg.get('remainingLatinOnlyNameCount'))
 if len(media.get('sources') or [])<100:gap('CHILD_CHANNEL_TARGET','CONTENT',{'current':len(media.get('sources') or []),'target':100})
 if kids and kids.get('verifiedVideoCount',0)<1000:gap('CHILD_VIDEO_TARGET','CONTENT',{'current':kids.get('verifiedVideoCount',0),'target':1000})
 if kids and not kids.get('STORY_TARGET_COMPLETE'):gap('CHILD_STORY_MATRIX_TARGET','CONTENT',{'underTargetCells':kids.get('underTargetStoryCellCount'),'next':kids.get('nextStoryTargetCell')})
 if len(story)<3:gap('CHILD_STORY_TYPES_MISSING','SYSTEM',story)
 if not subjects or not ages:gap('CHILD_TAXONOMY_INCOMPLETE','SYSTEM',{'subjects':len(subjects),'ages':len(ages)})
 if pub and pub.get('status')!='PUBLISHED':gap('PUBLICATION_MANIFEST_NOT_PUBLISHED','PUBLICATION',pub.get('status'))
 if resolver and int(resolver.get('acquisitionRequired') or 0)>0:gap('RESOURCE_EXTRACTION_BACKLOG','SOURCE',{'acquisitionRequired':resolver.get('acquisitionRequired'),'extractionReady':resolver.get('extractionReady'),'catalogResources':resolver.get('catalogResources')})
 payload={'schema':'prophet-system-gap-audit-v3','generatedAt':datetime.now(timezone.utc).isoformat(),'governedBy':CANON,'repairMode':a.repair,'safeRepairsApplied':repaired,'retiredWorkflows':retired,'summary':{'gapCount':len(gaps),'hardGapCount':sum(g['severity']=='HARD' for g in gaps),'workflowCount':len(workflows),'jsonErrorCount':len(json_errors),'brokenLocalLinkCount':len(broken),'placeholderFindingCount':len(placeholders)},'content':{'underTargetSlots':len(completion.get('underTargetSlots') or []),'missingCanonicalBiographyCount':bio.get('missingCanonicalBiographyCount'),'biographyEnrichmentUnresolved':ext.get('unresolvedCount'),'latinOnlyPersonNames':bg.get('remainingLatinOnlyNameCount')},'children':{'knownChannels':len(media.get('sources') or []),'channelTarget':100,'storyTypes':story,'subjects':len(subjects),'ageGroups':len(ages)},'resources':{'catalogResources':resolver.get('catalogResources'),'extractionReady':resolver.get('extractionReady'),'acquisitionRequired':resolver.get('acquisitionRequired'),'ocrDerivativeReady':resolver.get('ocrDerivativeReady')},'catalogStatusCounts':dict(cat),'gaps':gaps};OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(payload,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
