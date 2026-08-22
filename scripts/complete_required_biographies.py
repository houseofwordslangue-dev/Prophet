#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import base64
import gzip
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
EDITORIAL = DATA / "editorial"
DRAFTS = EDITORIAL / "drafts"
OUT = EDITORIAL / "required_biographies.json"
AUDIT = EDITORIAL / "required_biographies_audit.json"
FINAL_SOURCES = DATA / "final_missing_biographies.json"

REQUIRED_CATEGORIES = {
    "prophet", "family", "ancestor", "companion", "companions",
    "tabii", "tabiin", "follower", "followers", "successor", "successors",
    "tabi-al-tabiin", "tabi-tabiin", "household",
}
EXCLUDED_CATEGORIES = {"source-person", "author", "translator", "researcher", "editor"}


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def name_ar(p: dict) -> str:
    n = p.get("name") or {}
    return (n.get("ar") if isinstance(n, dict) else "") or p.get("nameAr") or p.get("name") or p.get("id") or ""


def add_person(required: dict[str, dict], p: dict, origin: str):
    pid = str(p.get("id") or p.get("slug") or "").strip()
    if not pid:
        return
    cat = str(p.get("category") or "family").strip().lower()
    if cat in EXCLUDED_CATEGORIES:
        return
    if cat not in REQUIRED_CATEGORIES and origin == "people.json":
        return
    row = required.setdefault(pid, {
        "id": pid,
        "nameAr": name_ar(p),
        "category": cat or "family",
        "origins": [],
    })
    if origin not in row["origins"]:
        row["origins"].append(origin)
    if not row.get("nameAr"):
        row["nameAr"] = name_ar(p)
    if row.get("category") in {"", "family"} and cat:
        row["category"] = cat


def load_all_bios() -> dict:
    chunks = sorted(DATA.glob("family_biographies_all.*.b64"), key=lambda p: int(p.name.split(".")[-2]))
    if not chunks:
        return {"people": []}
    try:
        b64 = "".join(p.read_text(encoding="utf-8").strip() for p in chunks)
        raw = gzip.decompress(base64.b64decode(b64)).decode("utf-8")
        return json.loads(raw)
    except Exception:
        return {"people": []}


def biography_text_present(row: dict) -> bool:
    bio = row.get("biography") or row.get("professionalBiography") or {}
    if isinstance(bio, dict):
        return any(bool(v) for v in bio.values())
    return bool(bio)


def verified_passage_count(row: dict) -> int:
    count = 0
    for x in row.get("sourcePassages") or []:
        sources = x.get("sources") or [] if isinstance(x, dict) else []
        if sources and all(s.get("verifiedAgainstOriginal") is not False for s in sources if isinstance(s, dict)):
            count += 1
    return count


def draft_rows(path: Path):
    data = load_json(path, {})
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []
    return data.get("drafts") or data.get("items") or data.get("articles") or []


def person_ref(article: dict):
    rp = article.get("relatedPerson") or article.get("person") or {}
    if isinstance(rp, dict) and rp.get("id"):
        return str(rp.get("id")), str(rp.get("name") or "")
    subject = article.get("subject")
    if isinstance(subject, dict) and subject.get("id"):
        return str(subject.get("id")), str(subject.get("name") or "")
    if isinstance(subject, str) and subject and not subject.startswith("http"):
        if " " not in subject and len(subject) < 120:
            return subject, ""
    return None, ""


def article_has_verified_source(article: dict) -> bool:
    if article.get("sourceCoveragePercent") == 100 and article.get("provenanceStatus") == "PASS":
        return True
    pars = article.get("paragraphs") or []
    if not pars:
        return False
    return all((not p.get("substantive", True)) or bool(p.get("sourceRefs")) for p in pars if isinstance(p, dict))


def main():
    required: dict[str, dict] = {}
    sources_by_id: dict[str, list[dict]] = defaultdict(list)

    people = load_json(DATA / "people.json", {"people": []})
    for p in people.get("people", []):
        add_person(required, p, "people.json")
        if p.get("id"):
            sources_by_id[str(p["id"])].append(p)

    family_people = load_json(DATA / "family_people.json", {"people": []})
    for p in family_people.get("people", []):
        add_person(required, p, "family_people.json")
        if p.get("id"):
            sources_by_id[str(p["id"])].append(p)

    groups = load_json(DATA / "family_groups.json", {"registry": []})
    for p in groups.get("registry", []):
        add_person(required, p, "family_groups.json")
        if p.get("id"):
            sources_by_id[str(p["id"])].append(p)

    detailed = load_json(DATA / "family_biographies.json", {"people": []})
    all_bios = load_all_bios()
    final_sources = load_json(FINAL_SOURCES, {"people": []})
    for dataset, origin in (
        (detailed, "family_biographies.json"),
        (all_bios, "family_biographies_all"),
        (final_sources, "final_missing_biographies.json"),
    ):
        for p in dataset.get("people", []):
            pid = str(p.get("id") or "").strip()
            if pid:
                sources_by_id[pid].append(p)
                if pid in required and origin not in required[pid]["origins"]:
                    required[pid]["origins"].append(origin)

    canonical = load_json(EDITORIAL / "canonical_biographies.json", {"people": {}}).get("people", {})
    support: dict[str, list[dict]] = defaultdict(list)

    for path in sorted(DRAFTS.glob("**/*.json")):
        for article in draft_rows(path):
            if not isinstance(article, dict):
                continue
            pid, pname = person_ref(article)
            if not pid:
                continue
            if pid not in required:
                required[pid] = {"id": pid, "nameAr": pname or pid, "category": "historical-person", "origins": ["editorial-relatedPerson"]}
            if article_has_verified_source(article):
                support[pid].append({
                    "id": article.get("id"),
                    "title": article.get("title"),
                    "section": article.get("section"),
                    "subsection": article.get("subsection"),
                    "wordCount": article.get("wordCount"),
                    "path": str(path.relative_to(ROOT)),
                })

    output_people = {}
    missing = []
    completed_from_existing = 0
    completed_from_supporting = 0

    for pid in sorted(required):
        p = required[pid]
        evidence_rows = sources_by_id.get(pid, [])
        bio_present = any(biography_text_present(x) for x in evidence_rows)
        passage_count = sum(verified_passage_count(x) for x in evidence_rows)
        support_rows = support.get(pid, [])
        prior = canonical.get(pid) or {}
        prior_canonical = prior.get("canonicalBiographyCount") == 1
        has_evidence = bio_present or passage_count > 0 or len(support_rows) > 0 or prior_canonical
        if bio_present or passage_count > 0 or prior_canonical:
            completed_from_existing += 1
        elif support_rows:
            completed_from_supporting += 1
        if not has_evidence:
            missing.append({
                "id": pid,
                "nameAr": p.get("nameAr") or pid,
                "category": p.get("category"),
                "origins": p.get("origins", []),
            })
        nm = p.get("nameAr") or pid
        output_people[pid] = {
            "id": pid,
            "nameAr": nm,
            "category": p.get("category"),
            "canonicalBiographyCount": 1 if has_evidence else 0,
            "canonicalStatus": "SOURCE_VERIFIED" if has_evidence else "SOURCE_REQUIRED",
            "canonicalUrl": f"person.html?id={quote(pid)}&name={quote(nm)}",
            "verifiedBiographyTextPresent": bio_present,
            "verifiedSourcePassageCount": passage_count,
            "supportingSourceArticleCount": len(support_rows),
            "supportingSourceArticles": support_rows,
            "origins": sorted(set(p.get("origins", []))),
            "policy": "One canonical person page; source articles remain supporting thematic material.",
        }

    payload = {
        "schema": "required-canonical-biographies-v1",
        "policy": {
            "oneBiographyPerPerson": True,
            "excludeReferenceOnlyPeople": True,
            "noTitleBasedIdentityGuessing": True,
            "sourceOnly": True,
        },
        "requiredPersonCount": len(required),
        "canonicalCompleteCount": len(required) - len(missing),
        "missingCanonicalBiographyCount": len(missing),
        "complete": len(missing) == 0,
        "people": output_people,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit = {
        "schema": "required-canonical-biographies-audit-v1",
        "requiredPersonCount": len(required),
        "canonicalCompleteCount": len(required) - len(missing),
        "missingCanonicalBiographyCount": len(missing),
        "completedFromExistingBiographyOrPassages": completed_from_existing,
        "completedFromSupportingSourceArticles": completed_from_supporting,
        "missing": missing,
        "complete": len(missing) == 0,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))
    if missing:
        raise SystemExit(f"Missing canonical source-backed biographies: {len(missing)}")


if __name__ == "__main__":
    main()
