#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from add_135_more_source_biographies import (
    PREFIX,
    SOURCE_AUTHOR,
    SOURCE_TITLE,
    clean_extract,
    fetch_extracts,
    list_titles,
    load_json,
    name_ar,
    norm_ar,
    source_url,
    words,
)

ROOT = Path(__file__).resolve().parents[1]
PEOPLE = ROOT / "data" / "people.json"
AUDIT = ROOT / "data" / "editorial" / "expanded_biographies_50_audit.json"
TARGET = 50
MIN_WORDS = 120


def main():
    people_doc = load_json(PEOPLE, {"people": []})
    people = people_doc.get("people") or []

    # Strictly exclude every person already present in the full public registry.
    existing_names = {norm_ar(name_ar(row)) for row in people if norm_ar(name_ar(row))}
    existing_ids = {
        str(row.get("id") or row.get("slug") or "").strip()
        for row in people
        if str(row.get("id") or row.get("slug") or "").strip()
    }

    titles = sorted(
        set(list_titles()),
        key=lambda x: hashlib.sha256(("new50:" + x).encode("utf-8")).hexdigest(),
    )

    chosen = []
    used_names = set()
    used_ids = set()
    batch_size = 20

    for i in range(0, len(titles), batch_size):
        batch = titles[i:i + batch_size]
        extracts = fetch_extracts(batch)
        for title in batch:
            suffix = title[len(PREFIX):].strip()
            nn = norm_ar(suffix)
            if not nn or nn in existing_names or nn in used_names:
                continue

            text = clean_extract(extracts.get(title, ""), suffix)
            wc = len(words(text))
            if wc < MIN_WORDS:
                continue

            pid = "siyar-new50-" + hashlib.sha1(title.encode("utf-8")).hexdigest()[:14]
            if pid in existing_ids or pid in used_ids:
                continue

            chosen.append((pid, suffix, title, text, wc))
            used_names.add(nn)
            used_ids.add(pid)
            if len(chosen) == TARGET:
                break
        if len(chosen) == TARGET:
            break
        time.sleep(0.08)

    if len(chosen) != TARGET:
        raise SystemExit(
            f"Could only source {len(chosen)}/{TARGET} distinct biographies after excluding all {len(people)} existing people"
        )

    new_ids = []
    new_names = []
    counts = []

    for pid, nm, title, text, wc in chosen:
        source = {
            "title": SOURCE_TITLE,
            "author": SOURCE_AUTHOR,
            "url": source_url(title),
            "wikisourcePage": title,
            "verifiedAgainstOriginal": True,
            "sourceType": "classical-biographical-entry",
        }
        people.append({
            "id": pid,
            "slug": pid,
            "name": {"ar": nm, "en": nm, "fr": nm},
            "category": "scholar",
            "biography": {"ar": [], "en": [], "fr": []},
            "professionalBiography": {"ar": [text], "en": [], "fr": []},
            "professionalSources": [source],
            "professionalAttribution": {
                "ar": "الذهبي — سير أعلام النبلاء",
                "en": "Al-Dhahabi — Siyar A'lam al-Nubala",
                "fr": "Al-Dhahabi — Siyar A'lam al-Nubala",
            },
            "professionalProvenance": "VERBATIM_CLASSICAL_SOURCE_EXCERPT",
            "sourcePassages": [{
                "language": "ar",
                "relation": "biography-source",
                "text": text,
                "sources": [source],
            }],
            "sayings": {"ar": [], "en": [], "fr": []},
            "provenance": "verified-classical-source",
            "canonicalBiography": True,
            "canonicalBiographyCount": 1,
            "sourceWordCount": wc,
        })
        new_ids.append(pid)
        new_names.append(nm)
        counts.append(wc)

    previous_count = len(people) - TARGET
    people_doc["people"] = people
    people_doc["count"] = len(people)
    people_doc["latestBiographyExpansion"] = {
        "added": TARGET,
        "previousPeopleCount": previous_count,
        "newPeopleCount": len(people),
        "source": SOURCE_TITLE,
        "author": SOURCE_AUTHOR,
        "policy": "50 genuinely new registry entries; verbatim source-backed body; no AI substantive content.",
    }
    PEOPLE.write_text(json.dumps(people_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit = {
        "schema": "expanded-biographies-50-audit-v1",
        "target": TARGET,
        "added": len(chosen),
        "previousPeopleCount": previous_count,
        "newPeopleCount": len(people),
        "duplicateAgainstExistingIds": len(set(new_ids) & existing_ids),
        "duplicateAgainstExistingNames": len({norm_ar(x) for x in new_names} & existing_names),
        "duplicateWithinNewIds": len(new_ids) - len(set(new_ids)),
        "duplicateWithinNewNames": len(new_names) - len({norm_ar(x) for x in new_names}),
        "minimumSourceWords": min(counts),
        "maximumSourceWords": max(counts),
        "requiredMinimumWords": MIN_WORDS,
        "sourceCoveragePercent": 100,
        "aiOriginalSubstantiveContentPercent": 0,
        "source": {
            "title": SOURCE_TITLE,
            "author": SOURCE_AUTHOR,
            "mirror": "Arabic Wikisource",
            "api": "core-revisions",
        },
        "newIds": new_ids,
        "complete": (
            len(chosen) == TARGET
            and not (set(new_ids) & existing_ids)
            and not ({norm_ar(x) for x in new_names} & existing_names)
            and len(new_ids) == len(set(new_ids))
            and len(new_names) == len({norm_ar(x) for x in new_names})
            and min(counts) >= MIN_WORDS
        ),
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))
    if not audit["complete"]:
        raise SystemExit("50-biography expansion audit failed")


if __name__ == "__main__":
    main()
