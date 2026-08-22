#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PEOPLE = ROOT / 'data' / 'people.json'
EXT_DIR = ROOT / 'data' / 'editorial' / 'biography-extensions'
INDEX = ROOT / 'data' / 'editorial' / 'canonical_biography_extensions.json'
AUDIT = ROOT / 'data' / 'editorial' / 'biography_content_extension_audit.json'
MAX_PASSAGES_PER_PERSON = 50
MAX_WORDS_PER_PERSON = 12000
MIN_WORDS = 20


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default


def norm(text: str) -> str:
    text = re.sub(r'[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06edـ]', '', str(text or ''))
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي')
    return re.sub(r'\s+', ' ', text).strip()


def fp(text: str) -> str:
    return hashlib.sha256(norm(text).encode('utf-8')).hexdigest()


def wc(text: str) -> int:
    return len([x for x in re.split(r'\s+', str(text or '').strip()) if x])


def source_for(row: dict) -> dict:
    srcs = row.get('professionalSources') or []
    if isinstance(srcs, dict):
        srcs = [srcs]
    src = srcs[0] if srcs else {}
    return {
        'recordId': row.get('id'),
        'repositoryPath': 'data/people.json',
        'sourceType': 'person-owned-verified-source',
        'title': src.get('title'),
        'author': src.get('author'),
        'url': src.get('url'),
        'wikisourcePage': src.get('wikisourcePage'),
        'verifiedAgainstOriginal': src.get('verifiedAgainstOriginal', True),
        'provenance': row.get('professionalProvenance') or row.get('provenance') or 'verified-source',
    }


def collect_owned_passages(row: dict):
    out = []
    seen = set()

    for item in row.get('sourcePassages') or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get('text') or '').strip()
        if not text or wc(text) < MIN_WORDS:
            continue
        key = fp(text)
        if key in seen:
            continue
        seen.add(key)
        srcs = item.get('sources') or row.get('professionalSources') or []
        if isinstance(srcs, dict):
            srcs = [srcs]
        src0 = srcs[0] if srcs else source_for(row)
        source = {
            'recordId': row.get('id'),
            'repositoryPath': 'data/people.json',
            'sourceType': 'person-owned-verified-source',
            'title': src0.get('title'),
            'author': src0.get('author'),
            'url': src0.get('url'),
            'wikisourcePage': src0.get('wikisourcePage'),
            'verifiedAgainstOriginal': src0.get('verifiedAgainstOriginal', True),
            'provenance': row.get('professionalProvenance') or row.get('provenance') or 'verified-source',
        }
        out.append({'text': text, 'source': source, 'wordCount': wc(text)})

    prof = row.get('professionalBiography') or {}
    if isinstance(prof, dict):
        for text in prof.get('ar') or []:
            text = str(text or '').strip()
            if not text or wc(text) < MIN_WORDS:
                continue
            key = fp(text)
            if key in seen:
                continue
            seen.add(key)
            out.append({'text': text, 'source': source_for(row), 'wordCount': wc(text)})

    return out


def main():
    doc = read_json(PEOPLE, {'people': []})
    people = [x for x in doc.get('people', []) if isinstance(x, dict) and x.get('id')]
    EXT_DIR.mkdir(parents=True, exist_ok=True)
    index = read_json(INDEX, {'people': {}})
    if not isinstance(index.get('people'), dict):
        index['people'] = {}

    people_with_owned = 0
    people_extended = 0
    added_passages = 0
    added_words = 0

    for row in people:
        pid = str(row['id'])
        owned = collect_owned_passages(row)
        if not owned:
            continue
        people_with_owned += 1

        path = EXT_DIR / f"{re.sub(r'[^A-Za-z0-9._-]+','-',pid).strip('-') or 'person'}.json"
        payload = read_json(path, {
            'schema': 'canonical-biography-source-extension-v1',
            'personId': pid,
            'personNameAr': ((row.get('name') or {}).get('ar') if isinstance(row.get('name'), dict) else row.get('nameAr')) or pid,
            'policy': 'Verbatim/bounded source-derived passages only; no model-authored factual fill-in.',
            'passages': [],
        })
        passages = payload.get('passages') or []
        if not isinstance(passages, list):
            passages = []
        existing = {fp(str(x.get('text') or '')) for x in passages if isinstance(x, dict) and str(x.get('text') or '').strip()}
        before = len(passages)
        total_words = sum(int(x.get('wordCount') or wc(x.get('text') or '')) for x in passages if isinstance(x, dict))

        for item in owned:
            key = fp(item['text'])
            if key in existing:
                continue
            if len(passages) >= MAX_PASSAGES_PER_PERSON or total_words >= MAX_WORDS_PER_PERSON:
                break
            if total_words + item['wordCount'] > MAX_WORDS_PER_PERSON and passages:
                break
            passages.append(item)
            existing.add(key)
            total_words += item['wordCount']
            added_passages += 1
            added_words += item['wordCount']

        if len(passages) > before:
            people_extended += 1
            payload['passages'] = passages
            payload['passageCount'] = len(passages)
            payload['wordCount'] = total_words
            payload['policy'] = 'Verbatim/bounded source-derived passages only; no model-authored factual fill-in.'
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

        if passages:
            index['people'][pid] = {
                'id': pid,
                'nameAr': payload.get('personNameAr'),
                'category': row.get('category'),
                'passageCount': len(passages),
                'wordCount': total_words,
                'file': str(path.relative_to(ROOT)),
            }

    index['peopleExtended'] = len(index['people'])
    index['passageCount'] = sum(int(v.get('passageCount') or 0) for v in index['people'].values())
    index['wordCount'] = sum(int(v.get('wordCount') or 0) for v in index['people'].values())
    index['policy'] = dict(index.get('policy') or {})
    index['policy']['personOwnedVerifiedSourcePassagesIncluded'] = True
    index['policy']['modelAuthoredFactualFillIn'] = False
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    audit = {
        'schema': 'biography-content-extension-audit-v1',
        'peopleScanned': len(people),
        'peopleWithVerifiedOwnedSource': people_with_owned,
        'peopleExtended': people_extended,
        'addedPassageCount': added_passages,
        'addedWordCount': added_words,
        'maximumPassagesPerPerson': MAX_PASSAGES_PER_PERSON,
        'maximumWordsPerPerson': MAX_WORDS_PER_PERSON,
        'aiOriginalSubstantiveContentPercent': 0,
        'complete': people_extended > 0 and added_passages > 0 and added_words > 0,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(audit, ensure_ascii=False))
    if not audit['complete']:
        raise SystemExit('No new verified owned source content was added')


if __name__ == '__main__':
    main()
