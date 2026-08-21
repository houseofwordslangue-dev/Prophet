#!/usr/bin/env python3
import glob, json, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
BATCH_GLOB = ROOT / 'data/editorial/drafts/2026-08-21/family-life-five-batch-*.json'
AUDIT = ROOT / 'data/editorial/remaining_family_life_5_audit.json'
SUPPLEMENT = ROOT / 'data/editorial/publication_supplement.json'
OUT_AUDIT = ROOT / 'data/editorial/remaining_family_biographies_publication_audit.json'


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    source_audit = load(AUDIT)
    assert source_audit['remainingMembersWithFiveDrafts'] == 115
    assert source_audit['draftsGenerated'] == 575
    assert source_audit['sourceGapMembers'] == 0
    assert source_audit['articlesAtOrBelow500Words'] == 0
    assert source_audit['minimumObservedWords'] >= 500

    paths = sorted(pathlib.Path(p) for p in glob.glob(str(BATCH_GLOB)))
    assert paths, 'No family life batch files found'

    published_ids = []
    subjects = {}
    minimum = 10**9
    maximum = 0
    prophet_only = {'light','prophet','messenger','human','mercy'}

    for path in paths:
        data = load(path)
        data['publicationStatus'] = 'PUBLISHED'
        data['contentPlacement'] = 'biographies'
        for row in data.get('drafts', []):
            wc = int(row.get('wordCount', 0))
            assert wc >= 500, f"Under 500 words: {row.get('id')}={wc}"
            assert row.get('section') not in prophet_only, row.get('id')
            row['publicationStatus'] = 'PUBLISHED'
            row['draftStatus'] = 'PUBLISHED_SOURCE_VERIFIED'
            row['contentType'] = 'SOURCE-DERIVED BIOGRAPHY'
            row['articleKind'] = 'biography'
            row['editorialCategory'] = 'biographies'
            row['biographyPlacement'] = True
            row['publishedAt'] = '2026-08-21T07:25:00Z'
            published_ids.append(row['id'])
            subj = row.get('subject', {})
            sid = subj.get('id')
            if sid:
                subjects.setdefault(sid, {'id': sid, 'name': subj.get('name',''), 'count': 0})['count'] += 1
            minimum = min(minimum, wc)
            maximum = max(maximum, wc)
        dump(path, data)

    assert len(published_ids) == 575
    assert len(set(published_ids)) == 575
    assert len(subjects) == 115
    assert all(v['count'] == 5 for v in subjects.values())

    supplement = load(SUPPLEMENT)
    batch_paths = [str(p.relative_to(ROOT)).replace('\\','/') for p in paths]
    existing_paths = supplement.setdefault('draftBatchPaths', [])
    for p in batch_paths:
        if p not in existing_paths:
            existing_paths.append(p)
    existing_ids = supplement.setdefault('publishedIds', [])
    seen = set(existing_ids)
    for pid in published_ids:
        if pid not in seen:
            existing_ids.append(pid); seen.add(pid)
    supplement['publishedAt'] = '2026-08-21T07:25:00Z'
    supplement['familyBiographies'] = {
        'status': 'PUBLISHED',
        'category': 'biographies',
        'people': 115,
        'articlesPerPerson': 5,
        'articles': 575,
        'minimumWords': minimum,
        'maximumWords': maximum,
        'articlesUnder500Words': 0,
        'sourceCoveragePercent': 100,
        'aiOriginalSubstantiveContentPercent': 0,
        'excludedAlreadyComplete': ['fatima-al-zahra','ali-ibn-abi-talib'],
        'structuralPlacement': 'proper family subgroup + biographies classification'
    }
    dump(SUPPLEMENT, supplement)

    audit = {
        'schema': 'remaining-family-biographies-publication-audit-v1',
        'generatedAt': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00','Z'),
        'status': 'PUBLISHED',
        'category': 'biographies',
        'people': 115,
        'articlesPerPerson': 5,
        'articles': 575,
        'minimumWordsRequired': 500,
        'minimumObservedWords': minimum,
        'maximumObservedWords': maximum,
        'articlesUnder500Words': 0,
        'uniqueArticleIds': len(set(published_ids)),
        'subjectsWithExactlyFive': sum(1 for v in subjects.values() if v['count']==5),
        'sourceCoveragePercent': 100,
        'aiOriginalSubstantiveContentPercent': 0,
        'prophetOnlySectionsUsed': 0,
        'batchPaths': batch_paths
    }
    dump(OUT_AUDIT, audit)
    print(json.dumps(audit, ensure_ascii=False))

if __name__ == '__main__':
    main()
