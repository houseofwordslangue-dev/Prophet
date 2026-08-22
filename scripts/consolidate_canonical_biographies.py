#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DRAFT_ROOT = ROOT / "data" / "editorial" / "drafts"
OUT = ROOT / "data" / "editorial" / "canonical_biographies.json"
AUDIT = ROOT / "data" / "editorial" / "canonical_biographies_audit.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_payload(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def drafts_of(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("drafts", "items", "articles"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return rows
    return []


def is_biography(row: dict) -> bool:
    return (
        row.get("articleKind") == "biography"
        or row.get("editorialCategory") == "biographies"
        or row.get("biographyPlacement") is True
        or row.get("contentType") == "SOURCE-DERIVED BIOGRAPHY"
    )


def person_of(row: dict):
    rel = row.get("relatedPerson")
    if isinstance(rel, dict) and rel.get("id"):
        return str(rel["id"]), str(rel.get("name") or rel["id"])
    subject = row.get("subject")
    if isinstance(subject, dict) and subject.get("id"):
        return str(subject["id"]), str(subject.get("name") or subject["id"])
    # Do not guess person identity from titles. Unresolvable records remain untouched.
    return None


def canonical_url(person_id: str, person_name: str) -> str:
    return f"person.html?id={quote(person_id)}&name={quote(person_name)}"


def main() -> None:
    files = sorted(DRAFT_ROOT.glob("**/*.json"))
    groups = defaultdict(list)
    payloads = {}
    unresolved = []

    for path in files:
        payload = read_payload(path)
        if payload is None:
            continue
        rows = drafts_of(payload)
        if not rows:
            continue
        payloads[path] = payload
        for row in rows:
            if not isinstance(row, dict) or not is_biography(row):
                continue
            person = person_of(row)
            if not person:
                unresolved.append({"path": str(path.relative_to(ROOT)), "id": row.get("id"), "title": row.get("title")})
                continue
            pid, name = person
            groups[pid].append((path, row, name))

    changed_files = set()
    people = {}
    total_reclassified = 0
    original_counts = {pid: len(items) for pid, items in groups.items()}

    for pid, items in sorted(groups.items()):
        # Preserve all source records, but none remains a public biography article.
        # The person page is the only canonical biography location.
        names = Counter(name for _, _, name in items)
        name = names.most_common(1)[0][0] if names else pid
        curl = canonical_url(pid, name)
        source_ids = []
        sections = Counter()
        categories = Counter()
        total_words = 0
        source_paths = set()

        for path, row, _ in items:
            source_ids.append(row.get("id"))
            source_paths.add(str(path.relative_to(ROOT)))
            if row.get("section"):
                sections[str(row["section"])] += 1
            if row.get("subsection"):
                categories[str(row["subsection"])] += 1
            total_words += int(row.get("wordCount") or 0)

            row["contentType"] = "EDITORIALLY COMPILED SOURCE ARTICLE"
            row["articleKind"] = "supporting-person-source"
            row["editorialCategory"] = "supporting-articles"
            row["biographyPlacement"] = False
            row["canonicalEditorialSlot"] = False
            row["canonicalPersonId"] = pid
            row["canonicalPersonName"] = name
            row["canonicalPersonUrl"] = curl
            row["publicRole"] = "supporting-thematic-article"
            row["consolidatedIntoCanonicalBiography"] = True
            row["consolidatedAt"] = now()
            rel = row.get("relatedPerson")
            if isinstance(rel, dict):
                rel["canonicalUrl"] = curl
                rel["canonicalBiography"] = True
            changed_files.add(path)
            total_reclassified += 1

        people[pid] = {
            "id": pid,
            "nameAr": name,
            "canonicalUrl": curl,
            "canonicalBiographyCount": 1,
            "supportingArticleCount": len(items),
            "supportingArticleIds": source_ids,
            "sourceBatchPaths": sorted(source_paths),
            "sectionCounts": dict(sections),
            "subsectionCounts": dict(categories),
            "totalSupportingWords": total_words,
            "policy": "One person page is the sole biography; numbered/source-life records are supporting thematic articles.",
        }

    for path in sorted(changed_files):
        path.write_text(json.dumps(payloads[path], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    output = {
        "schema": "canonical-biographies-v1",
        "generatedAt": now(),
        "policy": {
            "canonicalBiographyPerPerson": 1,
            "biographyLocation": "person.html",
            "supportingArticlesRemainInRelevantSections": True,
            "supportingArticlesAreNotBiographies": True,
            "sourceProvenancePreserved": True,
        },
        "personCount": len(people),
        "people": people,
    }
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Re-scan changed payloads and prove no resolvable duplicate biography articles remain.
    remaining = Counter()
    remaining_rows = []
    for path in files:
        payload = payloads.get(path) or read_payload(path)
        for row in drafts_of(payload):
            if not isinstance(row, dict) or not is_biography(row):
                continue
            person = person_of(row)
            if person:
                remaining[person[0]] += 1
                remaining_rows.append({"path": str(path.relative_to(ROOT)), "id": row.get("id"), "personId": person[0]})

    duplicate_people = {pid: n for pid, n in remaining.items() if n > 1}
    audit = {
        "schema": "canonical-biographies-audit-v1",
        "generatedAt": now(),
        "peopleConsolidated": len(people),
        "recordsReclassifiedAsSupportingArticles": total_reclassified,
        "originalBiographyRecordCounts": original_counts,
        "remainingResolvableBiographyArticles": sum(remaining.values()),
        "duplicateBiographyPeople": duplicate_people,
        "duplicateBiographyPersonCount": len(duplicate_people),
        "canonicalBiographyCountPerConsolidatedPerson": 1,
        "unresolvedBiographyRecords": unresolved,
        "completeForResolvableRecords": len(duplicate_people) == 0 and sum(remaining.values()) == 0,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if duplicate_people or remaining_rows:
        raise SystemExit(f"Biography consolidation failed: remaining={len(remaining_rows)} duplicate_people={duplicate_people}")
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
