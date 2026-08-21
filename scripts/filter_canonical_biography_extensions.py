#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROOT = ROOT / 'data/editorial/drafts'
INDEX_PATH = ROOT / 'data/editorial/canonical_biography_extensions.json'
AUDIT_PATH = ROOT / 'data/editorial/global_biography_placement_audit.json'


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def rows_of(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ('drafts', 'items', 'articles', 'records'):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def explicit_person_id(row: dict):
    for key in ('relatedPerson', 'subject'):
        obj = row.get(key)
        if isinstance(obj, dict) and obj.get('id'):
            return str(obj['id'])
    for key in ('canonicalPersonId', 'subjectPerson', 'personId'):
        if row.get(key):
            return str(row[key])
    return None


def main():
    index = read_json(INDEX_PATH, {}) or {}
    people = index.get('people') or {}

    record_owner = {}
    for path in sorted(DRAFT_ROOT.glob('**/*.json')):
        payload = read_json(path, {})
        rel = str(path.relative_to(ROOT))
        for row in rows_of(payload):
            if not isinstance(row, dict) or not row.get('id'):
                continue
            owner = explicit_person_id(row)
            if owner:
                record_owner[(rel, str(row['id']))] = owner

    filtered = []
    kept_passages = 0
    kept_words = 0
    surviving_people = {}

    for pid, meta in sorted(people.items()):
        path = ROOT / str(meta.get('file') or '')
        payload = read_json(path, {}) or {}
        rows = payload.get('passages') or []
        keep = []
        for item in rows:
            src = item.get('source') if isinstance(item, dict) else None
            src = src if isinstance(src, dict) else {}
            key = (str(src.get('repositoryPath') or ''), str(src.get('recordId') or ''))
            owner = record_owner.get(key)
            if owner != pid:
                filtered.append({
                    'personId': pid,
                    'repositoryPath': key[0],
                    'recordId': key[1],
                    'explicitOwner': owner,
                    'reason': 'source-record-not-explicitly-owned-by-target-person',
                })
                continue
            keep.append(item)

        if not keep:
            if path.exists():
                path.unlink()
            continue

        payload['policy'] = 'Only passages from source records explicitly linked to this exact person; no incidental name-match enrichment.'
        payload['passageCount'] = len(keep)
        payload['passages'] = keep
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        words = sum(int(x.get('wordCount') or len(str(x.get('text') or '').split())) for x in keep)
        kept_passages += len(keep)
        kept_words += words
        new_meta = dict(meta)
        new_meta['passageCount'] = len(keep)
        new_meta['wordCount'] = words
        surviving_people[pid] = new_meta

    index['policy'] = {
        'onePersonOneCanonicalBiographyPage': True,
        'extensionsRenderOnlyOnCanonicalPersonPage': True,
        'sourceDerivedOnly': True,
        'explicitPersonOwnershipRequired': True,
        'incidentalNameMatchesRejected': True,
        'noGeneratedFactualFillIn': True,
        'thematicArticlesRemainInSections': True,
    }
    index['peopleExtended'] = len(surviving_people)
    index['passageCount'] = kept_passages
    index['wordCount'] = kept_words
    index['people'] = surviving_people
    INDEX_PATH.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    audit = read_json(AUDIT_PATH, {}) or {}
    audit['biographyExtensionOwnershipPolicy'] = 'explicit-person-link-only'
    audit['incidentalNameMatchPassagesRejected'] = len(filtered)
    audit['rejectedExtensionPassages'] = filtered[:500]
    audit['peopleExtendedAfterOwnershipFilter'] = len(surviving_people)
    audit['extensionPassagesAfterOwnershipFilter'] = kept_passages
    audit['extensionWordsAfterOwnershipFilter'] = kept_words
    audit['strictExtensionOwnershipComplete'] = True
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print(json.dumps({
        'peopleExtended': len(surviving_people),
        'passages': kept_passages,
        'words': kept_words,
        'incidentalRejected': len(filtered),
    }, ensure_ascii=False))

    if not surviving_people or not kept_passages:
        raise SystemExit('Strict ownership filter removed every biography extension')


if __name__ == '__main__':
    main()
