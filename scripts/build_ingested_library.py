#!/usr/bin/env python3
from pathlib import Path
import json,datetime
ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'library'/'works'; OUT=ROOT/'data'/'ingested_library.json'
items=[]
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
        searchable=fmt in {'txt','html'} or bool(m.get('searchable'))
        listenable=fmt in {'txt','html'} or bool(m.get('listenable'))
        watchable=fmt in {'mp4','webm','mkv'} or bool(m.get('watchable'))
        items.append({
            'id': f"{m.get('workId','')}:{m.get('editionId','')}",
            'workId': m.get('workId'), 'editionId': m.get('editionId'),
            'titleOriginal': m.get('titleOriginal'), 'titleAr': m.get('titleAr'),
            'titleEn': m.get('titleEn'), 'titleFr': m.get('titleFr'),
            'author': m.get('author'), 'language': m.get('language'),
            'subjects': m.get('subjects') or [], 'siteSections': m.get('siteSections') or [],
            'format': fmt, 'mimeType': m.get('mimeType'), 'size': m.get('size'),
            'sha256': m.get('sha256'), 'localUrl': rel, 'readerUrl': rel,
            'capabilities': {'readable':readable,'searchable':searchable,'listenable':listenable,'watchable':watchable},
            'searchMode': 'fulltext-browser' if searchable else ('ocr-index' if fmt=='pdf' else 'none'),
            'listenMode': 'browser-tts' if listenable and fmt in {'txt','html'} else ('native-audio' if fmt in {'mp3','m4a','ogg','wav'} else 'none'),
            'watchMode': 'native-video' if watchable else 'none'
        })
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'schema':'ingested-library-v1','generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'count':len(items),'items':items},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'count':len(items),'output':str(OUT.relative_to(ROOT))},ensure_ascii=False))
