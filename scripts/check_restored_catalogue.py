#!/usr/bin/env python3
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/catalogue/manifest.json').read_text(encoding='utf-8'))
rows=[]
for chunk in manifest['chunks']:
    path=ROOT/chunk['path']
    data=json.loads(path.read_text(encoding='utf-8'))
    items=data.get('items',[])
    assert len(items)==chunk['count'], f"{chunk['path']}: expected {chunk['count']}, got {len(items)}"
    rows.extend(items)
assert len(rows)==manifest['baselineCount']==689, f"restored baseline count mismatch: {len(rows)}"
ids=[str(r[0]) for r in rows]
assert len(set(ids))==len(ids)==689, 'restored catalogue contains duplicate ids'
published=json.loads((ROOT/'data/published_user_books.json').read_text(encoding='utf-8')).get('items',[])
published_ids={str(x['id']) for x in published}
assert len(published_ids)==manifest['currentUploadedOverlayCount']==12, 'uploaded overlay count mismatch'
overlap=len(set(ids)&published_ids)
assert overlap==manifest['overlapCount']==5, f'overlay overlap mismatch: {overlap}'
union=len(set(ids)|published_ids)
assert union==manifest['expectedUniqueAfterOverlay']==696, f'expected 696 unique records, got {union}'
loader=(ROOT/'assets/catalogue-restore.js').read_text(encoding='utf-8')
assert 'capabilities:{readable:false,searchable:false,listenable:false,watchable:false}' in loader, 'restored historical records must not expose fake public actions'
html=(ROOT/'library.html').read_text(encoding='utf-8')
assert html.index('assets/catalogue-restore.js') < html.index('assets/bookstore.js'), 'catalogue restore must load before bookstore app'
print(f'PASS: restored={len(ids)}, uploaded={len(published_ids)}, overlap={overlap}, live_unique={union}')
