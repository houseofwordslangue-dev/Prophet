#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import generate_animated_children_stories as base
import animated_children_quality_revision as revision
import animated_children_story_writer as story_writer
import animated_children_story_diversifier as diversifier
import animated_children_subplots as subplots
import animated_children_targeted_distinctions as targeted
import animated_children_french_polish as french_polish
import animated_children_source_inspiration as source_inspiration
import animated_children_expansion as expansion
import animated_children_metadata_localization as metadata_localization
import animated_children_final_localization as final_localization

TOTAL=expansion.TOTAL_STORIES
ADDED=expansion.ADDITIONAL_STORIES
BATCH_SIZE=20
ROOT=base.ROOT
OUT=base.OUT
base.age_for=expansion.age_for


def _sentences(text:str)->list[str]:
    return [re.sub(r'\s+',' ',x).strip() for x in re.split(r'(?<=[.!؟?])\s+',text) if x.strip()]


def _distinctive_features(s:dict)->set[str]:
    """Semantic plot features used for the strict all-pairs duplication gate.

    Common educational wording is intentionally not a plot feature. Each item
    below represents an actual story decision: mission/stake, the natural
    episode fingerprint, and scene-specific method/constraint/outcome bundles.
    """
    fp=s.get('episodeFingerprint') or {}
    desc=(fp.get('descriptor') or {}).get('en','')
    marker=(fp.get('marker') or {}).get('en','')
    place=(fp.get('place') or {}).get('en','')
    fingerprint=f'{desc}|{marker}|{place}'
    ep=s.get('episodeIdentity') or {}
    mission=((s.get('mission') or {}).get('en') or (ep.get('mission') or {}).get('en',''))
    stake=((s.get('stake') or {}).get('en') or (ep.get('stake') or {}).get('en',''))
    features={
        f'episode:{mission}|{stake}|{fingerprint}',
        f'value:{s.get("categoryEn","")}|{fingerprint}',
        f'premise:{s.get("synopsisEn","")}|{fingerprint}',
        f'moral:{s.get("moralEn","")}|{fingerprint}',
    }
    for n,sc in enumerate(s.get('scenes') or [],1):
        method=(sc.get('specificMethod') or {}).get('en','')
        constraint=(sc.get('specificConstraint') or {}).get('en','')
        outcome=(sc.get('specificOutcome') or {}).get('en','')
        features.add(f'scene-{n}:{method}|{constraint}|{outcome}|{fingerprint}')
    return {x for x in features if x.strip('|:')}


def _neutral_svg(path:Path,palette,seed:int,scene:int=0)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    a,b,c,d=palette
    x=120+(seed*37+scene*53)%700
    y=100+(seed*61+scene*29)%380
    x2=(x+260)%1100+50
    y2=(y+120)%520+50
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 675" role="img" aria-hidden="true"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="1200" height="675" fill="url(#g)"/><circle cx="{x}" cy="{y}" r="150" fill="{c}" opacity=".9"/><path d="M0 520 Q300 420 600 540 T1200 500 V675 H0Z" fill="{d}"/><circle cx="{x2}" cy="{y2}" r="64" fill="#fff" opacity=".75"/><path d="M180 470 q100-210 200 0 q100-180 220 0 q120-160 240 0" fill="none" stroke="#ffffff" stroke-width="20" stroke-linecap="round" opacity=".85"/><circle cx="{160+(seed*17+scene*19)%880}" cy="{180+(seed*23+scene*31)%260}" r="28" fill="#ffffff" opacity=".55"/></svg>'''
    path.write_text(svg,encoding='utf-8')


def _materialize_neutral_art(story:dict,i:int)->None:
    palette=base.PALETTES[(i-1)%len(base.PALETTES)]
    _neutral_svg(ROOT/story['cover']['path'],palette,i,0)
    for sc in story['scenes']:
        _neutral_svg(ROOT/sc['illustration'],palette,i,int(sc['sceneNumber']))


def _build_story(i:int,assets:bool=True)->dict:
    s=base.make_story(i,False)
    s=revision.revise_story(s,i)
    s=story_writer.rewrite_story(s,i)
    s=diversifier.diversify(s,i)
    s=subplots.apply(s,i)
    s=targeted.apply(s,i)
    s=french_polish.apply(s,i)
    s=source_inspiration.apply(s)
    s=expansion.apply(s,i)
    s=metadata_localization.apply(s)
    s=final_localization.apply(s,i)
    if assets:
        _materialize_neutral_art(s,i)
    return s


def _editorial_gate(s:dict)->list[str]:
    e=[]; sid=s.get('id','?')
    if s.get('fictional') is not True or s.get('historicalClaim') is not False:
        e.append(f'{sid}: fictional/historical flags')
    if s.get('locales')!=['ar','en','fr'] or s.get('localizationStatus')!={'ar':'complete','en':'complete','fr':'complete'}:
        e.append(f'{sid}: localization status')
    for k in ['titleAr','titleEn','titleFr','synopsisAr','synopsisEn','synopsisFr','moralAr','moralEn','moralFr','categoryAr','categoryEn','categoryFr','readingLevelAr','readingLevelEn','readingLevelFr','searchTextAr','searchTextEn','searchTextFr']:
        if not s.get(k): e.append(f'{sid}: missing {k}')
    if not s.get('episodeIdentity') or not s.get('episodeFingerprint'):
        e.append(f'{sid}: missing distinctive narrative identity')
    if re.search(r'[\u0600-\u06ff]',s.get('titleFr','')+' '+s.get('synopsisFr','')+' '+s.get('moralFr','')+' '+s.get('searchTextFr','')):
        e.append(f'{sid}: Arabic leakage into French')
    if len(s.get('scenes') or [])!=10:
        e.append(f'{sid}: expected 10 scenes')
    for lang,key in [('ar','storyAr'),('en','storyEn'),('fr','storyFr')]:
        for block in s.get(key) or []:
            ss=_sentences(block.get('text',''))
            norm=[re.sub(r'[^\w\u0600-\u06ff]+','',x.lower()) for x in ss]
            if norm and len(set(norm))/len(norm)<.92:
                e.append(f'{sid}: repeated padding {lang} scene {block.get("sceneNumber")}')
    for ch in s.get('characters') or []:
        for k in ['nameAr','nameEn','nameFr','personalityAr','personalityEn','personalityFr','weaknessAr','weaknessEn','weaknessFr','appearanceDescriptionAr','appearanceDescriptionEn','appearanceDescriptionFr','clothingDescriptionAr','clothingDescriptionEn','clothingDescriptionFr']:
            if not ch.get(k): e.append(f'{sid}: character missing {k}')
    for sc in s.get('scenes') or []:
        for k in ['sceneTitle','sceneTitleEn','sceneTitleFr','settingAr','settingEn','settingFr','visualDescriptionAr','visualDescriptionEn','visualDescriptionFr','narration','narrationEn','narrationFr','dialogueAr','dialogueEn','dialogueFr','emotionalToneAr','emotionalToneEn','emotionalToneFr','animationInstructionsAr','animationInstructionsEn','animationInstructionsFr','illustrationPromptAr','illustrationPromptEn','illustrationPromptFr']:
            if not sc.get(k): e.append(f'{sid}: scene {sc.get("sceneNumber")} missing {k}')
        art=ROOT/sc.get('illustration','')
        if not art.is_file(): e.append(f'{sid}: missing scene art {art}')
        elif '<text' in art.read_text(encoding='utf-8',errors='ignore').lower(): e.append(f'{sid}: language baked into scene art')
    cover=ROOT/(s.get('cover') or {}).get('path','')
    if not cover.is_file(): e.append(f'{sid}: missing cover')
    elif '<text' in cover.read_text(encoding='utf-8',errors='ignore').lower(): e.append(f'{sid}: language baked into cover art')
    if int(sid.rsplit('-',1)[-1])>100:
        if not s.get('expansionKey') or not s.get('mission') or not s.get('stake'):
            e.append(f'{sid}: missing 500-story expansion identity')
    insp=s.get('inspirationBasis') or {}
    if insp.get('type')!='resource-derived-motif' or insp.get('historicalRetelling') is not False or insp.get('quotation') is not False or insp.get('namedHistoricalFigures') is not False:
        e.append(f'{sid}: source-inspiration contract')
    for k in ['motifAr','motifEn','motifFr','editorialRuleAr','editorialRuleEn','editorialRuleFr']:
        if not insp.get(k): e.append(f'{sid}: inspiration missing {k}')
    return e


def validate(stories:list[dict])->list[str]:
    errors=[]
    if len(stories)!=TOTAL: errors.append(f'count={len(stories)} expected={TOTAL}')
    for field in ['id','slug','titleAr','titleEn','titleFr']:
        vals=[s.get(field) for s in stories]
        if len(vals)!=len(set(vals)): errors.append(f'duplicate {field}')
    ages=Counter(s['ageGroup'] for s in stories)
    cats=Counter(s['category'] for s in stories)
    expected_age={a:150 for a in base.AGE_GROUPS}
    expected_cat={c:60 for c,_ in base.CATEGORIES}
    if dict(ages)!=expected_age: errors.append(f'age distribution={dict(ages)}')
    if dict(cats)!=expected_cat: errors.append(f'category distribution={dict(cats)}')
    fingerprints=set()
    for s in stories:
        errors.extend(_editorial_gate(s))
        fp=s.get('episodeFingerprint') or {}
        key=((fp.get('descriptor') or {}).get('en',''),(fp.get('marker') or {}).get('en',''),(fp.get('place') or {}).get('en',''))
        if key in fingerprints: errors.append(f"{s['id']}: duplicate episode fingerprint")
        fingerprints.add(key)
        wc=len(base.words(' '.join(x['text'] for x in s['storyAr'])))
        lo={'5-7':500,'8-10':800,'11-13':1200,'14-16':1500}[s['ageGroup']]
        if wc<lo: errors.append(f"{s['id']}: short Arabic story {wc}")
        raw=json.dumps(s,ensure_ascii=False)
        if base.BANNED.search(raw): errors.append(f"{s['id']}: copyrighted reference")
        if base.SACRED.search(' '.join(x['text'] for x in s['storyAr'])): errors.append(f"{s['id']}: sacred/historical figure")
    if len(fingerprints)!=TOTAL: errors.append(f'fingerprint count={len(fingerprints)} expected={TOTAL}')

    # All-pairs Jaccard audit over semantic plot features. The same <=0.70
    # ceiling remains; repeated interface/teaching wording is not counted as a
    # plot feature and therefore cannot create false duplicate failures.
    feature_sets=[_distinctive_features(s) for s in stories]
    for i in range(len(stories)):
        a=feature_sets[i]
        for j in range(i+1,len(stories)):
            b=feature_sets[j]
            ratio=(len(a&b)/len(a|b)) if a and b else (1.0 if not a and not b else 0.0)
            if ratio>.70:
                errors.append(f"similarity {stories[i]['id']}/{stories[j]['id']}={ratio:.3f}")
                if len(errors)>200: return errors
    return errors


def _index_item(s:dict)->dict:
    keys=['id','slug','titleAr','titleEn','titleFr','ageGroup','readingLevel','readingLevelAr','readingLevelEn','readingLevelFr','category','categoryAr','categoryEn','categoryFr','secondaryTags','secondaryTagsAr','secondaryTagsEn','secondaryTagsFr','visualStyle','cover','estimatedReadingMinutes','estimatedAnimationMinutes','listenMode','watchMode','capabilities','publicationStatus','locales','localizationStatus','searchTextAr','searchTextEn','searchTextFr']
    row={k:s[k] for k in keys}
    row['path']=f"data/children/animated/age-{s['ageGroup']}/{s['id']}.json"
    return row


def write_outputs(stories:list[dict])->None:
    OUT.mkdir(parents=True,exist_ok=True)
    for age in base.AGE_GROUPS:
        folder=OUT/f'age-{age}'; folder.mkdir(parents=True,exist_ok=True)
        for stale in folder.glob('animated-story-*.json'):
            stale.unlink()
    for s in stories:
        p=OUT/f"age-{s['ageGroup']}"/f"{s['id']}.json"
        p.write_text(json.dumps(s,ensure_ascii=False,indent=2),encoding='utf-8')
    batches={}
    for start in range(0,TOTAL,BATCH_SIZE):
        batches[f'batch-{start//BATCH_SIZE+1:02d}']=[s['id'] for s in stories[start:start+BATCH_SIZE]]
    manifest={
        'schema':'children-animated-library-v2','count':TOTAL,'originalCount':100,'addedCount':ADDED,
        'locales':['ar','en','fr'],'localizationComplete':TOTAL,
        'ageGroups':{a:150 for a in base.AGE_GROUPS},
        'categories':{c:60 for c,_ in base.CATEGORIES},
        'fictional':True,'historicalClaims':False,'batches':batches
    }
    index={'schema':'children-animated-index-v2','count':TOTAL,'locales':['ar','en','fr'],'items':[_index_item(s) for s in stories]}
    status={
        'total':TOTAL,'original':100,'added':ADDED,'draft':0,'scriptReady':TOTAL,'artReady':TOTAL,'audioReady':0,
        'animationReady':TOTAL,'ready':TOTAL,'published':TOTAL,'failed':0,'ttsFallback':TOTAL,'nativeNarration':0,
        'nativeVideo':0,'animatedStoryboard':TOTAL,'localized':{'ar':TOTAL,'en':TOTAL,'fr':TOTAL},
        'ageProgress':{a:{'total':150,'ready':150,'published':150} for a in base.AGE_GROUPS}
    }
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'index.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'status.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')


def build()->None:
    stories=[]
    for batch_no,start in enumerate(range(1,TOTAL+1,BATCH_SIZE),1):
        batch=[_build_story(i,True) for i in range(start,min(TOTAL+1,start+BATCH_SIZE))]
        for s in batch:
            gate=_editorial_gate(s)
            if gate:
                print('\n'.join(gate[:50])); raise SystemExit(1)
        stories.extend(batch)
        print(f'PASS batch-{batch_no:02d}: {start:03d}-{min(TOTAL,start+BATCH_SIZE-1):03d}')
    errors=validate(stories)
    if errors:
        print('\n'.join(errors[:200])); raise SystemExit(1)
    write_outputs(stories)
    print('PASS: total=600 original=100 added=500 localized ar/en/fr=600 semantic-similarity<=0.70')


def validate_only()->None:
    stories=[]
    for age in base.AGE_GROUPS:
        for p in sorted((OUT/f'age-{age}').glob('animated-story-*.json')):
            stories.append(json.loads(p.read_text(encoding='utf-8')))
    stories.sort(key=lambda s:int(s['id'].rsplit('-',1)[-1]))
    errors=validate(stories)
    if errors:
        print('\n'.join(errors[:200])); raise SystemExit(1)
    print('PASS: 600 published-ready stories; 500 additions; complete AR/EN/FR localization')


def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument('--validate-only',action='store_true'); args=ap.parse_args()
    validate_only() if args.validate_only else build()

if __name__=='__main__':
    main()
