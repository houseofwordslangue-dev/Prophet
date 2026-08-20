#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
path = ROOT / 'data/catalogue/disputed_attributions.json'
data = json.loads(path.read_text(encoding='utf-8'))
policy = data['policy']
records = data['records']

assert policy['defaultPublication'] == 'ALLOW'
assert policy['suppressOnDispute'] is False
assert policy['explicitUserOverrideRequiredToSuppress'] is True

expected_ids = {
    'life-seerah-070',
    'character-shamail-040',
    'quran-meaning-067',
    'teachings-wisdom-042',
    'life-seerah-071',
    'site-source-jilani-fath-rabbani',
}
ids = [str(r['id']) for r in records]
assert len(ids) == len(set(ids)) == 6
assert set(ids) == expected_ids, (set(ids), expected_ids)

for r in records:
    assert str(r.get('authorAr', '')).strip(), f"{r['id']}: author display missing"
    assert r.get('attributionStatus') in {'disputed-multiple', 'traditional-attribution'}
    assert r.get('publicationStatus') in {'published-disputed-attribution', 'published-attributed'}
    assert str(r.get('publicationLabelAr', '')).strip()
    assert str(r.get('attributionNoteAr', '')).strip()
    assert isinstance(r.get('authorVariants'), list) and r['authorVariants'], f"{r['id']}: variants missing"
    assert isinstance(r.get('evidence'), list) and r['evidence'], f"{r['id']}: evidence missing"
    assert all(str(e.get('url', '')).startswith('https://') for e in r['evidence'])
    assert 'capabilities' not in r, f"{r['id']}: attribution policy must not grant media capabilities"

# The manifest must activate this registry and keep the underlying 689/696 integrity target.
manifest = json.loads((ROOT / 'data/catalogue/manifest.json').read_text(encoding='utf-8'))
assert manifest.get('attributionPolicy') == 'data/catalogue/disputed_attributions.json'
assert manifest['baselineCount'] == 689
assert manifest['expectedUniqueAfterOverlay'] == 696
assert manifest['audit']['disputedAttributionRecordsPublished'] == 6

loader = (ROOT / 'assets/catalogue-restore.js').read_text(encoding='utf-8')
assert 'applyAttributionOverrides' in loader
assert 'disputedAttributionPublished:true' in loader
assert 'capabilities:item.capabilities' in loader

print('PASS disputed attribution publication:', len(records), 'records; suppression-on-dispute disabled')
