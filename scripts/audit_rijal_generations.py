#!/usr/bin/env python3
"""Build a source-evidenced rijal generation audit and compact public index.

Only explicit source generation/tabaqa fields are used. Dates, teacher/student
relations, old target counts and chronology heuristics never assign a generation.
Contradictions between explicit tabaqa evidence and the source chunk's Companion
status are quarantined in the general narrator corpus.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

DEFAULT_BASE = "https://raw.githubusercontent.com/R3GENESI5/Itqan/master/app/data/rijal"
ARABIC_ORDINALS = {
    "الأولى": 1, "الثانية": 2, "الثالثة": 3, "الرابعة": 4,
    "الخامسة": 5, "السادسة": 6, "السابعة": 7, "الثامنة": 8,
    "التاسعة": 9, "العاشرة": 10, "الحادية عشرة": 11,
    "الثانية عشرة": 12,
}


def fetch_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "Prophet-people-audit/1.1"})
    with urllib.request.urlopen(req, timeout=120) as response:
        return json.load(response)


def iter_profiles(payload: Any) -> Iterable[tuple[str, dict[str, Any]]]:
    if isinstance(payload, dict):
        if isinstance(payload.get("profiles"), list):
            for idx, item in enumerate(payload["profiles"]):
                if isinstance(item, dict):
                    yield str(item.get("id", idx)), item
            return
        for key, value in payload.items():
            if isinstance(value, dict):
                yield str(key), value
        return
    if isinstance(payload, list):
        for idx, item in enumerate(payload):
            if isinstance(item, dict):
                yield str(item.get("id", idx)), item


def parse_layer(value: Any, *, allow_free_numeric: bool) -> set[int]:
    out: set[int] = set()
    if value is None or value == "" or isinstance(value, bool):
        return out
    if isinstance(value, int):
        if 1 <= value <= 12:
            out.add(value)
        return out
    if isinstance(value, float) and value.is_integer():
        return parse_layer(int(value), allow_free_numeric=allow_free_numeric)
    if isinstance(value, (list, tuple, set)):
        for part in value:
            out.update(parse_layer(part, allow_free_numeric=allow_free_numeric))
        return out
    if isinstance(value, dict):
        for key in ("order", "number", "id", "tabaqa_order", "generation"):
            if key in value:
                out.update(parse_layer(value[key], allow_free_numeric=True))
        return out

    text = str(value).strip()
    for label, number in ARABIC_ORDINALS.items():
        if text.startswith(label) or text.startswith(f"الطبقة {label}"):
            out.add(number)
    if allow_free_numeric:
        exact = re.fullmatch(r"\s*(1[0-2]|[1-9])(?:st|nd|rd|th)?(?:\s+Generation)?\s*", text, flags=re.I)
        bracketed = re.search(r"\[(1[0-2]|[1-9])(?:st|nd|rd|th)?\s+Generation\]", text, flags=re.I)
        if exact:
            out.add(int(exact.group(1)))
        if bracketed:
            out.add(int(bracketed.group(1)))
    return out


def explicit_layer(profile: dict[str, Any]) -> tuple[int | None, list[str], bool]:
    evidence: list[str] = []
    layers: set[int] = set()
    for field in ("tabaqa_order", "generation", "tabaqat"):
        value = profile.get(field)
        if value in (None, "", []):
            continue
        found = parse_layer(value, allow_free_numeric=(field != "tabaqat"))
        if found:
            layers.update(found)
            evidence.append(field)
    if len(layers) == 1:
        return next(iter(layers)), evidence, False
    if len(layers) > 1:
        return None, evidence, True
    return None, evidence, False


def bucket(layer: int | None) -> str:
    if layer == 1:
        return "companions_explicit_layer"
    if layer is not None and 2 <= layer <= 6:
        return "tabiin"
    if layer is not None and 7 <= layer <= 9:
        return "atba_al_tabiin"
    if layer is not None and 10 <= layer <= 12:
        return "post_atba"
    return "unclassified"


def source_status_conflict(source_grade: str | None, layer: int | None) -> bool:
    if layer is None:
        return False
    if source_grade == "companion" and layer != 1:
        return True
    if source_grade != "companion" and layer == 1:
        return True
    return False


def slim_record(source_file: str, source_key: str, source_grade: str | None, profile: dict[str, Any], layer: int | None, classification: str, conflict: bool) -> dict[str, Any]:
    value = {
        "id": f"{source_file.removeprefix('profiles_').removesuffix('.json')}:{source_key}",
        "source_file": source_file,
        "source_key": source_key,
        "source_grade": source_grade,
        "name": profile.get("full_name") or profile.get("name") or profile.get("name_ar") or source_key,
        "grade": profile.get("grade_en") or profile.get("grade") or source_grade,
        "tabaqa": profile.get("tabaqat"),
        "tabaqa_order": layer,
        "generation_class": classification,
        "generation_conflict": conflict or None,
        "city": profile.get("city"),
        "death": profile.get("death"),
        "kunya": profile.get("kunya"),
    }
    return {k: v for k, v in value.items() if v not in (None, "", [])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--out", default="data/people/rijal-audit.json")
    parser.add_argument("--index-out", default="data/people/rijal-index.json")
    parser.add_argument("--expected-total", type=int, default=115735)
    parser.add_argument("--expected-companions", type=int, default=10880)
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    manifest = fetch_json(f"{base}/manifest.json")
    profile_files = [f for f in manifest.get("files", []) if f.get("type") == "profiles"]

    totals = Counter()
    layer_counts = Counter()
    field_counts = Counter()
    source_counts: dict[str, dict[str, Any]] = {}
    compact_index: list[dict[str, Any]] = []

    for source in profile_files:
        name = source["name"]
        source_grade = source.get("grade")
        payload = fetch_json(f"{base}/{name}")
        file_counter = Counter()
        observed = 0
        for source_key, profile in iter_profiles(payload):
            observed += 1
            layer, evidence, field_conflict = explicit_layer(profile)
            status_conflict = source_status_conflict(source_grade, layer)
            conflict = field_conflict or status_conflict
            if field_conflict:
                totals["field_generation_conflicts"] += 1
            if status_conflict:
                totals["source_status_conflicts"] += 1
            if conflict:
                totals["generation_conflicts"] += 1
                classification = "unclassified"
            else:
                classification = bucket(layer)

            totals[classification] += 1
            file_counter[classification] += 1
            if layer is not None:
                layer_counts[str(layer)] += 1
            else:
                totals["without_explicit_layer"] += 1
            for field in evidence:
                field_counts[field] += 1
            compact_index.append(slim_record(name, source_key, source_grade, profile, layer, classification, conflict))

        expected_file_count = source.get("count")
        source_counts[name] = {
            "source_grade": source_grade,
            "manifest_count": expected_file_count,
            "observed_count": observed,
            "count_matches_manifest": expected_file_count == observed,
            "classifications": dict(sorted(file_counter.items())),
        }
        totals["all_profiles"] += observed

    companion_manifest = next((f for f in profile_files if f.get("grade") == "companion"), {})
    partition = (
        totals["tabiin"] + totals["atba_al_tabiin"] + totals["post_atba"] +
        totals["companions_explicit_layer"] + totals["unclassified"]
    )
    checks = {
        "total_matches_expected": totals["all_profiles"] == args.expected_total,
        "total_matches_source_manifest": totals["all_profiles"] == manifest.get("total_profiles"),
        "companion_manifest_matches_expected": companion_manifest.get("count") == args.expected_companions,
        "all_chunk_counts_match_manifest": all(v["count_matches_manifest"] for v in source_counts.values()),
        "classification_partition_matches_total": partition == totals["all_profiles"],
        "companion_chunk_not_counted_as_later_generation": all(
            source_counts.get("profiles_companion.json", {}).get("classifications", {}).get(k, 0) == 0
            for k in ("tabiin", "atba_al_tabiin", "post_atba")
        ),
    }

    audit = {
        "schema_version": 2,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "method": "explicit_source_generation_fields_with_conflict_quarantine",
        "source": {
            "repository": "R3GENESI5/Itqan",
            "base_url": base,
            "manifest_version": manifest.get("version"),
            "manifest_total": manifest.get("total_profiles"),
            "manifest_companions": companion_manifest.get("count"),
        },
        "rules": {
            "companions": [1],
            "tabiin": [2, 3, 4, 5, 6],
            "atba_al_tabiin": [7, 8, 9],
            "post_atba": [10, 11, 12],
            "no_heuristic_inference": True,
            "conflicting_explicit_evidence": "unclassified",
            "companion_chunk_vs_later_tabaqa_conflict": "unclassified",
            "non_companion_chunk_vs_layer_1_conflict": "unclassified",
        },
        "counts": {
            "all_profiles": totals["all_profiles"],
            "companions_manifest": companion_manifest.get("count"),
            "companions_explicit_layer_nonconflicting": totals["companions_explicit_layer"],
            "tabiin": totals["tabiin"],
            "atba_al_tabiin": totals["atba_al_tabiin"],
            "post_atba": totals["post_atba"],
            "unclassified": totals["unclassified"],
            "without_explicit_layer": totals["without_explicit_layer"],
            "generation_conflicts": totals["generation_conflicts"],
            "field_generation_conflicts": totals["field_generation_conflicts"],
            "source_status_conflicts": totals["source_status_conflicts"],
        },
        "layer_counts_raw_before_conflict_quarantine": dict(sorted(layer_counts.items(), key=lambda x: int(x[0]))),
        "evidence_field_counts": dict(sorted(field_counts.items())),
        "source_files": source_counts,
        "checks": checks,
        "complete": all(checks.values()),
    }

    out = Path(args.out)
    index_out = Path(args.index_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    index_out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    index_out.write_text(json.dumps({"schema_version": 2, "count": len(compact_index), "records": compact_index}, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")

    print(json.dumps(audit["counts"], ensure_ascii=False, indent=2))
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
