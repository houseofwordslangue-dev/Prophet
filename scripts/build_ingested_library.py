#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from pathlib import Path
import json,datetime

ROOT=Path(__file__).resolve().parents[1]
STORE=ROOT/'library'/'works'; OUT=ROOT/'data'/'ingested_library.json'


def load_json(path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def catalogue_rows():
    rows={}
    for path in sorted((ROOT/'data'/'catalogue').glob('*.json')):
        data=load_json(path,{}) or {}
        for raw in data.get('items',[]):
            if not isinstance(raw,list) or len(raw)<4: continue
            rid=str(raw[0] or '').strip()
            if not rid: continue
            rows[rid]={
                'id':rid,
                'section':raw[2] if len(raw)>2 else '',
                'titleAr':raw[3] if len(raw)>3 else '',
                'titleEn':raw[4] if len(raw)>4 else '',
                'authorAr':raw[5] if len(raw)>5 else '',
                'authorEn':raw[6] if len(raw)>6 else '',
                'rights':raw[8] if len(raw)>8 else '',
                'sourceUrl':raw[12] if len(raw)>12 else '',
                'catalogueStatus':raw[-1] if raw else ''
            }
    return rows


def lifecycle_registry(published_items):
    published_ids=set()
    for x in published_items:
        wid=str(x.get('workId') or '').strip()
        if wid: published_ids.add(wid)
        xid=str(x.get('id') or '').strip()
        if ':' in xid: published_ids.add(xid.split(':',1)[0])

    buckets={
        'published/pdf':[], 'published/epub':[], 'published/text':[], 'published/media':[],
        'ready/epub':[], 'ready/pdf':[], 'ready/source':[],
        'processing/import':[], 'processing/conversion':[], 'processing/revision':[],
        'incoming/source-pending':[], 'failed/retry':[]
    }

    def add(folder,row):
        item=dict(row)
        item['folder']=folder
        buckets.setdefault(folder,[]).append(item)

    # Published assets always win over queue or catalogue states.
    for x in published_items:
        fmt=str(x.get('format') or '').lower()
        folder='published/media' if fmt in {'mp3','m4a','ogg','wav','mp4','webm','mkv'} else ('published/epub' if fmt=='epub' else ('published/pdf' if fmt=='pdf' else 'published/text'))
        add(folder,{
            'id':x.get('workId') or x.get('id'), 'editionId':x.get('editionId'),
            'titleAr':x.get('titleAr'), 'titleEn':x.get('titleEn'), 'author':x.get('author'),
            'format':fmt, 'publishedAsset':True, 'localUrl':x.get('localUrl')
        })

    claimed=set(published_ids)

    # Generated EPUBs are ready only when generation has completed; they remain
    # separate from published assets until the binary is promoted and validated.
    generated=load_json(ROOT/'data'/'generated_epubs.json',{}) or {}
    for x in generated.get('items',[]):
        rid=str(x.get('id') or '').strip()
        if not rid or rid in claimed: continue
        status=str(x.get('status') or '').upper()
        row={'id':rid,'titleAr':x.get('titleAr'),'format':'epub','status':status,
             'sourcePath':x.get('epubPath'),'sha256':x.get('sha256'),'sizeBytes':x.get('sizeBytes')}
        if status=='READY_EPUB':
            add('ready/epub',row); claimed.add(rid)
        elif 'REVISION' in status:
            add('processing/revision',row); claimed.add(rid)
        elif 'FAIL' in status or 'INVALID' in status:
            add('failed/retry',row); claimed.add(rid)
        else:
            add('processing/conversion',row); claimed.add(rid)

    # Archive import batch is explicitly in-flight acquisition/import work.
    archive=load_json(ROOT/'data'/'archive_import_batch.json',{}) or {}
    for x in archive.get('items',[]):
        rid=str(x.get('catalogue_id') or '').strip()
        if not rid or rid in claimed: continue
        add('processing/import',{'id':rid,'titleAr':x.get('title'),'archiveId':x.get('archive_id'),'status':'IMPORT_QUEUED'})
        claimed.add(rid)

    # Preserve acquisition-state jobs without destructively moving their files.
    state=load_json(ROOT/'private'/'acquisition_state.json',{}) or {}
    for x in state.get('items',[]):
        rid=str(x.get('id') or x.get('workId') or '').strip()
        if not rid or rid in claimed: continue
        status=str(x.get('status') or '').lower()
        row={'id':rid,'titleAr':x.get('titleAr') or x.get('title'),'status':x.get('status')}
        if any(k in status for k in ('fail','error','invalid')): folder='failed/retry'
        elif 'revis' in status: folder='processing/revision'
        elif any(k in status for k in ('convert','epub','ocr')): folder='processing/conversion'
        elif any(k in status for k in ('download','import','acquir','pending','queue')): folder='processing/import'
        elif any(k in status for k in ('ready','complete','success')): folder='ready/source'
        else: folder='processing/import'
        add(folder,row); claimed.add(rid)

    # Every remaining catalogue record receives one stable lifecycle home.
    for rid,row in catalogue_rows().items():
        if rid in claimed: continue
        st=str(row.get('catalogueStatus') or '').lower()
        if 'revis' in st: folder='processing/revision'
        elif any(k in st for k in ('convert','ocr','epub')): folder='processing/conversion'
        elif any(k in st for k in ('import','mirror','download')) and 'awaiting' not in st: folder='processing/import'
        elif any(k in st for k in ('source-ready','source-verified')) and row.get('sourceUrl'): folder='ready/source'
        else: folder='incoming/source-pending'
        add(folder,row)

    for rows in buckets.values():
        rows.sort(key=lambda x:(str(x.get('titleAr') or x.get('titleEn') or ''),str(x.get('id') or '')))

    counts={k:len(v) for k,v in buckets.items()}
    return {
        'schema':'resource-lifecycle-v1',
        'policy':{
            'noDestructiveMoveWhileProcessing':True,
            'publishedCanonicalPath':'library/works/<workId>/editions/<editionId>/original.<format>',
            'sourceArchive':{
                'root':'Prophet Muhammad Resources — Archive.org',
                'pdf':'PDF/',
                'epub':'EPUB/'
            },
            'transitionOrder':['incoming/source-pending','processing/import','processing/conversion','processing/revision','ready/*','published/*'],
            'publishRule':'Only validated local assets may enter published/* and receive reader URLs.'
        },
        'counts':counts,
        'totalTracked':sum(counts.values()),
        'folders':buckets
    }


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
            'resourceFolder': ('published/epub' if fmt=='epub' else ('published/pdf' if fmt=='pdf' else ('published/media' if fmt in {'mp3','m4a','ogg','wav','mp4','webm','mkv'} else 'published/text'))),
            'lifecycleStatus':'published',
            'capabilities': {'readable':readable,'searchable':searchable,'listenable':listenable,'watchable':watchable},
            'searchMode': 'fulltext-browser' if fmt in {'txt','html'} else ('epub-reader-search' if fmt=='epub' else ('ocr-index' if searchable and fmt=='pdf' else 'none')),
            'listenMode': 'browser-tts' if listenable and fmt in {'txt','html','epub'} else ('native-audio' if fmt in {'mp3','m4a','ogg','wav'} else 'none'),
            'watchMode': 'native-video' if watchable else 'none',
            'publishedAsset': True
        }

merged={**previous,**current}
items=sorted(merged.values(), key=lambda x:(str(x.get('titleAr') or x.get('titleOriginal') or ''),str(x.get('id') or '')))
# Backfill lifecycle fields on previously published entries without changing URLs.
for x in items:
    fmt=str(x.get('format') or '').lower()
    x['lifecycleStatus']='published'
    x['resourceFolder']=('published/epub' if fmt=='epub' else ('published/pdf' if fmt=='pdf' else ('published/media' if fmt in {'mp3','m4a','ogg','wav','mp4','webm','mkv'} else 'published/text')))

payload={
    'schema':'ingested-library-v3',
    'generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'count':len(items),
    'currentBatchCount':len(current),
    'items':items,
    'resourceLifecycle':lifecycle_registry(items)
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'count':len(items),'currentBatchCount':len(current),'previousCount':len(previous),'trackedResources':payload['resourceLifecycle']['totalTracked'],'folders':payload['resourceLifecycle']['counts'],'output':str(OUT.relative_to(ROOT))},ensure_ascii=False))
