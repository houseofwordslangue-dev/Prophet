#!/usr/bin/env python3
# GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md
from __future__ import annotations

import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS_FILE = ROOT / "data" / "editorial_sections.json"
DRAFTS_ROOT = ROOT / "data" / "editorial" / "drafts"
AUDIT_FILE = ROOT / "data" / "editorial" / "daily_rotation_audit.json"
BUILDER_FILE = ROOT / "scripts" / "build_100_genuine_articles.py"

# Eight main editorial sections => one run every three hours covers all in 24h.
ROTATION = ["light", "prophet", "messenger", "human", "mercy", "family", "companions", "media"]

# Broad, conservative section signals. Selection must have a positive score;
# we do not force an unrelated source extract merely to meet cadence.
SECTION_TERMS = {
    "light": ("light", "spiritual", "mystic", "mysticism", "sufi", "sufism", "نور", "روح"),
    "prophet": ("prophet", "mohammad", "muhammad", "birth", "childhood", "character", "mecca", "medina", "النبي"),
    "messenger": ("revelation", "revealed", "mission", "preach", "preaching", "message", "qur'an", "quran", "koran", "الرسالة", "الوحي"),
    "human": ("daily", "home", "food", "dress", "illness", "smile", "human", "habit", "marriage", "personal", "family life"),
    "mercy": ("mercy", "merciful", "compassion", "kindness", "forgave", "forgive", "forgiveness", "pardon", "charity"),
    "family": ("khadija", "aisha", "wife", "wives", "daughter", "son", "uncle", "father", "mother", "family", "marriage"),
    "companions": ("abu bakr", "omar", "umar", "uthman", "othman", "ali", "companion", "companions", "sahaba"),
    "media": ("speech", "speeches", "table-talk", "lecture", "sermon", "audio", "video", "documentary", "podcast", "transcript", "narration"),
}


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_builder():
    spec = importlib.util.spec_from_file_location("genuine_builder", BUILDER_FILE)
    if not spec or not spec.loader:
        raise RuntimeError("unable to load genuine-source builder")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def section_slot(section: str, slots_doc: dict) -> tuple[str, str] | None:
    choices = [
        (str(x.get("section") or ""), str(x.get("subsection") or ""))
        for x in (slots_doc.get("sections") or [])
        if x.get("active") and x.get("editorial") and str(x.get("section") or "") == section
    ]
    if not choices:
        return None
    preferred = [x for x in choices if x[1] == "research"]
    return (preferred or choices)[0]


def candidate_score(candidate: dict, section: str) -> int:
    text = " ".join([
        str(candidate.get("heading") or ""),
        str((candidate.get("source") or {}).get("titleOriginal") or ""),
        " ".join(candidate.get("paragraphs") or []),
    ]).lower()
    return sum(text.count(term.lower()) for term in SECTION_TERMS[section])


def existing_fingerprints() -> set[str]:
    seen = set()
    for path in DRAFTS_ROOT.glob("**/*.json"):
        data = load_json(path, {}) or {}
        for item in data.get("drafts", []) if isinstance(data, dict) else []:
            if not isinstance(item, dict):
                continue
            for source in item.get("sources") or []:
                fp = str(source.get("sourceFingerprint") or "").strip()
                if fp:
                    seen.add(fp)
            fp = str(item.get("sourceFingerprint") or "").strip()
            if fp:
                seen.add(fp)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--section", choices=ROTATION)
    args = ap.parse_args()

    now = datetime.now(timezone.utc)
    section = args.section or ROTATION[(now.hour // 3) % len(ROTATION)]
    slots_doc = load_json(SECTIONS_FILE, {}) or {}
    slot = section_slot(section, slots_doc)
    audit = load_json(AUDIT_FILE, {}) or {}
    audit.setdefault("version", "daily-rotating-editorial-fill-v1")
    audit.setdefault("sections", {})

    if not slot:
        audit["sections"][section] = {"status": "NEEDS_REVIEW", "at": now.isoformat(), "reason": "No active editorial slot"}
        save_json(AUDIT_FILE, audit)
        print("NEEDS_REVIEW", section, "No active editorial slot")
        return 0

    builder = load_builder()
    valid_pairs = {(slot[0], slot[1])}
    used = existing_fingerprints()
    all_candidates = []

    for src in builder.source_records():
        try:
            text = builder.fetch_text(src)
        except Exception as exc:
            print("SOURCE_RETRY", src.get("workId"), exc)
            continue
        if not text:
            continue
        try:
            candidates = builder.candidate_articles(src, text)
        except Exception as exc:
            print("SOURCE_PARSE_RETRY", src.get("workId"), exc)
            continue
        for c in candidates:
            if c.get("fingerprint") in used:
                continue
            score = candidate_score(c, section)
            if score > 0:
                all_candidates.append((score, c))

    if not all_candidates:
        audit["sections"][section] = {
            "status": "NEEDS_SOURCE",
            "at": now.isoformat(),
            "reason": "No unused source-grounded candidate matched this section; cadence does not override source truth.",
        }
        audit["lastRun"] = now.isoformat()
        save_json(AUDIT_FILE, audit)
        print("NEEDS_SOURCE", section)
        return 0

    all_candidates.sort(key=lambda pair: (-pair[0], str((pair[1].get("source") or {}).get("workId") or ""), str(pair[1].get("fingerprint") or "")))
    chosen = all_candidates[0][1]

    day = now.date().isoformat()
    seq = int(now.timestamp())
    record = builder.build_record(chosen, seq, valid_pairs)
    record["id"] = f"daily-{day}-{section}-{seq}"
    record["section"] = slot[0]
    record["subsection"] = slot[1]
    record["publicationStatus"] = "READY"
    record["publishedAt"] = now.isoformat()
    record["dailyRotation"] = {"section": section, "cycle": day, "cadence": "one verified article per main section per 24h when source-supported"}

    # Rebind paragraph/source IDs after changing the record ID.
    source_ref = record["id"] + "-source"
    for i, p in enumerate(record.get("paragraphs") or [], 1):
        p["id"] = f"{record['id']}-p{i:02d}"
        p["sourceRefs"] = [source_ref]
    for s in record.get("sources") or []:
        s["ref"] = source_ref

    out_dir = DRAFTS_ROOT / day
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"daily-{section}-{seq}.json"
    save_json(out, {"version": "daily-rotating-source-extract-v1", "generatedAt": now.isoformat(), "count": 1, "drafts": [record]})

    audit["sections"][section] = {
        "status": "READY_TO_PUBLISH",
        "at": now.isoformat(),
        "id": record["id"],
        "path": str(out.relative_to(ROOT)).replace("\\", "/"),
        "sourceFingerprint": chosen.get("fingerprint"),
    }
    audit["lastRun"] = now.isoformat()
    save_json(AUDIT_FILE, audit)
    print("READY_TO_PUBLISH", section, record["id"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
