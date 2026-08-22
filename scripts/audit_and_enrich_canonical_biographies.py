#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DRAFTS = DATA / "editorial" / "drafts"
EXT_DIR = DATA / "editorial" / "biography-extensions"
INDEX = DATA / "editorial" / "canonical_biography_extensions.json"
AUDIT = DATA / "editorial" / "global_biography_placement_audit.json"

MAX_PASSAGES_PER_PERSON = 20
MIN_PASSAGE_CHARS = 120
MAX_PASSAGE_CHARS = 2400
MAX_RAW_FILE_BYTES = 8_000_000
RAW_ROOTS = [ROOT / "library", ROOT / "sources", ROOT / "content", DATA / "sources"]

LIFE_PATTERNS = [
    re.compile(r"سيرت(?:ه|ها)?\s*وحيات(?:ه|ها)?"),
    re.compile(r"(?:^|\s)سيرة\s+(?:وحياة\s+)?"),
    re.compile(r"من\s+سيرت(?:ه|ها)\s+وحيات(?:ه|ها)"),
    re.compile(r"\bbiograph(?:y|ies)\b", re.I),
    re.compile(r"\blife\s+(?:and\s+times\s+)?of\b", re.I),
    re.compile(r"\bvie\s+de\b", re.I),
    re.compile(r"\bbiographie\b", re.I),
]

AR_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06EDـ]")
ARABIC = re.compile(r"[\u0600-\u06ff]")
LATIN = re.compile(r"[A-Za-z]")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def norm_ar(value: str) -> str:
    value = AR_DIACRITICS.sub("", str(value or ""))
    value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    return re.sub(r"\s+", " ", value).strip()


def safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-") or "person"


def rows_of(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("drafts", "items", "articles", "records"):
            if isinstance(payload.get(key), list):
                return payload[key]
    return []


def title_of(row: dict) -> str:
    title = row.get("title") or row.get("headline") or ""
    if isinstance(title, dict):
        return " ".join(str(v) for v in title.values())
    return str(title)


def person_of(row: dict):
    for key in ("relatedPerson", "subject"):
        obj = row.get(key)
        if isinstance(obj, dict) and obj.get("id"):
            return str(obj["id"]), str(obj.get("name") or obj.get("nameAr") or obj["id"])
    for key in ("canonicalPersonId", "subjectPerson", "personId"):
        if row.get(key):
            return str(row[key]), str(row.get("canonicalPersonName") or row.get("nameAr") or row[key])
    return None


def life_intent(row: dict) -> bool:
    markers = " ".join(str(row.get(k) or "") for k in ("articleKind", "editorialCategory", "contentType", "publicRole")).lower()
    if any(x in markers for x in ("biography", "life-biograph", "life-profile", "canonical-biography-chapter")):
        return True
    if row.get("biographyPlacement") is True:
        return True
    return any(p.search(title_of(row)) for p in LIFE_PATTERNS)


def explicit_source_backing(row: dict) -> bool:
    markers = " ".join(str(row.get(k) or "") for k in ("contentType", "draftStatus", "publicationStatus", "sourceType")).upper()
    if any(x in markers for x in ("SOURCE", "VERIFIED", "EXTRACT", "TRANSCR", "OCR")):
        return True
    if row.get("sources") or row.get("sourceRefs") or row.get("references") or row.get("provenance") or row.get("source"):
        return True
    return False


def paragraph_texts(row: dict):
    seen = set()
    for key in ("paragraphs", "sourcePassages", "passages"):
        seq = row.get(key)
        if not isinstance(seq, list):
            continue
        for item in seq:
            text = item.get("text") if isinstance(item, dict) else item
            text = str(text or "").strip()
            if text and text not in seen:
                seen.add(text)
                yield text
    for key in ("body", "content", "text", "articleBody", "bodyAr"):
        value = row.get(key)
        if isinstance(value, str) and value.strip() and value.strip() not in seen:
            yield value.strip()


def source_meta(row: dict, path: Path) -> dict:
    srcs = row.get("sources") or row.get("references") or []
    if isinstance(srcs, dict):
        srcs = [srcs]
    meta = {
        "repositoryPath": str(path.relative_to(ROOT)),
        "recordId": row.get("id"),
        "recordTitle": title_of(row),
        "sourceType": "github-editorial-extraction",
    }
    if isinstance(srcs, list) and srcs:
        meta["sources"] = srcs[:8]
    if row.get("provenance"):
        meta["provenance"] = row.get("provenance")
    if row.get("source"):
        meta["source"] = row.get("source")
    # Preserve Drive identifiers if prior ingestion attached them anywhere in the row.
    row_blob = json.dumps(row, ensure_ascii=False)
    ids = sorted(set(re.findall(r"(?:driveFileId|fileId)[\"'\s:]+([A-Za-z0-9_-]{20,})", row_blob)))
    if ids:
        meta["driveFileIds"] = ids[:8]
        meta["sourceType"] = "drive-derived-github-extraction"
    return meta


def collect_people():
    people = {}
    aliases = defaultdict(set)

    def add(row):
        if not isinstance(row, dict) or not row.get("id"):
            return
        pid = str(row["id"])
        name = row.get("name") or {}
        name_ar = row.get("nameAr") or (name.get("ar") if isinstance(name, dict) else None)
        if not name_ar:
            return
        entry = people.setdefault(pid, {"id": pid, "nameAr": str(name_ar), "category": row.get("category") or ""})
        for candidate in (name_ar, row.get("displayNameAr")):
            if candidate:
                aliases[pid].add(norm_ar(str(candidate)))

    for path, key in [
        (DATA / "people.json", "people"),
        (DATA / "family_people.json", "people"),
        (DATA / "family_groups.json", "registry"),
        (DATA / "family_biographies.json", "people"),
    ]:
        payload = read_json(path, {}) or {}
        for row in payload.get(key, []) if isinstance(payload, dict) else []:
            add(row)

    # Only use exact, reasonably distinctive Arabic names for automatic raw-text matching.
    matchers = []
    for pid, p in people.items():
        names = sorted(aliases[pid] or {norm_ar(p["nameAr"])}, key=len, reverse=True)
        for name in names:
            tokens = name.split()
            if len(name) >= 8 and (len(tokens) >= 2 or len(name) >= 12):
                matchers.append((pid, name))
    matchers.sort(key=lambda x: len(x[1]), reverse=True)
    return people, aliases, matchers


def candidate_from_text(text: str, person_name_norm: str):
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < MIN_PASSAGE_CHARS:
        return None
    ntext = norm_ar(text)
    pos = ntext.find(person_name_norm)
    if pos < 0:
        return None
    # Preserve a bounded source passage, never synthesize missing wording.
    if len(text) > MAX_PASSAGE_CHARS:
        raw_pos = max(0, text.find(person_name_norm.split()[0]))
        start = max(0, raw_pos - 500)
        end = min(len(text), start + MAX_PASSAGE_CHARS)
        text = text[start:end].strip()
    # Arabic biography extension on Arabic person pages; Latin-heavy source blocks stay in research sections.
    ar = len(ARABIC.findall(text))
    lat = len(LATIN.findall(text))
    if ar < 80 or lat > max(20, ar // 5):
        return None
    return text


def fingerprint(text: str) -> str:
    return hashlib.sha256(norm_ar(text).encode("utf-8")).hexdigest()


def main():
    people, aliases, matchers = collect_people()
    candidates = defaultdict(list)
    seen = defaultdict(set)
    source_channel_counts = Counter()
    source_file_counts = Counter()
    editorial_records_scanned = 0
    life_records = 0
    misplaced = []
    unresolved_life = []

    draft_paths = sorted(DRAFTS.glob("**/*.json")) if DRAFTS.exists() else []
    for path in draft_paths:
        payload = read_json(path, {})
        for row in rows_of(payload):
            if not isinstance(row, dict):
                continue
            editorial_records_scanned += 1
            pobj = person_of(row)
            if life_intent(row):
                life_records += 1
                if pobj:
                    if row.get("section") != "canonical-person-biography" or row.get("publicListing") is not False:
                        misplaced.append({
                            "path": str(path.relative_to(ROOT)), "id": row.get("id"), "title": title_of(row),
                            "personId": pobj[0], "section": row.get("section"), "publicListing": row.get("publicListing")
                        })
                else:
                    unresolved_life.append({"path": str(path.relative_to(ROOT)), "id": row.get("id"), "title": title_of(row)})

            if not explicit_source_backing(row):
                continue
            texts = list(paragraph_texts(row))
            if not texts:
                continue
            # Explicit person link has priority and permits a shorter alias check.
            if pobj and pobj[0] in people:
                pid = pobj[0]
                names = aliases[pid] or {norm_ar(people[pid]["nameAr"])}
                for text in texts:
                    chosen = None
                    for nm in names:
                        chosen = candidate_from_text(text, nm)
                        if chosen:
                            break
                    if not chosen:
                        continue
                    fp = fingerprint(chosen)
                    if fp in seen[pid]:
                        continue
                    seen[pid].add(fp)
                    meta = source_meta(row, path)
                    candidates[pid].append({"text": chosen, "source": meta})
                    source_channel_counts[meta["sourceType"]] += 1
                    source_file_counts[str(path.relative_to(ROOT))] += 1
            else:
                # Unlinked source extractions: exact distinctive full-name match only.
                for text in texts:
                    ntext = norm_ar(text)
                    for pid, nm in matchers:
                        if nm not in ntext:
                            continue
                        chosen = candidate_from_text(text, nm)
                        if not chosen:
                            continue
                        fp = fingerprint(chosen)
                        if fp in seen[pid]:
                            continue
                        seen[pid].add(fp)
                        meta = source_meta(row, path)
                        candidates[pid].append({"text": chosen, "source": meta})
                        source_channel_counts[meta["sourceType"]] += 1
                        source_file_counts[str(path.relative_to(ROOT))] += 1
                        break

    raw_files_scanned = 0
    for root in RAW_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".txt", ".md", ".text"}:
                continue
            try:
                if path.stat().st_size > MAX_RAW_FILE_BYTES:
                    continue
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            raw_files_scanned += 1
            # Paragraph-ish blocks; keep source wording unchanged other than whitespace normalization.
            blocks = [x.strip() for x in re.split(r"\n\s*\n|(?<=\.)\s{2,}", text) if x.strip()]
            for block in blocks:
                if len(block) < MIN_PASSAGE_CHARS:
                    continue
                nblock = norm_ar(block)
                for pid, nm in matchers:
                    if nm not in nblock:
                        continue
                    chosen = candidate_from_text(block, nm)
                    if not chosen:
                        continue
                    fp = fingerprint(chosen)
                    if fp in seen[pid]:
                        continue
                    seen[pid].add(fp)
                    rel = str(path.relative_to(ROOT))
                    candidates[pid].append({
                        "text": chosen,
                        "source": {"repositoryPath": rel, "sourceType": "github-local-source-text"},
                    })
                    source_channel_counts["github-local-source-text"] += 1
                    source_file_counts[rel] += 1
                    break

    if EXT_DIR.exists():
        shutil.rmtree(EXT_DIR)
    EXT_DIR.mkdir(parents=True, exist_ok=True)

    indexed = {}
    total_passages = 0
    total_words = 0
    for pid, rows in sorted(candidates.items()):
        # Prefer Drive-derived and explicitly linked editorial extracts, then local source text.
        rows.sort(key=lambda x: (0 if x["source"].get("sourceType") == "drive-derived-github-extraction" else 1, -len(x["text"])))
        kept = rows[:MAX_PASSAGES_PER_PERSON]
        if not kept:
            continue
        for item in kept:
            item["wordCount"] = len(item["text"].split())
        total_passages += len(kept)
        total_words += sum(x["wordCount"] for x in kept)
        fname = safe_id(pid) + ".json"
        relfile = f"data/editorial/biography-extensions/{fname}"
        payload = {
            "schema": "canonical-biography-source-extension-v1",
            "generatedAt": utcnow(),
            "personId": pid,
            "personNameAr": people[pid]["nameAr"],
            "policy": "Verbatim/bounded source-derived passages only; no model-authored factual fill-in.",
            "passageCount": len(kept),
            "passages": kept,
        }
        (EXT_DIR / fname).write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        indexed[pid] = {
            "id": pid,
            "nameAr": people[pid]["nameAr"],
            "category": people[pid].get("category"),
            "passageCount": len(kept),
            "wordCount": sum(x["wordCount"] for x in kept),
            "file": relfile,
        }

    index = {
        "schema": "canonical-biography-source-extension-index-v1",
        "generatedAt": utcnow(),
        "policy": {
            "onePersonOneCanonicalBiographyPage": True,
            "extensionsRenderOnlyOnCanonicalPersonPage": True,
            "sourceDerivedOnly": True,
            "noGeneratedFactualFillIn": True,
            "thematicArticlesRemainInSections": True,
        },
        "indexedPeople": len(people),
        "peopleExtended": len(indexed),
        "passageCount": total_passages,
        "wordCount": total_words,
        "people": indexed,
    }
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    audit = {
        "schema": "global-biography-placement-audit-v1",
        "generatedAt": utcnow(),
        "indexedPeople": len(people),
        "canonicalPageRule": "person.html?id=<person-id>",
        "canonicalBiographyPagesPerIndexedPerson": 1,
        "editorialRecordsScanned": editorial_records_scanned,
        "lifeBiographyRecordsScanned": life_records,
        "misplacedBiographyLifeRecords": misplaced,
        "misplacedBiographyLifeRecordCount": len(misplaced),
        "unresolvedLifeIntentRecords": unresolved_life,
        "rawSourceFilesScanned": raw_files_scanned,
        "peopleExtended": len(indexed),
        "extensionPassages": total_passages,
        "extensionWords": total_words,
        "sourceChannelCounts": dict(source_channel_counts),
        "topSourceFiles": source_file_counts.most_common(30),
        "completePlacementForExplicitPeople": len(misplaced) == 0,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "indexedPeople": audit["indexedPeople"],
        "lifeBiographyRecordsScanned": life_records,
        "misplaced": len(misplaced),
        "peopleExtended": len(indexed),
        "extensionPassages": total_passages,
        "extensionWords": total_words,
        "rawSourceFilesScanned": raw_files_scanned,
    }, ensure_ascii=False))
    if misplaced:
        raise SystemExit("Biography placement audit failed: explicit life/biography records remain outside canonical person pages")


if __name__ == "__main__":
    main()
