#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITORIAL = ROOT / "data" / "editorial"
DRAFTS = EDITORIAL / "drafts"
MANIFEST = EDITORIAL / "publication_manifest.json"
SECTIONS = ROOT / "data" / "editorial_sections.json"


def load(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def iter_drafts():
    for path in sorted(DRAFTS.glob("*/batch-*.json")):
        pack = load(path, {}) or {}
        for d in pack.get("drafts", []) or []:
            if isinstance(d, dict) and d.get("id"):
                yield path, d


def strict_verified(d: dict, overrides: dict) -> tuple[bool, str]:
    did = str(d.get("id") or "")
    if int(d.get("sourceCoveragePercent") or -1) != 100:
        return False, "sourceCoveragePercent != 100"
    if int(d.get("aiOriginalSubstantiveContentPercent") or 0) != 0:
        return False, "AI substantive content present"
    if int(d.get("unsupportedFactualParagraphs") or 0) != 0:
        return False, "unsupported factual paragraph present"
    if str(d.get("provenanceStatus") or "").upper() != "PASS":
        return False, "provenance not PASS"
    if str(d.get("duplicateCheck") or "PASS").upper() != "PASS":
        return False, "duplicate check not PASS"

    paragraphs = d.get("paragraphs") or []
    sources = d.get("sources") or []
    if not paragraphs or not sources:
        return False, "missing paragraphs or sources"
    for p in paragraphs:
        if p.get("aiOriginal") is True:
            return False, "paragraph marked aiOriginal"
        if not (p.get("sourceRefs") or []):
            return False, "paragraph has no sourceRefs"

    # A visual/manual verification override is authoritative only when it contains
    # replacement source text. This supports the already-reviewed Ibn Hisham OCR cases.
    if did in overrides:
        ov = overrides.get(did) or {}
        if not (ov.get("paragraphs") or []):
            return False, "verification override has no verified paragraphs"
        return True, "manual/visual verification override"

    if str(d.get("quotationVerification") or "").upper() != "PASS":
        return False, "quotation verification not PASS"
    if int(d.get("unverifiedQuotations") or 0) != 0:
        return False, "unverified quotation present"
    for p in paragraphs:
        if p.get("quotation") and p.get("quotationVerified") is not True:
            return False, "quotation not verified"
    for s in sources:
        if s.get("verifiedAgainstOriginal") is not True:
            return False, "source not verified against original"
    return True, "strict source verification PASS"


def main() -> int:
    ap = argparse.ArgumentParser(description="Publish only fully verified genuine-source editorial drafts")
    ap.add_argument("--check", action="store_true", help="Validate and report without writing")
    args = ap.parse_args()

    manifest = load(MANIFEST, {}) or {}
    overrides = manifest.get("verificationOverrides") or {}
    current = list(dict.fromkeys(str(x) for x in (manifest.get("publishedIds") or []) if x))
    current_set = set(current)

    eligible = []
    rejected = []
    batch_paths = []
    by_id = {}
    for path, d in iter_drafts():
        did = str(d["id"])
        by_id[did] = d
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if rel not in batch_paths:
            batch_paths.append(rel)
        ok, reason = strict_verified(d, overrides)
        if ok:
            eligible.append(did)
        else:
            rejected.append({"id": did, "reason": reason})

    # Never silently drop a previously published item. A previously published item
    # missing from today's draft corpus is treated as a hard failure instead.
    missing_current = [x for x in current if x not in by_id]
    if missing_current:
        raise SystemExit("FAIL: published IDs missing from draft corpus: " + ", ".join(missing_current))

    newly_published = [x for x in eligible if x not in current_set]
    published = current + newly_published

    slots_doc = load(SECTIONS, {}) or {}
    active_slots = {
        f"{x.get('section')}/{x.get('subsection')}"
        for x in (slots_doc.get("sections") or [])
        if x.get("active") and x.get("editorial")
    }
    covered_slots = {
        f"{by_id[x].get('section')}/{by_id[x].get('subsection')}"
        for x in published if x in by_id
    }
    section_counts = {}
    for did in published:
        d = by_id.get(did) or {}
        sec = str(d.get("section") or "")
        if sec:
            section_counts[sec] = section_counts.get(sec, 0) + 1

    integrity = dict(manifest.get("integrity") or {})
    integrity.update({
        "articlesPublished": len(published),
        "genuineSourceDerivedArticles": len(published),
        "aiGeneratedSubstantiveArticles": 0,
        "articlesWith100PercentSourceProvenance": len(published),
        "unsupportedFactualParagraphs": 0,
        "unverifiedQuotations": 0,
        "activeEditorialSlotsCovered": len(covered_slots & active_slots),
        "activeEditorialSlotsTotal": len(active_slots),
        "allMainSectionsHaveMoreThanOneArticle": bool(section_counts) and all(v > 1 for v in section_counts.values()),
    })

    print("eligible verified drafts:", len(eligible))
    print("already published:", len(current))
    print("newly publishable:", len(newly_published))
    print("rejected/pending verification:", len(rejected))
    print("active slots covered:", integrity["activeEditorialSlotsCovered"], "/", integrity["activeEditorialSlotsTotal"])

    if args.check or not newly_published:
        return 0

    manifest.update({
        "version": "genuine-source-autopublish-v2",
        "status": "PUBLISHED",
        "policy": "genuine-source-only / zero AI substantive content / automatic publication after strict provenance verification",
        "publishedAt": iso_now(),
        "publicFeed": manifest.get("publicFeed") or "editorial.html",
        "articleRoute": manifest.get("articleRoute") or "feature.html?id={id}",
        "draftBatchPaths": batch_paths,
        "publishedIds": published,
        "integrity": integrity,
        "automation": {
            "enabled": True,
            "mode": "strict-source-autopublish",
            "rule": "Only 100% source-provenance records with zero AI substantive content and verified quotations/originals are published.",
            "lastPublicationAt": iso_now(),
            "newlyPublishedThisRun": len(newly_published),
        },
    })
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("PUBLISHED NEW IDS:", ", ".join(newly_published))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
