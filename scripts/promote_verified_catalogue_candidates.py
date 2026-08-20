#!/usr/bin/env python3
"""Promote rights-cleared exact catalogue sources into the acquisition queue.

The professional 689-record catalogue separates work identity, access resolution,
and full-text eligibility. This promoter respects those fields and never promotes a
record merely because a title or discovery page exists.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import argparse
import base64
import gzip
import json

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "catalogue" / "manifest.json"
QUEUE = ROOT / "private" / "acquisition_candidates.json"
UA = "ProphetBiographyLibrary/6.7 catalogue-promoter"
MAX_BYTES = 400 * 1024 * 1024

LEGACY_SCHEMA = [
    "id","entryNumber","category","titleAr","title","authorAr","author","kind",
    "rightsStatus","verificationStatus","availabilityStatus","modesCsv","verifiedSource",
    "editionNoteAr","ingestionStatus","century","language","publicationYear"
]


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def truthy(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v or "").strip().lower() in {"1", "true", "yes", "y", "eligible", "allowed"}


def explicit_public_domain(row: dict) -> bool:
    if "eligibleForFullTextCopy" in row and not truthy(row.get("eligibleForFullTextCopy")):
        return False
    text = " ".join(str(row.get(k) or "") for k in (
        "rightsStatus", "publicNotes", "editionNoteAr", "blockerAr"
    )).lower()
    return any(token in text for token in (
        "public domain", "public-domain", "public_domain", "cc0", "unrestricted", "الملك العام"
    ))


def archive_identifier(url: str) -> str:
    p = urlparse(url)
    if p.hostname not in {"archive.org", "www.archive.org"}:
        return ""
    parts = [x for x in p.path.split("/") if x]
    if len(parts) >= 2 and parts[0] in {"details", "download"}:
        return parts[1]
    return ""


def get_json(url: str, timeout: int = 45):
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=timeout) as r:
        return json.load(r)


def choose_archive_file(identifier: str):
    meta = get_json(f"https://archive.org/metadata/{quote(identifier)}")
    files = meta.get("files", []) if isinstance(meta, dict) else []
    candidates = []
    for f in files:
        name = str(f.get("name") or "")
        low = name.lower()
        if not low.endswith((".pdf", ".epub", ".txt")):
            continue
        try:
            size = int(f.get("size") or 0)
        except Exception:
            size = 0
        if size and (size < 1024 or size > MAX_BYTES):
            continue
        if low.endswith("_text.pdf"):
            score = 0
        elif low.endswith(".pdf"):
            score = 1
        elif low.endswith(".epub"):
            score = 2
        else:
            score = 3
        candidates.append((score, size or MAX_BYTES, name))
    if not candidates:
        return None
    _, _, name = sorted(candidates)[0]
    ext = name.rsplit(".", 1)[-1].lower()
    return {
        "format": ext,
        "downloadUrl": f"https://archive.org/download/{quote(identifier)}/{quote(name)}",
        "sourceIdentifier": identifier,
    }


def gutenberg_download(url: str):
    p = urlparse(url)
    if p.hostname not in {"gutenberg.org", "www.gutenberg.org"}:
        return None
    parts = [x for x in p.path.split("/") if x]
    try:
        i = parts.index("ebooks")
        ebook_id = parts[i + 1]
    except Exception:
        return None
    if not ebook_id.isdigit():
        return None
    return {
        "format": "txt",
        "downloadUrl": f"https://gutenberg.org/ebooks/{ebook_id}.txt.utf-8",
        "sourceIdentifier": ebook_id,
    }


def professional_records(manifest: dict):
    payload_path = manifest.get("compressedPayload")
    if not payload_path:
        return None
    path = ROOT / str(payload_path)
    raw = base64.b64decode(path.read_text(encoding="utf-8").strip())
    payload = json.loads(gzip.decompress(raw).decode("utf-8"))
    schema = payload.get("schema", [])
    return [{k: (raw_row[i] if i < len(raw_row) else "") for i, k in enumerate(schema)}
            for raw_row in payload.get("items", [])]


def iter_catalogue():
    manifest = read_json(MANIFEST, {})
    try:
        records = professional_records(manifest)
    except Exception:
        records = None
    if records is not None:
        yield from records
        return

    chunks = manifest.get("chunks") or manifest.get("fallbackChunks") or []
    for chunk in chunks:
        path = ROOT / str(chunk.get("path") or "")
        doc = read_json(path, {})
        for raw in doc.get("items", []):
            if isinstance(raw, list):
                yield {k: (raw[i] if i < len(raw) else "") for i, k in enumerate(LEGACY_SCHEMA)}
            elif isinstance(raw, dict):
                yield raw


def source_for(row: dict):
    exact = str(row.get("exactSourceUrl") or row.get("verifiedSource") or "").strip()
    archive_id = str(row.get("archiveIdentifier") or "").strip()
    if exact:
        return exact, archive_identifier(exact) or archive_id
    if archive_id:
        return f"https://archive.org/details/{archive_id}", archive_id
    return "", ""


def promote(limit: int):
    queue = read_json(QUEUE, {"schema": "strict-unrestricted-candidates-v1", "rotationEnabled": True, "items": []})
    items = queue.setdefault("items", [])
    seen_work = {str(x.get("workId") or "") for x in items}
    seen_source = {(str(x.get("sourceRepository") or ""), str(x.get("sourceIdentifier") or "")) for x in items}
    scanned = eligible = added = 0
    errors = []

    for row in iter_catalogue():
        scanned += 1
        if not explicit_public_domain(row):
            continue
        source, archive_id = source_for(row)
        if not source:
            continue
        eligible += 1
        resolved = None
        repo = ""
        try:
            if archive_id:
                resolved = choose_archive_file(archive_id)
                repo = "Internet Archive"
            else:
                resolved = gutenberg_download(source)
                repo = "Project Gutenberg" if resolved else ""
        except Exception as exc:
            errors.append({"id": row.get("id"), "source": source, "error": type(exc).__name__})
            continue
        if not resolved:
            continue

        work_id = str(row.get("id") or resolved["sourceIdentifier"])
        key = (repo, str(resolved["sourceIdentifier"]))
        if work_id in seen_work or key in seen_source:
            continue

        title_ar = str(row.get("titleAr") or "")
        title = str(row.get("originalTitle") or row.get("title") or title_ar or work_id)
        author = str(row.get("authorAr") or row.get("authorRomanized") or row.get("author") or "")
        language = str(row.get("language") or ("ar" if title_ar else "en"))
        item = {
            "workId": work_id,
            "catalogueId": work_id,
            "titleOriginal": title,
            "titleAr": title_ar,
            "author": author,
            "language": language,
            "format": resolved["format"],
            "sourceRepository": repo,
            "sourceIdentifier": resolved["sourceIdentifier"],
            "sourceUrl": source,
            "downloadUrl": resolved["downloadUrl"],
            "rightsEvidence": "Public domain — professional catalogue marks full-text copy eligible",
            "rightsEvidenceUrl": source,
            "subjects": [str(row.get("categoryAr") or row.get("category") or "المصادر")],
            "siteSections": ["المصادر والدراسات"],
        }
        items.append(item)
        seen_work.add(work_id)
        seen_source.add(key)
        added += 1
        if added >= limit:
            break

    if added:
        QUEUE.parent.mkdir(parents=True, exist_ok=True)
        QUEUE.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"scanned": scanned, "eligible": eligible, "added": added, "queueTotal": len(items), "errors": errors[:20]}, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25)
    args = ap.parse_args()
    return promote(max(0, args.limit))


if __name__ == "__main__":
    raise SystemExit(main())
