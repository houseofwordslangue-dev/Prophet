#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
"""Build deterministic 50-person canonical biography assignment batches.

The script does not generate historical prose. It assigns source-backed rijal
profiles to the site's single canonical person route and records which source
fields are available for each biography.
"""
from __future__ import annotations

import argparse
import json
import math
import urllib.parse
import urllib.request
from pathlib import Path

SOURCE_BASE = "https://raw.githubusercontent.com/R3GENESI5/Itqan/master/app/data/rijal/"
EXPECTED_TOTAL = 115735
BATCH_SIZE = 50
PROFILE_FILES = [
    ("profiles_companion.json", "companion"),
    ("profiles_reliable.json", "reliable"),
    ("profiles_mostly_reliable.json", "mostly_reliable"),
    ("profiles_weak.json", "weak"),
    ("profiles_abandoned.json", "abandoned"),
    ("profiles_fabricator.json", "fabricator"),
    ("profiles_unknown.json", "unknown"),
]
BIO_FIELDS = [
    "full_name", "name_ar", "name", "kunya", "nasab", "laqab", "birth",
    "death", "city", "place", "residence", "tabaqat", "tabaqa", "generation",
    "grade_ar", "grade_en", "dhahabi", "jarh_wa_tadil", "teachers",
    "narrated_from", "students", "narrated_to", "relations", "classical_sources",
    "source_entries", "namings"
]


def load_json(name: str, source_dir: Path | None):
    if source_dir:
        return json.loads((source_dir / name).read_text(encoding="utf-8"))
    with urllib.request.urlopen(SOURCE_BASE + name, timeout=180) as r:
        return json.loads(r.read().decode("utf-8"))


def nonempty(v):
    return v is not None and v != "" and v != [] and v != {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, help="Local directory containing Itqan rijal JSON files")
    ap.add_argument("--output-dir", type=Path, default=Path("data/biography_batches/generated"))
    ap.add_argument("--allow-source-count-change", action="store_true")
    args = ap.parse_args()

    rows = []
    seen = set()
    duplicate_ids = []

    for partition_order, (filename, grade) in enumerate(PROFILE_FILES):
        data = load_json(filename, args.source_dir)
        if not isinstance(data, dict):
            raise SystemExit(f"Expected object in {filename}")
        for key in sorted(data.keys(), key=str):
            profile = data[key] or {}
            source_id = str(profile.get("id") or profile.get("key") or profile.get("global_id") or key)
            if source_id in seen:
                duplicate_ids.append(source_id)
                continue
            seen.add(source_id)
            available = [f for f in BIO_FIELDS if nonempty(profile.get(f))]
            rows.append({
                "sourceId": source_id,
                "sourcePartition": filename,
                "sourceGrade": grade,
                "sourcePartitionOrder": partition_order,
                "availableBiographyFields": available,
                "canonicalRoute": "person.html?rijal=1&id=" + urllib.parse.quote(source_id, safe="") + "&group=rijal&lang={lang}",
                "biographyStatus": "source-profile-assigned",
            })

    total = len(rows)
    if total != EXPECTED_TOTAL and not args.allow_source_count_change:
        raise SystemExit(f"Source total changed: {total} != expected {EXPECTED_TOTAL}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    total_batches = math.ceil(total / BATCH_SIZE)
    for i in range(total_batches):
        chunk = rows[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        batch_no = i + 1
        out = {
            "schema": "prophet-biography-batch-materialized-v1",
            "batchNumber": batch_no,
            "count": len(chunk),
            "ordinalStart": i * BATCH_SIZE + 1,
            "ordinalEnd": i * BATCH_SIZE + len(chunk),
            "onePersonOneCanonicalBiography": True,
            "sourceProfileBodiesDuplicated": False,
            "records": chunk,
        }
        (args.output_dir / f"batch-{batch_no:04d}.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    audit = {
        "schema": "prophet-biography-batch-build-audit-v1",
        "sourceProfiles": total,
        "batchSize": BATCH_SIZE,
        "totalBatches": total_batches,
        "lastBatchSize": total - (total_batches - 1) * BATCH_SIZE,
        "duplicateSourceIdsExcluded": len(duplicate_ids),
        "allProfilesAssignedCanonicalRoute": total > 0,
        "historicalProseGenerated": False,
        "sourceProfileBodiesDuplicated": False,
    }
    (args.output_dir / "audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(audit, ensure_ascii=False))


if __name__ == "__main__":
    main()
