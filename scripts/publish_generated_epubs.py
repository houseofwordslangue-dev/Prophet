#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "generated_epubs.json"
STORE = ROOT / "library" / "works"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def valid_epub(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size < 256:
            return False
        with zipfile.ZipFile(path) as z:
            return z.read("mimetype") == b"application/epub+zip" and "META-INF/container.xml" in z.namelist()
    except Exception:
        return False


def locate_epub(row: dict) -> Path | None:
    candidates = []
    for key in ("epubPath", "publicUrl", "path", "localPath"):
        raw = str(row.get(key) or "").strip().lstrip("/")
        if raw:
            candidates.append(ROOT / raw)
    bid = str(row.get("id") or "").strip()
    if bid:
        candidates.extend([
            ROOT / "epubs" / f"{bid}.epub",
            ROOT / "Prophet-Library-Ingestion" / "books" / bid / "complete.epub",
            ROOT / "Prophet-Library-Ingestion" / "books" / bid / "book.epub",
        ])
    seen = set()
    for p in candidates:
        p = p.resolve()
        if p in seen:
            continue
        seen.add(p)
        if valid_epub(p):
            return p
    return None


def main() -> int:
    if not MANIFEST.exists():
        print("No generated EPUB manifest; nothing to publish")
        return 0
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    published = []
    missing = []
    for row in data.get("items", []):
        if row.get("status") != "READY_EPUB":
            continue
        work_id = str(row.get("id") or "").strip()
        if not work_id:
            continue
        src = locate_epub(row)
        if src is None:
            missing.append({"id": work_id, "title": row.get("titleAr") or row.get("title")})
            continue
        digest = sha256(src)
        edition_id = f"ed-{digest[:12]}"
        dest_dir = STORE / work_id / "editions" / edition_id
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "original.epub"
        if not dest.exists() or sha256(dest) != digest:
            shutil.copy2(src, dest)
        meta = {
            "workId": work_id,
            "editionId": edition_id,
            "titleOriginal": row.get("titleAr") or row.get("title") or work_id,
            "titleAr": row.get("titleAr"),
            "titleEn": row.get("titleEn"),
            "titleFr": row.get("titleFr"),
            "author": row.get("author") or "",
            "language": row.get("language") or "ar",
            "subjects": row.get("subjects") or ["المصادر والدراسات"],
            "siteSections": row.get("siteSections") or ["المصادر والدراسات"],
            "format": "epub",
            "mimeType": mimetypes.types_map.get(".epub", "application/epub+zip"),
            "size": dest.stat().st_size,
            "sha256": digest,
            "searchable": True,
            "listenable": True,
            "watchable": False,
            "sourceGeneratedEpub": True,
        }
        (dest_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        published.append({"id": work_id, "editionId": edition_id, "path": str(dest.relative_to(ROOT))})
    report = {
        "manifestReady": sum(1 for x in data.get("items", []) if x.get("status") == "READY_EPUB"),
        "publishedThisRun": len(published),
        "missingBinary": len(missing),
        "published": published,
        "missing": missing,
    }
    out = ROOT / "data" / "generated_epubs_publication_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
