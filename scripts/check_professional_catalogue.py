#!/usr/bin/env python3
import base64, gzip, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/catalogue/manifest.json').read_text(encoding='utf-8'))
assert manifest['version'].startswith('professional-enrichment-')
raw=base64.b64decode((ROOT/manifest['compressedPayload']).read_text(encoding='utf-8').strip())
payload=json.loads(gzip.decompress(raw).decode('utf-8'))
schema=payload['schema']; rows=payload['items']
assert schema==manifest['schema'], 'schema mismatch'
assert len(rows)==manifest['baselineCount']==689, f"baseline count {len(rows)}"
records=[dict(zip(schema,row)) for row in rows]
ids=[str(r['id']) for r in records]
assert len(set(ids))==689, 'duplicate historical IDs'
assert all(str(r.get('titleAr','')).strip() for r in records), 'blank canonical Arabic display title'

bib=Counter(r.get('bibliographicStatus') for r in records)
levels=Counter(r.get('recordLevel') for r in records)
access=Counter(r.get('accessResolutionStatus') for r in records)
manif=Counter(r.get('manifestationStatus') for r in records)
expected=manifest['audit']
assert dict(bib)==expected['bibliographicStatus'], (bib,expected['bibliographicStatus'])
assert dict(levels)==expected['recordLevels'], (levels,expected['recordLevels'])
assert dict(access)==expected['accessResolution'], (access,expected['accessResolution'])
assert dict(manif)==expected['manifestationStatus'], (manif,expected['manifestationStatus'])
assert sum(1 for r in records if str(r.get('titleAr','')).strip())==expected['titleAr']
assert sum(1 for r in records if r.get('bibliographicStatus')=='RESEARCH_PENDING')==expected['identityResearchPending']
assert sum(1 for r in records if r.get('accessResolutionStatus') in {'EXACT_SOURCE_REGISTERED','LOCAL_ASSET_REGISTERED'})==expected['exactOrLocalSource']
assert sum(1 for r in records if r.get('accessResolutionStatus')!='SOURCE_RESEARCH_PENDING')==expected['discoveryOrBetter']

uploaded=json.loads((ROOT/'data/published_user_books.json').read_text(encoding='utf-8'))['items']
uids=[str(x['id']) for x in uploaded]
assert len(uids)==manifest['currentUploadedOverlayCount']==12
assert len(set(uids))==12
intersection=set(ids)&set(uids)
assert len(intersection)==manifest['overlapCount']==5, sorted(intersection)
assert len(set(ids)|set(uids))==manifest['expectedUniqueAfterOverlay']==696

# Historical payload contains bibliographic/source metadata only; UI capabilities are attached separately by the current overlay.
assert 'capabilities' not in schema
print('PASS professional catalogue:',len(records),'historical +',len(uploaded),'overlay -',len(intersection),'overlap =',len(set(ids)|set(uids)),'unique')
print('Bibliographic:',dict(bib))
print('Access:',dict(access))
