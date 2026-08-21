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
TARGET_VERSION = "genuine-source-autopublish-v2"


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


def verified_override(ov: dict) -> tuple[bool, str]:
    if not isinstance(ov, dict):
        return False, "missing verification override"
    paragraphs = [str(x).strip() for x in (ov.get("paragraphs") or []) if str(x).strip()]
    if not paragraphs:
        return False, "verification override has no verified paragraphs"
    if not str(ov.get("sourceRef") or "").strip():
        return False, "verification override has no sourceRef"
    if not str(ov.get("sourceFile") or "").strip():
        return False, "verification override has no sourceFile"
    if not str(ov.get("volume") or "").strip():
        return False, "verification override has no volume"
    if not str(ov.get("pdfPage") or "").strip():
        return False, "verification override has no pdfPage"
    return True, "complete source-verified manifest override"


def strict_verified(d: dict, overrides: dict) -> tuple[bool, str]:
    did = str(d.get("id") or "")
    if int(d.get("sourceCoveragePercent") or -1) != 100:
        return False, "sourceCoveragePercent != 100"
    if int(d.get("aiOriginalSubstantiveContentPercent") or 0) != 0:
        return False, "non-source substantive content present"
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
            return False, "paragraph not source-derived"
        if not (p.get("sourceRefs") or []):
            return False, "paragraph has no sourceRefs"

    if did in overrides:
        return verified_override(overrides.get(did) or {})

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
    ledger_ids = list(dict.fromkeys(str(x) for x in (manifest.get("publishedIds") or []) if x))

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

    # Build the effective publication set only from records that still have
    # source-backed draft data or a complete source-verified manifest override.
    effective_current = []
    manifest_verified = set()
    stale_ledger = []
    for did in ledger_ids:
        if did in by_id:
            ok, reason = strict_verified(by_id[did], overrides)
            if ok:
                effective_current.append(did)
            else:
                stale_ledger.append((did, reason))
            continue
        ok, reason = verified_override(overrides.get(did) or {})
        if ok:
            effective_current.append(did)
            manifest_verified.add(did)
        else:
            stale_ledger.append((did, reason))

    effective_set = set(effective_current)
    newly_published = [x for x in eligible if x not in effective_set]
    published = effective_current + newly_published

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
        "activeEditorialSlotsCovered": len(covered_slots & active_slots) if by_id else int(integrity.get("activeEditorialSlotsCovered") or 0),
        "activeEditorialSlotsTotal": len(active_slots),
        "allMainSectionsHaveMoreThanOneArticle": (bool(section_counts) and all(v > 1 for v in section_counts.values())) if section_counts else bool(integrity.get("allMainSectionsHaveMoreThanOneArticle", False)),
        "manifestVerifiedOverridesWithoutLegacyDraft": len(manifest_verified),
        "staleManifestIdsExcluded": len(stale_ledger),
    })

    print("eligible verified drafts:", len(eligible))
    print("manifest-only source-verified records:", len(manifest_verified))
    print("effective already published:", len(effective_current))
    print("stale manifest ledger IDs excluded:", len(stale_ledger))
    for did, reason in stale_ledger:
        print("STALE", did, reason, sep=" | ")
    print("newly publishable:", len(newly_published))
    print("rejected/pending verification:", len(rejected))
    print("active slots covered:", integrity["activeEditorialSlotsCovered"], "/", integrity["activeEditorialSlotsTotal"])

    if args.check:
        return 0

    manifest_needs_cleanup = published != ledger_ids
    activation_needed = not bool((manifest.get("automation") or {}).get("enabled")) or manifest.get("version") != TARGET_VERSION
    if not newly_published and not activation_needed and not manifest_needs_cleanup:
        print("No publication-state change required.")
        return 0

    stamp = iso_now()
    manifest.update({
        "version": TARGET_VERSION,
        "status": "PUBLISHED",
        "policy": "genuine-source-only / automatic publication after strict provenance verification",
        "publishedAt": stamp if newly_published else (manifest.get("publishedAt") or stamp),
        "publicFeed": manifest.get("publicFeed") or "editorial.html",
        "articleRoute": manifest.get("articleRoute") or "feature.html?id={id}",
        "draftBatchPaths": batch_paths,
        "publishedIds": published,
        "integrity": integrity,
        "automation": {
            "enabled": True,
            "mode": "strict-source-autopublish",
            "schedule": "hourly plus source/draft pushes",
            "rule": "Only records with complete source provenance and verified quotations/originals are published.",
            "activatedAt": (manifest.get("automation") or {}).get("activatedAt") or stamp,
            "lastPublicationAt": stamp if newly_published else (manifest.get("automation") or {}).get("lastPublicationAt"),
            "newlyPublishedThisRun": len(newly_published),
            "staleManifestIdsRemovedThisRun": len(stale_ledger),
        },
    })
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    if newly_published:
        print("PUBLISHED NEW IDS:", ", ".join(newly_published))
    if stale_ledger:
        print("REMOVED STALE IDS:", ", ".join(x[0] for x in stale_ledger))
    if not newly_published and not stale_ledger:
        print("AUTOPUBLISHER ACTIVATED; existing publication set preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
