#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import shutil
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PUBLIC_EPUBS = ROOT / "epubs"
INDEX = DATA / "generated_epubs.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def discover_roots(explicit: list[str]) -> list[Path]:
    roots: list[Path] = []
    candidates = explicit[:]
    env = os.getenv("PM_LIBRARY_ROOT", "").strip()
    if env:
        candidates.extend([x for x in env.split(os.pathsep) if x])
    candidates.extend([
        str(ROOT / "Prophet-Library-Ingestion" / "books"),
        str(ROOT.parent / "Prophet-Library-Ingestion" / "books"),
        str(Path.home() / "Prophet-Library-Ingestion" / "books"),
        str(Path.home() / "My Drive" / "Prophet-Library-Ingestion" / "books"),
        str(Path.home() / "Google Drive" / "My Drive" / "Prophet-Library-Ingestion" / "books"),
    ])
    seen = set()
    for raw in candidates:
        p = Path(raw).expanduser().resolve()
        if p in seen or not p.exists() or not p.is_dir():
            continue
        seen.add(p)
        roots.append(p)
    return roots


def extract_pdf_text(path: Path) -> str:
    try:
        import fitz  # PyMuPDF
    except Exception:
        return ""
    try:
        doc = fitz.open(path)
        chunks = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                chunks.append(f"\n\n===== PAGE {i + 1} =====\n{text}")
        doc.close()
        return "".join(chunks).strip()
    except Exception:
        return ""


def read_book_text(book_dir: Path) -> tuple[str, str]:
    preferred = [
        book_dir / "text.txt",
        book_dir / "complete.txt",
        book_dir / "book.txt",
    ]
    for p in preferred:
        if p.exists() and p.stat().st_size > 20:
            return p.read_text(encoding="utf-8", errors="replace"), p.name
    for p in sorted(book_dir.glob("*.txt")):
        if p.stat().st_size > 20:
            return p.read_text(encoding="utf-8", errors="replace"), p.name
    for name in ("searchable.pdf", "complete.pdf"):
        p = book_dir / name
        if p.exists() and p.stat().st_size > 4096:
            text = extract_pdf_text(p)
            if len(re.sub(r"\s+", "", text)) >= 200:
                return text, p.name
    for p in sorted(book_dir.glob("*.pdf")):
        if p.stat().st_size > 4096:
            text = extract_pdf_text(p)
            if len(re.sub(r"\s+", "", text)) >= 200:
                return text, p.name
    return "", ""


def metadata_for(book_dir: Path) -> dict:
    meta = load_json(book_dir / "metadata.json", {}) or {}
    title = meta.get("title") or meta.get("titleAr") or book_dir.name
    author = meta.get("author") or meta.get("authorAr") or ""
    language = meta.get("language") or "ar"
    return {"id": meta.get("id") or book_dir.name, "title": title, "author": author, "language": language, **meta}


def split_text(text: str, max_chars: int = 70000) -> list[str]:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paras = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    chapters: list[str] = []
    cur: list[str] = []
    size = 0
    for p in paras:
        if cur and size + len(p) > max_chars:
            chapters.append("\n\n".join(cur))
            cur, size = [], 0
        cur.append(p)
        size += len(p)
    if cur:
        chapters.append("\n\n".join(cur))
    return chapters or [text]


def xhtml_body(text: str) -> str:
    out = []
    for raw in re.split(r"\n{2,}", text):
        p = raw.strip()
        if not p:
            continue
        m = re.fullmatch(r"=+\s*PAGE\s+(\d+)\s*=+", p, flags=re.I)
        if m:
            out.append(f'<h2 class="page-marker">Page {m.group(1)}</h2>')
            continue
        out.append("<p>" + html.escape(p).replace("\n", "<br/>") + "</p>")
    return "\n".join(out)


def build_epub(out_path: Path, meta: dict, text: str) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_path.with_suffix(".epub.tmp")
    tmp.unlink(missing_ok=True)
    title = str(meta.get("title") or meta.get("titleAr") or meta.get("id") or "Book")
    author = str(meta.get("author") or meta.get("authorAr") or "")
    lang = str(meta.get("language") or "ar")
    book_id = str(meta.get("id") or uuid.uuid4())
    chapters = split_text(text)
    container_xml = """<?xml version=\"1.0\"?>\n<container version=\"1.0\" xmlns=\"urn:oasis:names:tc:opendocument:xmlns:container\"><rootfiles><rootfile full-path=\"OEBPS/content.opf\" media-type=\"application/oebps-package+xml\"/></rootfiles></container>"""
    css = "body{font-family:serif;line-height:1.9;margin:5%;}html[lang=ar] body{direction:rtl;text-align:right;}p{margin:.8em 0}.page-marker{font-size:.9em;color:#666;border-top:1px solid #ddd;padding-top:.5em}"
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="css" href="styles.css" media-type="text/css"/>',
    ]
    spine = []
    nav_links = []
    files: dict[str, str] = {}
    for i, chapter in enumerate(chapters, 1):
        fn = f"chapter-{i:04d}.xhtml"
        item_id = f"c{i}"
        manifest.append(f'<item id="{item_id}" href="{fn}" media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{item_id}"/>')
        nav_links.append(f'<li><a href="{fn}">{html.escape(title)} — {i}</a></li>')
        files[f"OEBPS/{fn}"] = f'''<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{html.escape(lang)}" lang="{html.escape(lang)}"><head><meta charset="utf-8"/><title>{html.escape(title)}</title><link rel="stylesheet" href="styles.css"/></head><body>{xhtml_body(chapter)}</body></html>'''
    opf = f'''<?xml version="1.0" encoding="utf-8"?>\n<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{html.escape(lang)}"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="bookid">urn:prophet:{html.escape(book_id)}</dc:identifier><dc:title>{html.escape(title)}</dc:title><dc:language>{html.escape(lang)}</dc:language><dc:creator>{html.escape(author)}</dc:creator><meta property="dcterms:modified">{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}</meta></metadata><manifest>{''.join(manifest)}</manifest><spine>{''.join(spine)}</spine></package>'''
    nav = f'''<?xml version="1.0" encoding="utf-8"?>\n<!DOCTYPE html>\n<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="{html.escape(lang)}" lang="{html.escape(lang)}"><head><title>{html.escape(title)}</title></head><body><nav epub:type="toc"><h1>{html.escape(title)}</h1><ol>{''.join(nav_links)}</ol></nav></body></html>'''
    with zipfile.ZipFile(tmp, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        z.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/styles.css", css, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        for name, body in files.items():
            z.writestr(name, body, compress_type=zipfile.ZIP_DEFLATED)
    tmp.replace(out_path)


def validate_epub(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as z:
            if z.read("mimetype") != b"application/epub+zip":
                return False
            names = set(z.namelist())
            return "META-INF/container.xml" in names and "OEBPS/content.opf" in names
    except Exception:
        return False


def process_book(book_dir: Path) -> dict:
    meta = metadata_for(book_dir)
    bid = str(meta.get("id") or book_dir.name)
    title = str(meta.get("title") or meta.get("titleAr") or bid)
    target = PUBLIC_EPUBS / f"{bid}.epub"
    existing = [book_dir / "complete.epub", book_dir / "book.epub"] + sorted(book_dir.glob("*.epub"))
    src_epub = next((p for p in existing if p.exists() and p.is_file() and validate_epub(p)), None)
    source_name = ""
    mode = "reflowable-text"
    if src_epub:
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists() or sha256(target) != sha256(src_epub):
            shutil.copy2(src_epub, target)
        source_name = src_epub.name
        mode = "existing-epub"
    else:
        text, source_name = read_book_text(book_dir)
        if len(re.sub(r"\s+", "", text)) < 200:
            return {"id": bid, "titleAr": title, "status": "NO_TEXT", "sourcePath": str(book_dir), "sourceFile": source_name}
        build_epub(target, meta, text)
    if not validate_epub(target):
        return {"id": bid, "titleAr": title, "status": "INVALID_EPUB", "sourcePath": str(book_dir), "sourceFile": source_name}
    return {
        "id": bid,
        "titleAr": title,
        "author": meta.get("author") or meta.get("authorAr") or "",
        "language": meta.get("language") or "ar",
        "epubPath": str(target.relative_to(ROOT)).replace(os.sep, "/"),
        "publicUrl": str(target.relative_to(ROOT)).replace(os.sep, "/"),
        "sourcePath": str(book_dir),
        "sourceFile": source_name,
        "mode": mode,
        "sizeBytes": target.stat().st_size,
        "sha256": sha256(target),
        "status": "READY_EPUB",
    }


def enumerate_book_dirs(roots: list[Path]) -> list[Path]:
    out = []
    seen = set()
    for root in roots:
        for p in sorted(root.iterdir()):
            if not p.is_dir():
                continue
            if p.resolve() in seen:
                continue
            seen.add(p.resolve())
            out.append(p)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert every locally available library work to EPUB and publish same-origin copies.")
    ap.add_argument("--root", action="append", default=[], help="Library books root; can be repeated")
    ap.add_argument("--strict", action="store_true", help="Exit non-zero if any work cannot be converted")
    args = ap.parse_args()
    roots = discover_roots(args.root)
    PUBLIC_EPUBS.mkdir(parents=True, exist_ok=True)
    previous = load_json(INDEX, {"items": []}) or {"items": []}
    by_id = {str(x.get("id")): x for x in previous.get("items", []) if x.get("id")}
    failures = []
    processed = 0
    for book_dir in enumerate_book_dirs(roots):
        row = process_book(book_dir)
        processed += 1
        if row.get("status") == "READY_EPUB":
            by_id[str(row["id"])] = row
            print("READY_EPUB", row["id"], row.get("titleAr", ""))
        else:
            failures.append(row)
            print(row.get("status"), row.get("id"), row.get("titleAr", ""))
    ready = sorted((x for x in by_id.values() if x.get("status") == "READY_EPUB"), key=lambda x: str(x.get("titleAr") or x.get("id")))
    payload = {
        "version": 2,
        "generatedAt": now_iso(),
        "roots": [str(x) for x in roots],
        "processedThisRun": processed,
        "count": len(ready),
        "failedThisRun": failures,
        "items": ready,
    }
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Published EPUBs:", len(ready), "processed:", processed, "failed:", len(failures))
    if args.strict and failures:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
