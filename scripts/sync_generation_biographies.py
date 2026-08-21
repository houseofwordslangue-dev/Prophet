#!/usr/bin/env python3
"""Build source-extracted Tābiʿīn and Atbāʿ al-Tābiʿīn biography shards.

The source is Al-Itqan's open structured rijāl corpus. The script never creates
biographical facts: it copies only non-empty source fields from the published
records and classifies a person only when the record carries an attributable
ṭabaqa/generation marker.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generations"
OUT.mkdir(parents=True, exist_ok=True)
BASE = "https://r3genesi5.github.io/Itqan/app/data/rijal/"
UA = "ProphetBiographySite/7.0-generation-extractor"
TARGETS = {"tabiin": 7883, "atba_tabiin": 5808}
SHARD_SIZE = 750

ARABIC_ORDINALS = {
    "الأولى": 1, "الاولى": 1,
    "الثانية": 2, "الثالثة": 3, "الرابعة": 4, "الخامسة": 5,
    "السادسة": 6, "السابعة": 7, "الثامنة": 8, "التاسعة": 9,
    "العاشرة": 10, "الحادية عشرة": 11, "الحادي عشر": 11,
    "الثانية عشرة": 12, "الثاني عشر": 12,
}

KEEP_FIELDS = (
    "id", "key", "full_name", "name_ar", "name", "kunya", "laqab", "nasab",
    "nisba", "birth", "birth_year", "death", "death_year", "city", "place",
    "residence", "tabaqat", "tabaqa", "generation", "grade_ar", "grade_en",
    "grade", "dhahabi", "jarh_wa_tadil", "namings", "name_variants", "aliases",
    "alternate_names", "teachers", "narrated_from", "shuyukh", "students",
    "narrated_to", "talabah", "relations", "relationships", "family", "sources",
    "source_refs", "classical_sources", "source_entries", "global_id", "confidence",
)


def get_json(name: str):
    req = urllib.request.Request(BASE + name, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=240) as r:
        return json.loads(r.read().decode("utf-8"))


def text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def tabaqa_number(p: dict) -> int | None:
    candidates = [p.get("generation"), p.get("tabaqa"), p.get("tabaqat")]
    for raw in candidates:
        if isinstance(raw, int) and 1 <= raw <= 12:
            return raw
        s = text(raw).strip()
        if not s:
            continue
        for label, n in ARABIC_ORDINALS.items():
            if s.startswith(label) or label in s:
                return n
        m = re.search(r"(?:generation|tabaq(?:a|at)?|طبقة)\s*[:#-]?\s*(\d{1,2})", s, re.I)
        if m and 1 <= int(m.group(1)) <= 12:
            return int(m.group(1))
        if s.isdigit() and 1 <= int(s) <= 12:
            return int(s)
    return None


def group_of(p: dict) -> str | None:
    grade = (text(p.get("grade_en")) + " " + text(p.get("grade_ar"))).lower()
    tabaqa = " ".join(text(p.get(k)) for k in ("tabaqat", "tabaqa", "generation"))
    if "companion" in grade or "صحاب" in grade or "صحاب" in tabaqa:
        return None
    if "اتباع التابع" in tabaqa.replace("أ", "ا") or "أتباع التابع" in tabaqa:
        return "atba_tabiin"
    if "تابع" in tabaqa and "اتباع" not in tabaqa.replace("أ", "ا"):
        return "tabiin"
    if "مخضرم" in tabaqa:
        return "tabiin"
    n = tabaqa_number(p)
    if n in (2, 3, 4, 5):
        return "tabiin"
    if n in (6, 7, 8, 9):
        return "atba_tabiin"
    return None


def meaningful(v) -> bool:
    return v not in (None, "", [], {})


def extract(p: dict, grade_partition: str) -> dict:
    out = {k: p[k] for k in KEEP_FIELDS if k in p and meaningful(p[k])}
    out["source_partition"] = grade_partition
    out["generation_group"] = group_of(p)
    out["source_record"] = "Al-Itqan unified rijal corpus v1.20"
    return out


def has_biographical_material(p: dict) -> bool:
    keys = (
        "nasab", "laqab", "birth", "birth_year", "death", "death_year", "city",
        "place", "residence", "tabaqat", "tabaqa", "generation", "dhahabi",
        "jarh_wa_tadil", "teachers", "narrated_from", "shuyukh", "students",
        "narrated_to", "talabah", "sources", "source_refs", "classical_sources",
        "source_entries", "namings", "name_variants", "aliases",
    )
    return any(meaningful(p.get(k)) for k in keys)


def stable_key(p: dict) -> str:
    return str(p.get("id") or p.get("key") or p.get("global_id") or p.get("full_name") or "")


def write_group(group: str, rows: list[dict]) -> list[dict]:
    rows.sort(key=lambda p: (text(p.get("full_name") or p.get("name_ar") or p.get("name")), stable_key(p)))
    shards = []
    for i in range(0, len(rows), SHARD_SIZE):
        chunk = rows[i:i + SHARD_SIZE]
        name = f"profiles_{group}_{i // SHARD_SIZE + 1:03d}.json"
        path = OUT / name
        payload = {stable_key(p): p for p in chunk if stable_key(p)}
        raw = (json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
        path.write_bytes(raw)
        shards.append({
            "name": name,
            "count": len(payload),
            "sha256": hashlib.sha256(raw).hexdigest(),
        })
    return shards


def main():
    manifest = get_json("manifest.json")
    profile_files = [x for x in manifest.get("files", []) if x.get("type") == "profiles" and x.get("grade") != "companion"]
    groups: dict[str, dict[str, dict]] = {"tabiin": {}, "atba_tabiin": {}}
    scanned = 0
    classifiable = Counter()

    for entry in profile_files:
        chunk = get_json(entry["name"])
        values = chunk.values() if isinstance(chunk, dict) else chunk
        for p in values:
            scanned += 1
            g = group_of(p)
            if not g:
                continue
            classifiable[g] += 1
            ep = extract(p, entry.get("grade", "unknown"))
            if not has_biographical_material(ep):
                continue
            k = stable_key(ep)
            if k:
                groups[g][k] = ep

    for old in OUT.glob("profiles_tabiin_*.json"):
        old.unlink()
    for old in OUT.glob("profiles_atba_tabiin_*.json"):
        old.unlink()

    output = {
        "schema": "source-extracted-generation-biographies-v1",
        "generatedAtUnix": int(time.time()),
        "source": {
            "name": "Al-Itqan unified narrator / rijal corpus",
            "manifestVersion": manifest.get("version"),
            "profileCount": manifest.get("total_profiles"),
            "classicalTexts": manifest.get("classical_texts"),
            "base": BASE,
        },
        "classification": {
            "tabiin": "explicit Tabi'i/Mukhadram markers or tabaqat 2-5",
            "atba_tabiin": "explicit Atba' al-Tabi'in markers or tabaqat 6-9",
            "rule": "No person is assigned from name, dates or AI inference alone.",
        },
        "groups": {},
        "scannedNonCompanionProfiles": scanned,
    }

    all_complete = True
    for g in ("tabiin", "atba_tabiin"):
        rows = list(groups[g].values())
        shards = write_group(g, rows)
        expected = TARGETS[g]
        published = len(rows)
        complete = published >= expected
        all_complete = all_complete and complete
        output["groups"][g] = {
            "expectedMinimum": expected,
            "classifiableSourceRecords": classifiable[g],
            "publishedExtractedProfiles": published,
            "completeAgainstProjectCheckpoint": complete,
            "shards": shards,
        }

    output["allRemainingGroupsComplete"] = all_complete
    raw = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    (OUT / "manifest.json").write_text(raw, encoding="utf-8")
    (ROOT / "GENERATION_BIOGRAPHY_REPORT.json").write_text(raw, encoding="utf-8")
    print(raw)
    if not all_complete:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
