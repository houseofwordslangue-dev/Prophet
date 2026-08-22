#!/usr/bin/env python3
"""Build deterministic source-grounded rijal biography batches.

Each batch contains at most 50 source profiles. No missing biographical fact is
invented: fields absent from the source profile are omitted. The resulting
records are consumed by the canonical person.html rijal biography renderer.
"""
from __future__ import annotations

import argparse
import json
import math
import urllib.request
from pathlib import Path

REMOTE = "https://r3genesi5.github.io/Itqan/app/data/rijal/"
BATCH_SIZE = 50
KEEP = (
    "id", "global_id", "full_name", "name_ar", "name", "kunya", "laqab",
    "nasab", "nisba", "grade_ar", "grade_en", "grade", "tabaqat", "tabaqa",
    "generation", "city", "place", "residence", "birth", "birth_year",
    "death", "death_year", "namings", "name_variants", "aliases", "dhahabi",
    "jarh_wa_tadil", "teachers", "narrated_from", "shuyukh", "students",
    "narrated_to", "talabah", "relations", "relationships", "family",
    "classical_sources", "source_entries", "sources", "source_refs",
    "provenance", "unique_key", "uniqueness"
)


def get_json(url: str):
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.load(response)


def clean_profile(profile: dict, partition: str) -> dict:
    out = {k: profile[k] for k in KEEP if k in profile and profile[k] not in (None, "", [], {})}
    out["source_partition"] = partition
    out["canonical_url"] = f"person.html?rijal=1&id={profile.get('id', profile.get('global_id', ''))}&group=rijal&lang=ar&p={partition}"
    out["provenance_class"] = "SOURCED_EXTRACTED"
    return out


def profile_sort_key(item):
    p = item[1]
    raw = p.get("id", p.get("global_id", item[0]))
    try:
        return (0, int(raw))
    except Exception:
        return (1, str(raw))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start-batch", type=int, default=1)
    ap.add_argument("--batch-count", type=int, default=1)
    ap.add_argument("--out", default="data/editorial/rijal-biography-batches")
    args = ap.parse_args()

    manifest = get_json(REMOTE + "manifest.json")
    partitions = [x for x in manifest.get("files", []) if x.get("type") == "profiles"]
    rows = []
    for part in partitions:
        name = part["name"]
        data = get_json(REMOTE + name)
        for key, profile in sorted(data.items(), key=profile_sort_key):
            if isinstance(profile, dict) and (profile.get("full_name") or profile.get("name_ar") or profile.get("name")):
                rows.append(clean_profile(profile, name))

    outdir = Path(args.out)
    outdir.mkdir(parents=True, exist_ok=True)
    total_batches = math.ceil(len(rows) / BATCH_SIZE)
    start = max(1, args.start_batch)
    end = min(total_batches, start + max(1, args.batch_count) - 1)

    produced = []
    for batch_no in range(start, end + 1):
        a = (batch_no - 1) * BATCH_SIZE
        b = min(len(rows), a + BATCH_SIZE)
        records = rows[a:b]
        payload = {
            "schema": "rijal-biography-batch-v1",
            "batchNumber": batch_no,
            "batchSize": len(records),
            "configuredBatchSize": BATCH_SIZE,
            "sourceProfileTotal": len(rows),
            "source": "R3GENESI5/Itqan app/data/rijal",
            "provenanceClass": "SOURCED_EXTRACTED",
            "status": "SOURCE_READY",
            "policy": {
                "onePersonOneCanonicalBiography": True,
                "noInventedFacts": True,
                "missingFields": "omit",
                "publicProcessCommentary": False
            },
            "records": records
        }
        path = outdir / f"batch-{batch_no:04d}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        produced.append(str(path))

    state = {
        "schema": "rijal-biography-batch-state-v1",
        "sourceProfileTotal": len(rows),
        "batchSize": BATCH_SIZE,
        "totalBatches": total_batches,
        "lastRequestedStartBatch": start,
        "lastRequestedEndBatch": end,
        "produced": produced
    }
    (outdir / "state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(state, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
