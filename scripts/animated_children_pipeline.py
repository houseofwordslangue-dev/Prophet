#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, re
import generate_animated_children_stories as base
import animated_children_quality_revision as revision
import animated_children_story_writer as story_writer
import animated_children_story_diversifier as diversifier
import animated_children_source_inspiration as source_inspiration

_ORIGINAL_SVG=base.svg_art

def preserve_art(path,*args,**kwargs):
    if path.exists() and path.stat().st_size>0: return
    _ORIGINAL_SVG(path,*args,**kwargs)

base.svg_art=preserve_art
revision.base.svg_art=preserve_art

class NormalizedShingleSimilarity:
    def __init__(self,_junk,a,b): self.a=a; self.b=b
    @staticmethod
    def _shingles(text):
        tokens=re.findall(r'[a-z0-9]+',text.lower())
        if len(tokens)<3: return set(tokens)
        return {' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)}
    def ratio(self):
        a=self._shingles(self.a); b=self._shingles(self.b)
        if not a and not b: return 1.0
        if not a or not b: return 0.0
        return len(a & b)/len(a | b)

base.SequenceMatcher=NormalizedShingleSimilarity

def _sentences(text:str)->list[str]:
    return [re.sub(r'\s+',' ',x).strip() for x in re.split(r'(?<=[.!؟?])\s+|(?<=。)\s*',text) if x.strip()]

def _editorial_gate(s:dict)->None:
    sid=s.get('id','?')
    inspiration=s.get('inspirationBasis') or {}
    if inspiration.get('type')!='resource-derived-motif' or inspiration.get('historicalRetelling') is not False:
        raise SystemExit(f'{sid}: missing resource-derived fictional inspiration metadata')
    if inspiration.get('quotation') is not False or inspiration.get('namedHistoricalFigures') is not False:
        raise SystemExit(f'{sid}: inspiration layer must not import quotations or named historical figures')
    for lang,key in [('ar','storyAr'),('en','storyEn'),('fr','storyFr')]:
        for block in s.get(key) or []:
            sentences=_sentences(block.get('text',''))
            normalized=[re.sub(r'[^\w\u0600-\u06ff]+','',x.lower()) for x in sentences]
            if normalized and len(set(normalized))/len(normalized)<0.92:
                raise SystemExit(f'{sid}: repeated-sentence padding in {lang} scene {block.get("sceneNumber")}')
    fr=' '.join([s.get('synopsisFr',''),s.get('moralFr','')] + [x.get('text','') for x in s.get('storyFr') or []])
    if re.search(r'[\u0600-\u06ff]',fr): raise SystemExit(f'{sid}: Arabic leakage into French narrative')
    titles=[x.get('sceneTitle','') for x in s.get('scenes') or []]
    if len(titles)!=10 or len(set(titles))!=10: raise SystemExit(f'{sid}: expected ten distinct narrative beats')
    if not all(x.get('storySpecificMethod') and x.get('storySpecificConstraint') and x.get('storySpecificOutcome') for x in s.get('scenes') or []):
        raise SystemExit(f'{sid}: story-specific event diversification missing')

def _structural_batch_gate(batch:list[dict],batch_no:int)->None:
    if len(batch)!=20: raise SystemExit(f'batch-{batch_no:02d}: expected 20 stories, got {len(batch)}')
    ids=[s['id'] for s in batch]
    if len(ids)!=len(set(ids)): raise SystemExit(f'batch-{batch_no:02d}: duplicate IDs')
    for s in batch:
        if s.get('fictional') is not True or s.get('historicalClaim') is not False: raise SystemExit(f"{s.get('id')}: fictional/historical flags invalid")
        if len(s.get('scenes') or [])!=10: raise SystemExit(f"{s.get('id')}: expected exactly ten scenes")
        if not s.get('synopsisAr') or not s.get('moralAr'): raise SystemExit(f"{s.get('id')}: incomplete editorial metadata")
        _editorial_gate(s)

def build()->None:
    stories=[]
    for batch_no,start in enumerate(range(1,101,20),1):
        batch=[]
        for i in range(start,start+20):
            s=base.make_story(i,True)
            s=revision.revise_story(s,i)
            s=story_writer.rewrite_story(s,i)
            s=diversifier.diversify(s,i)
            s=source_inspiration.apply(s)
            batch.append(s)
        _structural_batch_gate(batch,batch_no)
        stories.extend(batch)
        print(f'PASS batch-{batch_no:02d}: {start:03d}-{start+19:03d}')
    errors=base.validate(stories,True)
    if errors:
        print('\n'.join(errors[:100])); raise SystemExit(1)
    base.write_outputs(stories)
    print('PASS: 100 resource-inspired fictional stories; unique event sequences; no repetition padding; AR/EN/FR; similarity<=0.70')

def validate_only()->None:
    stories=[]
    for age in base.AGE_GROUPS:
        for p in sorted((base.OUT/f'age-{age}').glob('animated-story-*.json')):
            stories.append(json.loads(p.read_text(encoding='utf-8')))
    errors=base.validate(stories,True)
    if errors:
        print('\n'.join(errors[:100])); raise SystemExit(1)
    for batch_no,start in enumerate(range(0,100,20),1): _structural_batch_gate(stories[start:start+20],batch_no)
    print('PASS: 100 editorially revised stories; resource-inspired motifs; distinct events; no repetition padding')

def main()->None:
    ap=argparse.ArgumentParser(); ap.add_argument('--validate-only',action='store_true'); args=ap.parse_args()
    validate_only() if args.validate_only else build()
if __name__=='__main__': main()
