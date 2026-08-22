#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = ROOT / 'data' / 'public_catalog_all.generated.json'
RES = ROOT / 'private' / 'source_first_resolution.json'
OUT = ROOT / 'data' / 'editorial' / 'resource_extraction_readiness_gate.json'
ALLOW = ROOT / 'data' / 'editorial' / 'generation_resource_allowlist.json'


def load(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def main():
    cat = load(CAT, {'items': []})
    res = load(RES, {'items': []})
    catalog = [x for x in cat.get('items', []) if isinstance(x, dict)]
    rows = [x for x in res.get('items', []) if isinstance(x, dict)]
    by_id = {str(x.get('id') or ''): x for x in rows}
    blockers = []
    eligible = []
    eligible_rows = []

    for item in catalog:
        wid = str(item.get('id') or '')
        r = by_id.get(wid)
        if r and r.get('extractionReady') is True and r.get('preferred'):
            eligible.append(wid)
            eligible_rows.append({
                'id': wid,
                'title': item.get('title'),
                'author': item.get('author'),
                'state': r.get('state'),
                'preferred': r.get('preferred'),
                'textOrigin': r.get('textOrigin'),
            })
            continue
        blockers.append({
            'id': wid,
            'title': item.get('title'),
            'author': item.get('author'),
            'catalogAccess': item.get('access'),
            'state': 'HARD_BLOCKED',
            'resolverState': (r or {}).get('state') or 'MISSING_FROM_RESOLUTION',
            'reason': ((r or {}).get('reason') or 'No verified extraction path is currently materialized.'),
            'generationAllowed': False,
            'retryOnNewSource': True,
        })

    total = len(catalog)
    now = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    out = {
        'schema': 'resource-extraction-readiness-gate-v2',
        'governedBy': 'MASTER-OVERRIDING-SITE-INSTRUCTION.md',
        'generatedAt': now,
        'catalogResources': total,
        'extractionReady': len(eligible),
        'blocked': len(blockers),
        'coveragePercent': round(100 * len(eligible) / total, 2) if total else 100.0,
        'allResourcesExtractionReady': len(blockers) == 0,
        'generationEligibleIds': eligible,
        'hardBlockedIds': [x['id'] for x in blockers],
        'blockers': blockers,
        'policy': 'Generation may use only generationEligibleIds. A resource without a verified extraction path is HARD_BLOCKED and may not be silently substituted, summarized, synthesized, or treated as available.',
    }
    allow = {
        'schema': 'generation-resource-allowlist-v1',
        'governedBy': 'MASTER-OVERRIDING-SITE-INSTRUCTION.md',
        'generatedAt': now,
        'eligibleCount': len(eligible),
        'blockedCount': len(blockers),
        'allResourcesExtractionReady': len(blockers) == 0,
        'generationEligibleIds': eligible,
        'hardBlockedIds': [x['id'] for x in blockers],
        'eligibleResources': eligible_rows,
        'rule': 'Downstream extraction and SOURCE_GROUNDED_SYNTHESIS must select source resources only from generationEligibleIds.',
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    ALLOW.write_text(json.dumps(allow, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: out[k] for k in ('catalogResources','extractionReady','blocked','coveragePercent','allResourcesExtractionReady')}, ensure_ascii=False))
    return 0 if out['allResourcesExtractionReady'] else 2


if __name__ == '__main__':
    sys.exit(main())
