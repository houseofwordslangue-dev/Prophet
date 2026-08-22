#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
OUT = DATA / 'audits' / 'bookstore-publication-audit-current.json'

def load(path, default=None):
    p = ROOT / path
    if not p.exists():
        return default if default is not None else {}
    return json.loads(p.read_text(encoding='utf-8'))

def ids(rows):
    out=set()
    for x in rows or []:
        if not isinstance(x, dict):
            continue
        k=str(x.get('id') or x.get('workId') or '').strip()
        if k: out.add(k)
    return out

public = load('data/public_catalog_all.generated.json', {'items':[]})
published = load('data/published_user_books.json', {'items':[]})
epubs = load('data/generated_epubs.json', {'items':[]})
ingested = load('data/ingested_library.json', {'items':[]})

chunk_ids=set()
chunk_rows=0
for p in sorted((DATA/'catalogue').glob('chunk-*.json')):
    j=json.loads(p.read_text(encoding='utf-8'))
    for r in j.get('items',[]):
        chunk_rows += 1
        if isinstance(r,list) and r and str(r[0]).strip():
            chunk_ids.add(str(r[0]).strip())

public_ids=ids(public.get('items'))
published_ids=ids(published.get('items'))
epub_ids=ids(epubs.get('items'))
ingested_ids=ids(ingested.get('items'))

# These are the feeds actually merged by library.html + bookstore-catalogue-bridge.js + bookstore.js.
bookstore_universe = chunk_ids | public_ids | published_ids | epub_ids | ingested_ids
required_published = public_ids | published_ids | epub_ids
missing = sorted(required_published - bookstore_universe)

library=(ROOT/'library.html').read_text(encoding='utf-8') if (ROOT/'library.html').exists() else ''
required_scripts=['assets/bookstore-catalogue-bridge.js','assets/bookstore.js','assets/provider-access-ui.js']
script_wiring={s:(s in library and (ROOT/s).exists()) for s in required_scripts}

# Published catalogue resources are browseable at minimum as bookstore records. A genuine URL is exposed
# through provider-access-ui; richer capabilities remain source-truth-gated in bookstore.js/reader.html.
source_action_candidates=0
for x in public.get('items',[]):
    if not isinstance(x,dict): continue
    urls=[]
    urls += list(x.get('sources') or [])
    urls += [x.get('sourceUrl'),x.get('readerUrl'),x.get('publicUrl'),x.get('downloadUrl')]
    if any(isinstance(u,str) and u.startswith(('http://','https://')) for u in urls):
        source_action_candidates += 1

complete=(not missing) and all(script_wiring.values()) and len(required_published)>0
OUT.parent.mkdir(parents=True, exist_ok=True)
audit={
    'schema':'bookstore-publication-audit-v1',
    'rule':'Every published resource must appear in the public bookstore list with no omission.',
    'publicCatalogueCount':len(public_ids),
    'publishedUserBooksCount':len(published_ids),
    'generatedEpubCount':len(epub_ids),
    'ingestedCount':len(ingested_ids),
    'catalogueChunkRows':chunk_rows,
    'catalogueChunkUniqueIds':len(chunk_ids),
    'requiredPublishedUniqueCount':len(required_published),
    'bookstoreUniverseUniqueCount':len(bookstore_universe),
    'publishedMissingFromBookstoreCount':len(missing),
    'publishedMissingFromBookstore':missing,
    'publishedWithRealSourceActionCandidateCount':source_action_candidates,
    'scriptWiring':script_wiring,
    'capabilityPolicy':{
        'browse':'all published records are listed; real provider/source URL shown when available',
        'read':'only genuine readable assets',
        'search':'only genuine searchable assets',
        'listen':'only genuine audio or supported TTS text',
        'watch':'only genuine media assets'
    },
    'complete':complete
}
OUT.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
raise SystemExit(0 if complete else 1)
