#!/usr/bin/env python3
from pathlib import Path
import json,datetime

ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'library'/'works'; OUT=ROOT/'data'/'ingested_library.json'

# Before rebuilding the public index, promote every READY_EPUB whose binary is
# actually present in the checkout into library/works. Missing binaries are
# reported but never exposed as fake published links.
try:
    from publish_generated_epubs import main as publish_generated_epubs
    publish_generated_epubs()
except Exception as exc:
    print('Generated EPUB promotion warning:', exc)

# GitHub Actions runners are ephemeral. Keep previously published entries from the
# committed index and overlay the files acquired/generated in the current runner.
previous={}
if OUT.exists():
    try:
        old=json.loads(OUT.read_text(encoding='utf-8'))
        for x in old.get('items',[]):
            key=str(x.get('id') or f"{x.get('workId','')}:{x.get('editionId','')}")
            if key and key!=':': previous[key]=x
    except Exception:
        previous={}

current={}
if STORE.exists():
    for meta_path in sorted(STORE.glob('*/editions/*/metadata.json')):
        try: m=json.loads(meta_path.read_text(encoding='utf-8'))
        except Exception: continue
        ed=meta_path.parent
        originals=sorted(ed.glob('original.*'))
        if not originals: continue
        original=originals[0]
        rel='/' + str(original.relative_to(ROOT)).replace('\\','/')
        fmt=str(m.get('format') or original.suffix.lstrip('.')).lower()
        readable=fmt in {'txt','html','pdf','epub'}
        searchable=fmt in {'txt','html','epub'} or bool(m.get('searchable'))
        listenable=fmt in {'txt','html','epub'} or bool(m.get('listenable'))
        watchable=fmt in {'mp4','webm','mkv'} or bool(m.get('watchable'))
        key=f"{m.get('workId','')}:{m.get('editionId','')}"
        current[key]={
            'id': key,
            'workId': m.get('workId'), 'editionId': m.get('editionId'),
            'titleOriginal': m.get('titleOriginal'), 'titleAr': m.get('titleAr'),
            'titleEn': m.get('titleEn'), 'titleFr': m.get('titleFr'),
            'author': m.get('author'), 'language': m.get('language'),
            'subjects': m.get('subjects') or [], 'siteSections': m.get('siteSections') or [],
            'format': fmt, 'mimeType': m.get('mimeType'), 'size': m.get('size'),
            'sha256': m.get('sha256'), 'localUrl': rel, 'readerUrl': rel,
            'capabilities': {'readable':readable,'searchable':searchable,'listenable':listenable,'watchable':watchable},
            'searchMode': 'fulltext-browser' if fmt in {'txt','html'} else ('epub-reader-search' if fmt=='epub' else ('ocr-index' if searchable and fmt=='pdf' else 'none')),
            'listenMode': 'browser-tts' if listenable and fmt in {'txt','html','epub'} else ('native-audio' if fmt in {'mp3','m4a','ogg','wav'} else 'none'),
            'watchMode': 'native-video' if watchable else 'none',
            'publishedAsset': True
        }

merged={**previous,**current}
items=sorted(merged.values(), key=lambda x:(str(x.get('titleAr') or x.get('titleOriginal') or ''),str(x.get('id') or '')))
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'schema':'ingested-library-v2','generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'count':len(items),'currentBatchCount':len(current),'items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'count':len(items),'currentBatchCount':len(current),'previousCount':len(previous),'output':str(OUT.relative_to(ROOT))},ensure_ascii=False))
