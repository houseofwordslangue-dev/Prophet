#!/usr/bin/env python3
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
published = json.loads((ROOT / 'data' / 'published_user_books.json').read_text(encoding='utf-8'))
ingested = json.loads((ROOT / 'data' / 'user_ingested_books.json').read_text(encoding='utf-8'))
items = published.get('items', [])
source = ingested.get('books', [])

assert items, 'published catalogue is empty'
ids = [str(x.get('id', '')) for x in items]
assert all(ids), 'published item without id'
assert len(ids) == len(set(ids)), 'duplicate published ids'
source_ids = {str(x.get('id', '')) for x in source}
missing = sorted(source_ids - set(ids))
assert not missing, f'user-ingested books missing from public catalogue: {missing}'

for item in items:
    assert item.get('publicationStatus', '').startswith('published-'), f"{item['id']}: not marked published"
    assert item.get('titleAr'), f"{item['id']}: missing Arabic title"
    caps = item.get('capabilities') or {}
    actionable = any(bool(caps.get(k)) for k in ('readable','searchable','listenable','watchable'))
    if actionable:
        url = item.get('readerUrl') or item.get('localUrl') or item.get('sourceUrl')
        assert url and url != '#', f"{item['id']}: enabled capability without a real URL"

cover = next((x for x in items if x.get('id') == 'quran-meaning-093'), None)
assert cover and cover.get('publicationStatus') == 'published-cover-only'
assert not any((cover.get('capabilities') or {}).values()), 'cover-only record exposes a false capability'

bookstore = (ROOT / 'assets' / 'bookstore.js').read_text(encoding='utf-8')
assert "data/published_user_books.json" in bookstore, 'bookstore does not load published user catalogue'
html = (ROOT / 'library.html').read_text(encoding='utf-8')
assert 'assets/bookstore.js' in html and 'assets/bookstore-published.css' in html

print(f'PASS: {len(items)} published catalogue records; {len(source_ids)} user-ingested source records covered; no dangling public capability buttons.')
