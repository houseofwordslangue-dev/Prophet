#!/usr/bin/env python3
"""Promote explicitly public-domain records from the restored catalogue into the acquisition queue.

This script does not guess rights. A catalogue row is eligible only when its own
rights/edition evidence explicitly says public domain (English or Arabic) and it
contains a concrete Internet Archive or Project Gutenberg source URL.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
import argparse
import json

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "catalogue" / "manifest.json"
QUEUE = ROOT / "private" / "acquisition_candidates.json"
UA = "ProphetBiographyLibrary/6.7 catalogue-promoter"
MAX_BYTES = 400 * 1024 * 1024


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def explicit_public_domain(row: dict) -> bool:
    text = " ".join(str(row.get(k) or "") for k in ("rightsStatus", "editionNoteAr")).lower()
    return any(token in text for token in ("public domain", "public-domain", "الملك العام"))


def archive_identifier(url: str) -> str:
    p = urlparse(url)
    if p.hostname not in {"archive.org", "www.archive.org"}:
        return ""
    parts = [x for x in p.path.split("/") if x]
    if len(parts) >= 2 and parts[0] == "details":
        return parts[1]
    if len(parts) >= 2 and parts[0] == "download":
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


def iter_catalogue():
    manifest = read_json(MANIFEST, {})
    schema = manifest.get("schema", [])
    for chunk in manifest.get("chunks", []):
        path = ROOT / str(chunk.get("path") or "")
        doc = read_json(path, {})
        for raw in doc.get("items", []):
            if isinstance(raw, list):
                yield {k: (raw[i] if i < len(raw) else "") for i, k in enumerate(schema)}
            elif isinstance(raw, dict):
                yield raw


def promote(limit: int):
    queue = read_json(QUEUE, {"schema": "strict-unrestricted-candidates-v1", "rotationEnabled": True, "items": []})
    items = queue.setdefault("items", [])
    seen_work = {str(x.get("workId") or "") for x in items}
    seen_source = {(str(x.get("sourceRepository") or ""), str(x.get("sourceIdentifier") or "")) for x in items}
    scanned = eligible = added = 0
    errors = []

    for row in iter_catalogue():
        scanned += 1
        source = str(row.get("verifiedSource") or "").strip()
        if not source or not explicit_public_domain(row):
            continue
        eligible += 1
        resolved = None
        repo = ""
        try:
            identifier = archive_identifier(source)
            if identifier:
                resolved = choose_archive_file(identifier)
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
        title = str(row.get("title") or title_ar or work_id)
        author = str(row.get("authorAr") or row.get("author") or "")
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
            "rightsEvidence": "Public domain — explicit evidence retained in restored catalogue",
            "rightsEvidenceUrl": source,
            "subjects": [str(row.get("category") or "المصادر")],
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
