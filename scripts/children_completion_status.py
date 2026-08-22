#!/usr/bin/env python3
# GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md
from __future__ import annotations
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'data/children'
TAX=BASE/'taxonomy.json'
MEDIA=BASE/'media-sources.json'
OUT=BASE/'completion_status.json'
CHANNEL_TARGET=100
VIDEO_TARGET=1000
STORY_TARGET=5000
STORY_TYPES={'illustrated-stories','very-short-stories','animated-stories'}

def load(p,d):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except Exception:return d

def walk(v):
    if isinstance(v,dict):
        yield v
        for x in v.values(): yield from walk(x)
    elif isinstance(v,list):
        for x in v: yield from walk(x)

def infer_story_type(path:Path,o:dict):
    vals=' '.join(str(o.get(k) or '') for k in ('contentType','storyType','type','kind','collection')).lower()
    p=str(path).lower()
    if 'very-short' in vals or 'very_short' in vals or 'very-short' in p:return 'very-short-stories'
    if 'animated' in vals or 'animation' in vals or 'animated' in p:return 'animated-stories'
    if 'illustrated' in vals or 'illustration' in vals or 'illustrated' in p:return 'illustrated-stories'
    return None

def main():
    tax=load(TAX,{}) or {}; media=load(MEDIA,{}) or {}
    subjects=[str(x.get('id')) for x in tax.get('subjects',[]) if isinstance(x,dict) and x.get('id')]
    ages=[str(x.get('id')) for x in tax.get('ageGroups',[]) if isinstance(x,dict) and x.get('id')]
    content_types=[str(x.get('id')) for x in tax.get('contentTypes',[]) if isinstance(x,dict) and x.get('id')]
    story_types=[x for x in content_types if x in STORY_TYPES]

    channels={}
    for x in media.get('sources',[]) or []:
        if isinstance(x,dict):
            k=str(x.get('id') or x.get('url') or '').strip()
            if k:channels[k]=x

    videos={}; matrix=Counter(); stories=set(); audio=set(); books=set(); articles=set(); transcripts=set()
    for p in BASE.rglob('*.json'):
        if p in {TAX,MEDIA,OUT}:continue
        d=load(p,None)
        if d is None:continue
        for o in walk(d):
            if not isinstance(o,dict):continue
            oid=str(o.get('id') or o.get('slug') or '').strip()
            url=str(o.get('url') or o.get('sourceUrl') or o.get('videoUrl') or o.get('embedUrl') or '').strip()
            kind=' '.join(str(o.get(k) or '') for k in ('mediaType','contentType','type','kind')).lower()
            if ('youtube.com/' in url or 'youtu.be/' in url or 'video' in kind) and (oid or url): videos[oid or url]=o
            if 'audio' in kind and (oid or url):audio.add(oid or url)
            if 'book' in kind and (oid or url):books.add(oid or url)
            if ('article' in kind or 'reading' in kind or 'research' in kind) and (oid or url):articles.add(oid or url)
            if 'transcript' in kind and (oid or url):transcripts.add(oid or url)
            st=infer_story_type(p,o)
            if not st:continue
            age=str(o.get('ageGroup') or o.get('age') or '').strip()
            sub=str(o.get('subjectCategory') or o.get('subject') or o.get('category') or '').strip()
            if isinstance(o.get('subject'),dict):sub=str((o.get('subject') or {}).get('id') or '').strip()
            sid=oid or f'{p}:{age}:{sub}:{len(stories)}'
            if sid in stories:continue
            stories.add(sid)
            if st in story_types and sub in subjects and age in ages:matrix[f'{st}|{sub}|{age}']+=1

    cells=[]
    for st in story_types:
        for sub in subjects:
            for age in ages:
                key=f'{st}|{sub}|{age}'; count=matrix[key]
                cells.append({'storyType':st,'subject':sub,'ageGroup':age,'count':count,'deficit':max(0,STORY_TARGET-count)})
    under=[x for x in cells if x['count']<STORY_TARGET]
    under.sort(key=lambda x:(x['count'],x['storyType'],x['subject'],x['ageGroup']))
    state={
      'schema':'children-completion-state-v1','generatedAt':datetime.now(timezone.utc).isoformat(),'governedBy':'MASTER_OVERRIDING_INSTRUCTION.md',
      'verifiedChannelCount':len(channels),'channelTarget':CHANNEL_TARGET,'CHANNEL_TARGET_COMPLETE':len(channels)>=CHANNEL_TARGET,
      'verifiedVideoCount':len(videos),'videoTarget':VIDEO_TARGET,'VIDEO_TARGET_COMPLETE':len(videos)>=VIDEO_TARGET,
      'audioCount':len(audio),'bookCount':len(books),'articleReadingCount':len(articles),'transcriptCount':len(transcripts),
      'contentTypes':content_types,'storyTypes':story_types,'subjectCount':len(subjects),'ageGroupCount':len(ages),
      'storyTargetPerCell':STORY_TARGET,'storyMatrixCellCount':len(cells),'calculatedStoryMatrixTarget':len(cells)*STORY_TARGET,
      'totalDetectedStoryRecords':len(stories),'storyCountsByCell':{f"{x['storyType']}|{x['subject']}|{x['ageGroup']}":x['count'] for x in cells},
      'underTargetStoryCellCount':len(under),'emptyStoryCellCount':sum(x['count']==0 for x in under),'nextStoryTargetCell':under[0] if under else None,
      'STORY_TARGET_COMPLETE':not under,
      'CHILDREN_MEDIA_STORY_COMPLETION_COMPLETE':bool(len(channels)>=CHANNEL_TARGET and len(videos)>=VIDEO_TARGET and not under)
    }
    OUT.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(state,ensure_ascii=False))
    return 0
if __name__=='__main__':raise SystemExit(main())
