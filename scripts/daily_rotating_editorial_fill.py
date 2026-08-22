#!/usr/bin/env python3
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

# Use a broad/research-like home for source extracts where the taxonomy offers it.
PREFERRED_SUBSECTION = {
    "light": "research",
    "prophet": "research",
    "messenger": "research",
    "human": "research",
    "mercy": "mercy-stories",
    "family": "wives",
    "companions": "biographies",
    "media": "research",
}


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_builder():
    spec = importlib.util.spec_from_file_location("genuine_builder", BUILDER_FILE)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load genuine-source builder")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def active_pairs() -> set[tuple[str, str]]:
    doc = load_json(SECTIONS_FILE, {}) or {}
    return {
        (str(x.get("section")), str(x.get("subsection")))
        for x in (doc.get("sections") or [])
        if x.get("active") and x.get("editorial") and x.get("canonicalRotation")
    }


def used_fingerprints() -> set[str]:
    used = set()
    if not DRAFTS_ROOT.exists():
        return used
    for p in DRAFTS_ROOT.rglob("*.json"):
        obj = load_json(p, {}) or {}
        drafts = obj.get("drafts") if isinstance(obj, dict) else None
        if not isinstance(drafts, list):
            continue
        for d in drafts:
            if not isinstance(d, dict):
                continue
            for s in d.get("sources") or []:
                fp = str((s or {}).get("sourceFingerprint") or "").strip()
                if fp:
                    used.add(fp)
    return used


def score_candidate(section: str, candidate: dict) -> int:
    src = candidate.get("source") or {}
    hay = " ".join([
        str(candidate.get("heading") or ""),
        str(src.get("titleOriginal") or ""),
        str(src.get("author") or ""),
        " ".join(str(x) for x in (src.get("subjects") or [])),
        " ".join(str(x) for x in (candidate.get("paragraphs") or [])),
    ]).lower()
    score = 0
    for term in SECTION_TERMS[section]:
        n = hay.count(term.lower())
        if n:
            score += min(n, 8)
    return score


def choose_section(now: datetime) -> str:
    # Slots: 00,03,06,09,12,15,18,21 UTC. Any delayed run still maps
    # deterministically into the correct daily rotation slot.
    idx = (now.hour // 3) % len(ROTATION)
    return ROTATION[idx]


def main() -> int:
    ap = argparse.ArgumentParser(description="Create at most one new source-grounded article for the current rotating main section")
    ap.add_argument("--section", choices=ROTATION, help="override automatic three-hour section slot")
    args = ap.parse_args()

    now = datetime.now(timezone.utc).replace(microsecond=0)
    section = args.section or choose_section(now)
    day = now.date().isoformat()
    compact_day = now.strftime("%Y%m%d")
    out_dir = DRAFTS_ROOT / day
    out_file = out_dir / f"batch-daily-{section}.json"

    audit = load_json(AUDIT_FILE, {}) or {}
    audit.setdefault("version", "daily-section-rotation-v1")
    audit.setdefault("rotation", ROTATION)
    audit.setdefault("runs", [])

    # Exactly one new draft per section per UTC day. Re-runs are safe/no-op.
    if out_file.exists():
        print(f"DAILY ROTATION SKIP: {section} already has today's batch")
        audit["runs"].append({"at": now.isoformat(), "date": day, "section": section, "status": "ALREADY_FILLED"})
        audit["runs"] = audit["runs"][-100:]
        save_json(AUDIT_FILE, audit)
        return 0

    pairs = active_pairs()
    preferred = PREFERRED_SUBSECTION[section]
    target_pair = (section, preferred)
    section_pairs = sorted(p for p in pairs if p[0] == section)
    if target_pair not in pairs:
        if not section_pairs:
            print(f"DAILY ROTATION PENDING: no active canonical slot for {section}")
            audit["runs"].append({"at": now.isoformat(), "date": day, "section": section, "status": "NO_ACTIVE_SLOT"})
            audit["runs"] = audit["runs"][-100:]
            save_json(AUDIT_FILE, audit)
            return 0
        target_pair = section_pairs[0]

    builder = load_builder()
    builder.GENERATED_PREFIX = f"{compact_day}-daily-{section}-"
    builder.NOW = now.isoformat().replace("+00:00", "Z")

    used = used_fingerprints()
    candidates = []
    sources_scanned = 0

    for source in builder.source_records():
        # Keep the daily job bounded. The source list is relevance-sorted.
        if sources_scanned >= 24:
            break
        sources_scanned += 1
        text = builder.fetch_text(source)
        if not text:
            continue
        for c in builder.candidate_articles(source, text):
            fp = str(c.get("fingerprint") or "")
            if not fp or fp in used:
                continue
            sc = score_candidate(section, c)
            if sc > 0:
                candidates.append((sc, c))

    candidates.sort(key=lambda x: (-x[0], -int(x[1].get("wordCount") or 0), str(x[1].get("fingerprint") or "")))

    if not candidates:
        print(f"DAILY ROTATION PENDING: no new verified source candidate for {section}; nothing fabricated")
        audit["runs"].append({
            "at": now.isoformat(), "date": day, "section": section,
            "status": "NEEDS_SOURCE", "sourcesScanned": sources_scanned,
        })
        audit["runs"] = audit["runs"][-100:]
        save_json(AUDIT_FILE, audit)
        return 0

    score, candidate = candidates[0]
    record = builder.build_record(candidate, 1, {target_pair})
    record["dailyRotation"] = {
        "date": day,
        "section": section,
        "cadence": "one-new-source-grounded-article-per-main-section-per-24h",
        "slotHoursUtc": 3,
        "selectionScore": score,
        "masterInstruction": "MASTER_OVERRIDING_INSTRUCTION.md",
    }

    payload = {
        "version": "daily-section-rotation-v1",
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "section": section,
        "subsection": target_pair[1],
        "count": 1,
        "drafts": [record],
    }
    save_json(out_file, payload)

    audit["runs"].append({
        "at": now.isoformat(), "date": day, "section": section,
        "subsection": target_pair[1], "status": "DRAFT_READY_FOR_STRICT_AUTOPUBLISH",
        "articleId": record["id"], "sourceFingerprint": candidate["fingerprint"],
        "sourcesScanned": sources_scanned, "selectionScore": score,
    })
    audit["runs"] = audit["runs"][-100:]
    audit["lastRunAt"] = now.isoformat().replace("+00:00", "Z")
    audit["lastSection"] = section
    save_json(AUDIT_FILE, audit)

    print("DAILY ROTATION READY", section, target_pair[1], record["id"], sep=" | ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
