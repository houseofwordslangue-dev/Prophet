#!/usr/bin/env python3
# GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md
from __future__ import annotations

import argparse, json, re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data/audits/system_gap_audit.json'
CANON='MASTER_OVERRIDING_INSTRUCTION.md'
OBSOLETE='MASTER-OVERRIDING-SITE-INSTRUCTION.md'
TEXT_EXT={'.py','.yml','.yaml','.md','.json','.html','.js','.css'}
PLACEHOLDERS=('TODO','FIXME','COMING SOON','PLACEHOLDER','javascript:void(0)','href="#"')

def load(p,default=None):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return default

def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values():yield from walk(x)
    elif isinstance(v,list):
        for x in v:yield from walk(x)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--repair',action='store_true');args=ap.parse_args()
    repaired=[]; stale=[]; json_errors=[]; placeholders=[]; broken_links=[]

    # Canonical governance reference repair: exact filename substitution only.
    for base in (ROOT/'scripts', ROOT/'.github/workflows'):
        if not base.exists():continue
        for p in base.rglob('*'):
            if not p.is_file() or p.suffix.lower() not in TEXT_EXT:continue
            try:t=p.read_text(encoding='utf-8')
            except Exception:continue
            if OBSOLETE in t:
                stale.append(str(p.relative_to(ROOT)))
                if args.repair:
                    p.write_text(t.replace(OBSOLETE,CANON),encoding='utf-8');repaired.append(str(p.relative_to(ROOT)))

    # JSON syntax sweep.
    for base in (ROOT/'data',ROOT/'private'):
        if not base.exists():continue
        for p in base.rglob('*.json'):
            try:json.loads(p.read_text(encoding='utf-8'))
            except Exception as e:json_errors.append({'path':str(p.relative_to(ROOT)),'error':type(e).__name__+': '+str(e)[:200]})

    # Public HTML placeholder and local-link sweep.
    htmls=list(ROOT.glob('*.html')); public_names={p.name for p in ROOT.iterdir() if p.is_file()}
    for p in htmls:
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
            if not target:continue
            q=(ROOT/target)
            if not q.exists() and target not in public_names:
                broken_links.append({'page':p.name,'attribute':attr.lower(),'target':target})

    workflows=sorted((ROOT/'.github/workflows').glob('*.y*ml')) if (ROOT/'.github/workflows').exists() else []
    workflow_names=[p.name for p in workflows]
    auto_workflow_excess=[x for x in workflow_names if x!='daily-generative-control.yml']

    bio=load(ROOT/'data/editorial/required_biographies_audit.json',{}) or {}
    bio_ext=load(ROOT/'data/editorial/all_biographies_extension_audit.json',{}) or {}
    bio_gap=load(ROOT/'data/editorial/biography_gap_repair_audit.json',{}) or {}
    completion=load(ROOT/'data/editorial/content_completion_state.json',{}) or {}
    taxonomy=load(ROOT/'data/children/taxonomy.json',{}) or {}
    media=load(ROOT/'data/children/media-sources.json',{}) or {}
    publication=load(ROOT/'data/editorial/publication_manifest.json',{}) or {}
    catalog=load(ROOT/'data/public_catalog_all.generated.json',{}) or {}

    # Catalog status counts without assuming one schema.
    cat_counts=Counter()
    items=(catalog.get('items') or catalog.get('resources') or catalog.get('catalog') or []) if isinstance(catalog,dict) else []
    for x in items:
        if isinstance(x,dict):cat_counts[str(x.get('availability') or x.get('status') or x.get('publicationStatus') or 'UNKNOWN')]+=1

    children_types=[str(x.get('id')) for x in taxonomy.get('contentTypes',[]) if isinstance(x,dict)]
    story_types=[x for x in children_types if x in {'illustrated-stories','very-short-stories','animated-stories'}]
    subjects=[str(x.get('id')) for x in taxonomy.get('subjects',[]) if isinstance(x,dict)]
    ages=[str(x.get('id')) for x in taxonomy.get('ageGroups',[]) if isinstance(x,dict)]

    gaps=[]
    def gap(code,severity,detail):gaps.append({'code':code,'severity':severity,'detail':detail})
    if not (ROOT/CANON).exists():gap('MASTER_MISSING','HARD',CANON)
    if stale:gap('OBSOLETE_MASTER_REFERENCES','REPAIRABLE',{'count':len(stale),'paths':stale[:100]})
    if json_errors:gap('INVALID_JSON','HARD',{'count':len(json_errors),'examples':json_errors[:50]})
    if broken_links:gap('BROKEN_LOCAL_LINKS','HARD',{'count':len(broken_links),'examples':broken_links[:100]})
    if placeholders:gap('PUBLIC_PLACEHOLDERS','REVIEW',{'count':len(placeholders),'examples':placeholders[:100]})
    if auto_workflow_excess:gap('EXTRA_WORKFLOWS_NOTIFICATION_RISK','SYSTEM',{'count':len(auto_workflow_excess),'files':auto_workflow_excess})
    if not completion:gap('CONTENT_COMPLETION_STATE_MISSING','RETRYABLE','Run scripts/content_completion_status.py')
    elif not completion.get('ARTICLE_FILL_COMPLETE'):gap('ARTICLE_TARGET_INCOMPLETE','CONTENT',{'underTargetSlots':len(completion.get('underTargetSlots') or []),'emptySlots':completion.get('emptySlots') or [],'next':completion.get('nextTargetSlot')})
    if bio.get('missingCanonicalBiographyCount') not in (None,0):gap('MISSING_CANONICAL_BIOGRAPHIES','CONTENT',bio.get('missingCanonicalBiographyCount'))
    if int(bio_ext.get('unresolvedCount') or 0)>0:gap('BIOGRAPHY_ENRICHMENT_UNRESOLVED','SOURCE',bio_ext.get('unresolvedCount'))
    if int(bio_gap.get('remainingLatinOnlyNameCount') or 0)>0:gap('ARABIC_PERSON_NAMES_LATIN_ONLY','LOCALIZATION',bio_gap.get('remainingLatinOnlyNameCount'))
    if len(media.get('sources') or [])<100:gap('CHILD_CHANNEL_TARGET','CONTENT',{'current':len(media.get('sources') or []),'target':100})
    if len(story_types)<3:gap('CHILD_STORY_TYPES_MISSING','SYSTEM',story_types)
    if not subjects or not ages:gap('CHILD_TAXONOMY_INCOMPLETE','SYSTEM',{'subjects':len(subjects),'ages':len(ages)})
    if publication and publication.get('status')!='PUBLISHED':gap('PUBLICATION_MANIFEST_NOT_PUBLISHED','PUBLICATION',publication.get('status'))

    payload={
      'schema':'prophet-system-gap-audit-v1','generatedAt':datetime.now(timezone.utc).isoformat(),
      'governedBy':CANON,'repairMode':args.repair,'safeRepairsApplied':repaired,
      'summary':{'gapCount':len(gaps),'hardGapCount':sum(g['severity']=='HARD' for g in gaps),'workflowCount':len(workflows),'jsonErrorCount':len(json_errors),'brokenLocalLinkCount':len(broken_links),'placeholderFindingCount':len(placeholders)},
      'content':{'activeEditorialSlotCount':completion.get('activeEditorialSlotCount'),'underTargetSlots':len(completion.get('underTargetSlots') or []),'missingCanonicalBiographyCount':bio.get('missingCanonicalBiographyCount'),'biographyEnrichmentUnresolved':bio_ext.get('unresolvedCount'),'latinOnlyPersonNames':bio_gap.get('remainingLatinOnlyNameCount')},
      'children':{'knownChannels':len(media.get('sources') or []),'channelTarget':100,'contentTypes':children_types,'storyTypes':story_types,'subjects':len(subjects),'ageGroups':len(ages),'storyMatrixCells':len(story_types)*len(subjects)*len(ages),'storyTargetPerCell':5000},
      'catalogStatusCounts':dict(cat_counts),'gaps':gaps
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(payload,ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
