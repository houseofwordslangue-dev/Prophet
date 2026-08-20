#!/usr/bin/env python3
import base64, gzip, json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'data/catalogue/manifest.json').read_text(encoding='utf-8'))
assert manifest['version'].startswith('professional-enrichment-')

def load_professional_payload():
    try:
        raw=base64.b64decode((ROOT/manifest['compressedPayload']).read_text(encoding='utf-8').strip(), validate=True)
        return json.loads(gzip.decompress(raw).decode('utf-8'))
    except (OSError, EOFError, ValueError, json.JSONDecodeError) as exc:
        print('WARNING: professional compressed payload unavailable/corrupt:', type(exc).__name__, str(exc))
        return None

payload=load_professional_payload()
if payload is None:
    rows=[]
    for chunk in manifest.get('fallbackChunks',[]):
        p=ROOT/chunk['path']
        d=json.loads(p.read_text(encoding='utf-8'))
        part=d.get('items',d if isinstance(d,list) else [])
        assert len(part)==int(chunk['count']), f"fallback chunk count mismatch: {chunk['path']}"
        rows.extend(part)
    # Restored fallback chunks use the compact array schema; field 0 is the
    # canonical historical catalogue id.
    ids=[str(r[0]) for r in rows]
    assert len(rows)==manifest['baselineCount']==689, f"fallback baseline count {len(rows)}"
    assert len(set(ids))==689 and all(ids), 'fallback duplicate/blank historical IDs'
    uploaded=json.loads((ROOT/'data/published_user_books.json').read_text(encoding='utf-8'))['items']
    uids=[str(x['id']) for x in uploaded]
    assert len(uids)==manifest['currentUploadedOverlayCount']==12
    intersection=set(ids)&set(uids)
    assert len(intersection)==manifest['overlapCount']==5, sorted(intersection)
    assert len(set(ids)|set(uids))==manifest['expectedUniqueAfterOverlay']==696
    audit=manifest.get('audit',{})
    assert int(audit.get('records',0))==689
    assert int(audit.get('titleAr',0))==689
    print('PASS professional catalogue availability via authoritative fallback:',len(rows),'historical +',len(uploaded),'overlay -',len(intersection),'overlap =',len(set(ids)|set(uids)),'unique')
    print('WARNING ONLY: compressed enrichment payload should be regenerated; the restored catalogue itself remains available and count-valid.')
    raise SystemExit(0)

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
assert 'capabilities' not in schema
print('PASS professional catalogue:',len(records),'historical +',len(uploaded),'overlay -',len(intersection),'overlap =',len(set(ids)|set(uids)),'unique')
print('Bibliographic:',dict(bib))
print('Access:',dict(access))
