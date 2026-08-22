#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import concurrent.futures
import json
import time
from pathlib import Path

import source_first_fulltext_resolver as base

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / 'private/resource_extraction_queue.json'
OVERRIDES = ROOT / 'private/native_source_overrides.json'
PROVIDERS = ROOT / 'data/provider_access.json'
REPORT = ROOT / 'data/editorial/unresolved_content_force_resolution.json'
CAT_DIR = ROOT / 'data/catalogue'
PUBLIC = ROOT / 'data/public_catalog_all.generated.json'
MAX_WORKERS = 8


def load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def save(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def full_catalogue_metadata():
    rows = {}
    public = load(PUBLIC, {'items': []})
    for x in public.get('items', []):
        wid = str(x.get('id') or x.get('workId') or '')
        if wid:
            rows[wid] = {
                'id': wid,
                'titleAr': x.get('titleAr') or x.get('title') or '',
                'titleEn': x.get('titleEn') or '',
                'authorAr': x.get('authorAr') or x.get('author') or '',
                'authorEn': x.get('authorEn') or '',
                'sources': list(x.get('sources') or []),
            }
    for p in sorted(CAT_DIR.glob('chunk-*.json')):
        chunk = load(p, {'items': []})
        for r in chunk.get('items', []):
            if not isinstance(r, list) or not r:
                continue
            wid = str(r[0] or '')
            if not wid:
                continue
            old = rows.get(wid, {'id': wid, 'sources': []})
            # Compact chunk schema used by this repository:
            # id, entryNo, category, titleAr, titleRomanized/En, authorAr, authorRomanized/En, ... sourceUrl at 12.
            old['titleAr'] = old.get('titleAr') or (str(r[3]) if len(r) > 3 and r[3] else '')
            old['titleEn'] = old.get('titleEn') or (str(r[4]) if len(r) > 4 and r[4] else '')
            old['authorAr'] = old.get('authorAr') or (str(r[5]) if len(r) > 5 and r[5] else '')
            old['authorEn'] = old.get('authorEn') or (str(r[6]) if len(r) > 6 and r[6] else '')
            if len(r) > 12 and r[12]:
                old.setdefault('sources', []).append(str(r[12]))
            rows[wid] = old
    return rows


def provider_map():
    out = {}
    for x in load(PROVIDERS, {'items': []}).get('items', []):
        wid = str(x.get('catalogueId') or x.get('id') or '')
        if wid and x.get('providerUrl'):
            out.setdefault(wid, []).append(x)
    return out


def variants(meta, queue_row):
    vals = [
        queue_row.get('title'),
        meta.get('titleAr'),
        meta.get('titleEn'),
    ]
    result = []
    seen = set()
    for v in vals:
        s = str(v or '').strip()
        n = base.norm(s)
        if s and n and n not in seen:
            seen.add(n)
            result.append(s)
    return result


def authors(meta, queue_row):
    vals = [queue_row.get('author'), meta.get('authorAr'), meta.get('authorEn')]
    result = []
    seen = set()
    for v in vals:
        s = str(v or '').strip()
        n = base.norm(s)
        if s and n and n not in seen:
            seen.add(n)
            result.append(s)
    return result


def best_candidate(candidates):
    candidates = base.dedup(candidates)
    if not candidates:
        return None
    candidates.sort(key=base.rank)
    return candidates[0]


def resolve_one(queue_row, meta, providers):
    wid = str(queue_row.get('id') or '')
    titles = variants(meta, queue_row)
    auths = authors(meta, queue_row)
    candidates = []
    discovery = []

    # 1) Existing explicitly known URLs, including all resource-list provider URLs.
    for u in list(meta.get('sources') or []):
        if not u:
            continue
        discovery.append({'method': 'catalog-source', 'url': u})
        if 'archive.org' in u:
            candidates += base.archive_files(u)
        elif 'gutenberg.org' in u:
            candidates += base.gutenberg(u)
        else:
            f = base.fmt(u)
            if f:
                candidates.append({'format': f, 'url': u, 'name': u.rsplit('/', 1)[-1], 'source': 'catalog-direct', 'textOrigin': 'PDF_TEXT_OR_SCAN' if f == 'pdf' else 'VERIFIED_TEXT', 'verifiedAccessible': True})

    for p in providers:
        u = str(p.get('providerUrl') or '')
        if not u:
            continue
        discovery.append({'method': 'provider-access', 'url': u})
        if 'archive.org' in u:
            # Restricted Archive records correctly return no extraction files.
            # They stay bookstore-visible, but are not falsely counted as extraction-ready.
            candidates += base.archive_files(u)

    chosen = best_candidate(candidates)
    if chosen:
        return {'id': wid, 'resolved': True, 'candidate': chosen, 'discovery': discovery, 'matchedTitle': titles[0] if titles else ''}

    # 2) Native text search first.
    for t in titles:
        ws = base.wikisource(t)
        if ws:
            chosen = best_candidate(ws)
            if chosen:
                return {'id': wid, 'resolved': True, 'candidate': chosen, 'discovery': discovery + [{'method': 'wikisource', 'query': t}], 'matchedTitle': t}

    # 3) Archive discovery. Discovery is broad; acceptance remains inside base.archive_search/title_score.
    for t in titles:
        for a in auths[:2] or ['']:
            ar = base.archive_search(t, a)
            if ar:
                chosen = best_candidate(ar)
                if chosen:
                    return {'id': wid, 'resolved': True, 'candidate': chosen, 'discovery': discovery + [{'method': 'archive-search', 'title': t, 'author': a}], 'matchedTitle': t}

    return {'id': wid, 'resolved': False, 'candidate': None, 'discovery': discovery, 'matchedTitle': titles[0] if titles else ''}


def override_from(result, meta):
    c = result['candidate']
    return {
        'workId': result['id'],
        'titleAr': meta.get('titleAr') or result.get('matchedTitle') or '',
        'authorAr': meta.get('authorAr') or '',
        'verifiedSource': c.get('url'),
        'verifiedFormat': c.get('format'),
        'sourceRole': 'verified-extraction-source',
        'textOrigin': c.get('textOrigin'),
        'sourceRepository': c.get('source'),
        'redistributionApproved': False,
        'note': 'Automatically discovered by force_resolve_unresolved_content.py; source identity accepted only through the repository strict title-matching resolver. Redistribution rights are not inferred from discoverability.',
    }


def main():
    # Refresh authoritative queue before working it.
    base.main()
    queue_doc = load(QUEUE, {'items': []})
    queue = list(queue_doc.get('items') or [])
    metadata = full_catalogue_metadata()
    providers = provider_map()

    before = len(queue)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {
            ex.submit(resolve_one, row, metadata.get(str(row.get('id') or ''), {}), providers.get(str(row.get('id') or ''), [])): row
            for row in queue
        }
        for fut in concurrent.futures.as_completed(futs):
            row = futs[fut]
            try:
                results.append(fut.result())
            except Exception as exc:
                results.append({'id': str(row.get('id') or ''), 'resolved': False, 'candidate': None, 'error': str(exc)[:500]})

    current = load(OVERRIDES, {'schema': 'native-source-overrides-v2', 'governedBy': 'MASTER-OVERRIDING-SITE-INSTRUCTION.md', 'items': []})
    by_id = {str(x.get('workId') or x.get('catalogueId') or ''): x for x in current.get('items', []) if isinstance(x, dict)}
    added = 0
    for r in results:
        if not r.get('resolved'):
            continue
        wid = str(r.get('id') or '')
        meta = metadata.get(wid, {})
        new = override_from(r, meta)
        old = by_id.get(wid)
        # Preserve a human/curated override unless the new one provides a verified source where none existed.
        if old and old.get('verifiedSource'):
            continue
        by_id[wid] = {**(old or {}), **new}
        added += 1

    save(OVERRIDES, {
        'schema': 'native-source-overrides-v2',
        'governedBy': 'MASTER-OVERRIDING-SITE-INSTRUCTION.md',
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'items': list(by_id.values()),
    })

    # Rebuild the authoritative resolution/queue after writing verified overrides.
    base.main()
    after_doc = load(QUEUE, {'items': []})
    after = len(after_doc.get('items') or [])

    report = {
        'schema': 'unresolved-content-force-resolution-v1',
        'governedBy': 'MASTER-OVERRIDING-SITE-INSTRUCTION.md',
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'beforeUnresolved': before,
        'verifiedOverridesAdded': added,
        'afterUnresolved': after,
        'resolvedThisPass': max(0, before - after),
        'allResolved': after == 0,
        'policy': 'No unresolved record is silently substituted. Restricted provider access remains bookstore-visible but does not become extraction-ready unless a usable verified source exists.',
        'results': results,
    }
    save(REPORT, report)
    print(json.dumps({k: report[k] for k in ('beforeUnresolved', 'verifiedOverridesAdded', 'afterUnresolved', 'resolvedThisPass', 'allResolved')}, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
