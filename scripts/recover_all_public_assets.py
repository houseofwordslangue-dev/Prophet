#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
"""Recover every rights-cleared, verifiable asset from the retained failed-download corpus.

This script understands the compact professional catalogue chunks plus unresolved records in
other data JSON files. It resolves high-confidence Archive.org matches, downloads only assets
that are public domain or carry a redistribution-friendly licence, respects GitHub's 100 MB
per-file limit, and never marks a catalogue record as local unless a real file exists.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CATALOGUE = DATA / "catalogue"
RECOVERY = DATA / "recovery"
LIBRARY = ROOT / "library" / "works"
INDEX = DATA / "ingested_library.json"
QUEUE = RECOVERY / "all_recovery_queue.json"
REPORT = RECOVERY / "all_recovery_report.json"

MAX_FILE_BYTES = int(os.getenv("RECOVERY_MAX_FILE_BYTES", str(95 * 1024 * 1024)))
MAX_TOTAL_BYTES = int(os.getenv("RECOVERY_MAX_TOTAL_BYTES", str(900 * 1024 * 1024)))
MAX_DOWNLOADS = int(os.getenv("RECOVERY_MAX_DOWNLOADS", "2000"))
TIMEOUT = int(os.getenv("RECOVERY_HTTP_TIMEOUT", "45"))
USER_AGENT = "ProphetLibraryRecovery/2.0 (+https://github.com/houseofwordslangue-dev/Prophet)"
ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_META = "https://archive.org/metadata/{identifier}"

UNRESOLVED_WORDS = (
    "awaiting", "unresolved", "failed", "missing", "undownloaded", "not-mirrored",
    "not mirrored", "research-pending", "research_pending", "source-ready-limited",
    "source_verified", "source-verified", "catalogued", "partial", "discovered",
)
SAFE_RIGHTS_WORDS = (
    "public-domain", "public domain", "public_domain", "الملك العام", "المجال العام",
    "cc0", "cc-by", "cc by", "cc-by-sa", "cc by-sa", "creative commons attribution",
    "no known copyright restrictions",
)
RESTRICTED_RIGHTS_WORDS = (
    "restricted", "copyright", "all rights reserved", "modern-edition-rights-restricted",
    "noncommercial", "non-commercial", "cc-by-nc", "cc by-nc",
)
STATUS_KEYS = (
    "ingestionStatus", "ingestion_status", "localAssetStatus", "local_asset_status",
    "accessResolutionStatus", "access_resolution_status", "availabilityStatus",
    "availability_status", "status", "state", "queueStatus", "queue_status",
    "recordedState", "recorded_state",
)
URL_KEYS = (
    "exactSourceUrl", "exact_source_url", "sourceDiscoveryUrl", "source_discovery_url",
    "sourceUrl", "source_url", "downloadUrl", "download_url", "directUrl", "direct_url",
    "manualLink", "manual_link", "sourcePage", "source_page", "archiveUrl", "archive_url", "url",
)
TITLE_KEYS = ("titleAr", "titleOriginal", "originalTitle", "title", "name", "work", "label", "titleEn", "titleFr")
AUTHOR_KEYS = ("authorAr", "author", "authorRomanized", "creator", "editor")
ID_KEYS = ("workId", "work_id", "id", "queueId", "queue_id")


@dataclass
class Candidate:
    key: str
    work_id: str
    title: str
    author: str
    url: str
    status: str
    rights: str
    rights_note: str
    explicit_copy_ok: bool
    origin: str
    kind: str = "work"


@dataclass
class Outcome:
    key: str
    work_id: str
    title: str
    author: str
    source_url: str
    status: str
    reason: str = ""
    local_path: str = ""
    size: int = 0
    sha256: str = ""
    resolved_identifier: str = ""
    resolved_title: str = ""
    rights_evidence: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def text(v: Any) -> str:
    if isinstance(v, list):
        return " ".join(str(x) for x in v if x is not None)
    return "" if v is None else str(v)


def first_text(d: dict[str, Any], keys: Iterable[str]) -> str:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def walk(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def normalize(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.casefold().replace("’", "'").replace("ʿ", "").replace("ʾ", "")
    s = re.sub(r"[^\w\u0600-\u06ff]+", " ", s, flags=re.UNICODE)
    return " ".join(s.split())


def tokens(s: str) -> set[str]:
    return {x for x in normalize(s).split() if len(x) > 1}


def similarity(a: str, b: str) -> float:
    aa, bb = tokens(a), tokens(b)
    if not aa or not bb:
        return 0.0
    if normalize(a) == normalize(b):
        return 1.0
    return len(aa & bb) / len(aa | bb)


def stable_id(title: str, author: str, url: str) -> str:
    return "recovered-" + hashlib.sha1(f"{title}|{author}|{url}".encode("utf-8")).hexdigest()[:12]


def safe_slug(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s or "").strip("-._")
    return (s[:90] or "recovered-work")


def all_urls(d: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for k in URL_KEYS:
        v = d.get(k)
        vals = v if isinstance(v, list) else [v]
        for x in vals:
            if isinstance(x, str) and x.startswith(("http://", "https://")) and x not in out:
                out.append(x)
    return out


def unresolved(status: str) -> bool:
    s = status.casefold()
    return any(w in s for w in UNRESOLVED_WORDS)


def rights_text_safe(rights: str, note: str = "") -> bool:
    s = f"{rights} {note}".casefold()
    if any(w in s for w in RESTRICTED_RIGHTS_WORDS):
        return False
    return any(w in s for w in SAFE_RIGHTS_WORDS)


def published_work_ids() -> set[str]:
    data = load_json(INDEX)
    out: set[str] = set()
    if isinstance(data, dict):
        for item in data.get("items", []):
            if isinstance(item, dict) and item.get("publishedAsset") is True and item.get("workId"):
                out.add(str(item["workId"]))
    return out


def collect_compact_catalogue() -> list[Candidate]:
    out: list[Candidate] = []
    local = published_work_ids()
    for path in sorted(CATALOGUE.glob("chunk-*.json")):
        data = load_json(path)
        rows = data.get("items", []) if isinstance(data, dict) else []
        for row in rows:
            if not isinstance(row, list) or len(row) < 15:
                continue
            # Compact fallback schema used by the 14 professional catalogue chunks:
            # id, entryNumber, category, titleAr, titleRomanized, authorAr,
            # authorRomanized, kind, rightsStatus, verificationStatus,
            # availabilityStatus, sourceType, exact/discovery URL, publicNotes, ingestionStatus.
            work_id = text(row[0]).strip()
            if not work_id or work_id in local:
                continue
            title = text(row[3]).strip() or text(row[4]).strip()
            author = text(row[5]).strip() or text(row[6]).strip()
            kind = text(row[7]).strip() or "work"
            rights = text(row[8]).strip()
            availability = text(row[10]).strip()
            url = text(row[12]).strip()
            note = text(row[13]).strip()
            status = text(row[14]).strip() or availability
            if not unresolved(status) and not unresolved(availability):
                continue
            key = hashlib.sha1(f"catalogue|{work_id}|{url}".encode("utf-8")).hexdigest()
            out.append(Candidate(
                key=key, work_id=work_id, title=title, author=author, url=url,
                status=status, rights=rights, rights_note=note,
                explicit_copy_ok=rights_text_safe(rights, note),
                origin=str(path.relative_to(ROOT)), kind=kind,
            ))
    return out


def collect_generic_json() -> list[Candidate]:
    out: list[Candidate] = []
    local = published_work_ids()
    skip = {INDEX, QUEUE, REPORT}
    for path in sorted(DATA.rglob("*.json")):
        if path in skip or path.parent == CATALOGUE:
            continue
        data = load_json(path)
        if data is None:
            continue
        for d in walk(data):
            title = first_text(d, TITLE_KEYS)
            if not title:
                continue
            work_id = first_text(d, ID_KEYS)
            if work_id and work_id in local:
                continue
            status = " ".join(first_text(d, (k,)) for k in STATUS_KEYS if first_text(d, (k,))).strip()
            urls = all_urls(d)
            explicit_manifest = "recovery" in path.parts
            if not explicit_manifest and not unresolved(status):
                continue
            rights = first_text(d, ("rightsStatus", "rights_status", "rights", "license", "licence"))
            note = first_text(d, ("publicNotes", "public_notes", "rightsNote", "rights_note", "notes"))
            copy_ok = d.get("eligibleForFullTextCopy") is True or d.get("eligible_for_full_text_copy") is True or rights_text_safe(rights, note)
            author = first_text(d, AUTHOR_KEYS)
            if not urls:
                urls = [""]
            for url in urls:
                wid = work_id or stable_id(title, author, url)
                key = hashlib.sha1(f"json|{path}|{wid}|{url}".encode("utf-8")).hexdigest()
                out.append(Candidate(key, wid, title, author, url, status, rights, note, copy_ok, str(path.relative_to(ROOT)), first_text(d, ("kind", "type")) or "work"))
    return out


def collect_candidates() -> list[Candidate]:
    merged: dict[tuple[str, str], Candidate] = {}
    for c in collect_compact_catalogue() + collect_generic_json():
        k = (c.work_id, c.url)
        old = merged.get(k)
        if old is None or (c.explicit_copy_ok and not old.explicit_copy_ok):
            merged[k] = c
    return list(merged.values())


def http_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def archive_identifier(url: str) -> str:
    try:
        u = urllib.parse.urlparse(url)
        if u.netloc.endswith("archive.org"):
            m = re.search(r"/details/([^/?#]+)", u.path)
            if m:
                return urllib.parse.unquote(m.group(1))
    except Exception:
        pass
    return ""


def archive_query_from_url(url: str) -> str:
    try:
        u = urllib.parse.urlparse(url)
        if u.netloc.endswith("archive.org") and u.path.startswith("/search"):
            return urllib.parse.parse_qs(u.query).get("query", [""])[0]
    except Exception:
        pass
    return ""


def archive_search(title: str, author: str, hinted: str = "") -> tuple[str, str, float, float]:
    q = hinted.strip() or " ".join(x for x in (title, author) if x)
    if not q:
        return "", "", 0.0, 0.0
    params = [
        ("q", q), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "creator"),
        ("rows", "10"), ("page", "1"), ("output", "json"), ("sort[]", "downloads desc"),
    ]
    data = http_json(ARCHIVE_SEARCH + "?" + urllib.parse.urlencode(params))
    docs = data.get("response", {}).get("docs", []) if isinstance(data, dict) else []
    scores: list[tuple[float, str, str]] = []
    for d in docs:
        ident = text(d.get("identifier")).strip()
        dt = text(d.get("title")).strip()
        creator = text(d.get("creator")).strip()
        ts = similarity(title or q, dt)
        ascore = similarity(author, creator) if author else 0.0
        score = ts * 0.88 + ascore * 0.12
        if title and normalize(title) == normalize(dt):
            score = max(score, 0.97)
        if ident:
            scores.append((score, ident, dt))
    scores.sort(reverse=True)
    if not scores:
        return "", "", 0.0, 0.0
    second = scores[1][0] if len(scores) > 1 else 0.0
    return scores[0][1], scores[0][2], scores[0][0], second


def year_from_metadata(md: dict[str, Any]) -> int | None:
    for key in ("date", "year", "publicationdate"):
        m = re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", text(md.get(key)))
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass
    return None


def archive_rights_ok(meta: dict[str, Any], candidate: Candidate) -> tuple[bool, str]:
    md = meta.get("metadata", {}) if isinstance(meta, dict) else {}
    if str(md.get("is_dark", "")).casefold() in ("true", "1", "yes"):
        return False, "Archive item is access-restricted"
    licence = text(md.get("licenseurl"))
    rights = text(md.get("rights"))
    combined = f"{licence} {rights}".casefold()
    if any(w in combined for w in ("publicdomain", "public domain", "creativecommons.org/publicdomain", "/licenses/by/", "/licenses/by-sa/", "cc0", "no known copyright restrictions")):
        return True, f"archive metadata: {licence or rights}"[:300]
    if candidate.explicit_copy_ok:
        return True, f"catalogue rights: {candidate.rights or candidate.rights_note}"[:300]
    year = year_from_metadata(md)
    if year is not None and year <= 1930 and not any(w in combined for w in ("copyright", "all rights reserved", "restricted")):
        return True, f"archive publication year {year} (public-domain cutoff <= 1930)"
    return False, "No redistribution-safe rights evidence"


def choose_archive_file(meta: dict[str, Any]) -> tuple[str, str, int]:
    files = meta.get("files", []) if isinstance(meta, dict) else []
    choices: list[tuple[int, int, str]] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        name = text(f.get("name")).strip()
        if not name or name.endswith(("_meta.xml", "_files.xml", "_reviews.xml")):
            continue
        try:
            size = int(f.get("size") or 0)
        except Exception:
            size = 0
        if size and size >= MAX_FILE_BYTES:
            continue
        low = name.casefold()
        fmt = text(f.get("format")).casefold()
        if low.endswith("_djvu.txt") or low.endswith(".txt") or "full text" in fmt:
            rank = 0
        elif low.endswith(".epub") or "epub" in fmt:
            rank = 1
        elif low.endswith(".pdf") or "pdf" in fmt:
            rank = 2
        elif low.endswith((".html", ".htm")):
            rank = 3
        else:
            continue
        if size and size < 1024:
            continue
        choices.append((rank, size or MAX_FILE_BYTES - 1, name))
    if not choices:
        return "", "", 0
    choices.sort(key=lambda x: (x[0], x[1]))
    _, size, name = choices[0]
    return name, name, 0 if size == MAX_FILE_BYTES - 1 else size


def extension(url: str) -> str:
    p = urllib.parse.urlparse(url).path.casefold()
    if p.endswith("_djvu.txt"):
        return ".txt"
    for ext in (".txt", ".epub", ".pdf", ".html", ".htm", ".xml", ".json"):
        if p.endswith(ext):
            return ext
    return ".bin"


def download(url: str, dest: Path) -> tuple[int, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    h = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r, tmp.open("wb") as f:
            declared = r.headers.get("Content-Length")
            if declared and int(declared) >= MAX_FILE_BYTES:
                raise ValueError(f"oversized:{declared}")
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total >= MAX_FILE_BYTES:
                    raise ValueError(f"oversized:{total}")
                h.update(chunk)
                f.write(chunk)
        if total < 512:
            raise ValueError(f"payload-too-small:{total}")
        tmp.replace(dest)
        return total, h.hexdigest()
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def save(candidate: Candidate, url: str, rights_evidence: str, ident: str = "", resolved_title: str = "") -> Outcome:
    ext = extension(url)
    seed = hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]
    rel = Path("library") / "works" / safe_slug(candidate.work_id) / "editions" / f"recovery-{seed}" / f"original{ext}"
    dest = ROOT / rel
    if dest.exists() and dest.stat().st_size > 0:
        raw = dest.read_bytes()
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "already-downloaded", local_path="/" + rel.as_posix(), size=len(raw), sha256=hashlib.sha256(raw).hexdigest(), resolved_identifier=ident, resolved_title=resolved_title, rights_evidence=rights_evidence)
    try:
        size, sha = download(url, dest)
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "downloaded", local_path="/" + rel.as_posix(), size=size, sha256=sha, resolved_identifier=ident, resolved_title=resolved_title, rights_evidence=rights_evidence)
    except urllib.error.HTTPError as e:
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "failed", f"HTTP {e.code}", resolved_identifier=ident, resolved_title=resolved_title, rights_evidence=rights_evidence)
    except Exception as e:
        reason = str(e)
        status = "oversized" if reason.startswith("oversized:") else "failed"
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, status, reason[:300], resolved_identifier=ident, resolved_title=resolved_title, rights_evidence=rights_evidence)


def process(candidate: Candidate) -> Outcome:
    url = candidate.url.strip()
    if url:
        host = urllib.parse.urlparse(url).netloc.casefold()
        if "youtube.com" in host or "youtu.be" in host:
            return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "media-reference", "YouTube binary media not mirrored; URL retained")
        if "gutenberg.org" in host:
            if re.search(r"\.(?:txt|epub|html?|pdf)(?:$|[?#])", url, re.I) or ".txt.utf-8" in url:
                return save(candidate, url, "Project Gutenberg public-domain distribution")
        ident = archive_identifier(url)
        if ident:
            try:
                meta = http_json(ARCHIVE_META.format(identifier=urllib.parse.quote(ident, safe="")))
                ok, evidence = archive_rights_ok(meta, candidate)
                if not ok:
                    return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "rights-unverified", evidence, resolved_identifier=ident)
                name, _, _ = choose_archive_file(meta)
                if not name:
                    return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "unresolved", "No suitable sub-95MB readable file", resolved_identifier=ident, rights_evidence=evidence)
                dl = f"https://archive.org/download/{urllib.parse.quote(ident)}/{urllib.parse.quote(name)}"
                return save(candidate, dl, evidence, ident, candidate.title)
            except Exception as e:
                return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "failed", f"archive metadata: {e}"[:300], resolved_identifier=ident)
        hinted = archive_query_from_url(url)
        if hinted:
            return resolve_archive_search(candidate, hinted)
        # Non-Archive source pages are not blindly scraped; use them as discovery hints and
        # search Archive.org for a rights-verifiable manifestation of the same work.
        return resolve_archive_search(candidate, "")
    return resolve_archive_search(candidate, "")


def resolve_archive_search(candidate: Candidate, hinted: str) -> Outcome:
    try:
        ident, rt, score, second = archive_search(candidate.title, candidate.author, hinted)
        if not ident or score < 0.70 or (second and score - second < 0.08 and score < 0.93):
            return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, candidate.url, "ambiguous", f"archive score={score:.3f}, second={second:.3f}", resolved_identifier=ident, resolved_title=rt)
        meta = http_json(ARCHIVE_META.format(identifier=urllib.parse.quote(ident, safe="")))
        ok, evidence = archive_rights_ok(meta, candidate)
        if not ok:
            return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, candidate.url, "rights-unverified", evidence, resolved_identifier=ident, resolved_title=rt)
        name, _, _ = choose_archive_file(meta)
        if not name:
            return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, candidate.url, "unresolved", "No suitable sub-95MB readable file", resolved_identifier=ident, resolved_title=rt, rights_evidence=evidence)
        dl = f"https://archive.org/download/{urllib.parse.quote(ident)}/{urllib.parse.quote(name)}"
        return save(candidate, dl, evidence, ident, rt)
    except Exception as e:
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, candidate.url, "failed", f"archive search: {e}"[:300])


def update_index(outcomes: list[Outcome]) -> None:
    data = load_json(INDEX)
    if not isinstance(data, dict):
        data = {"schema": "ingested-library-v2", "items": []}
    items = data.get("items")
    if not isinstance(items, list):
        items = []
    by_url = {str(i.get("localUrl")): i for i in items if isinstance(i, dict) and i.get("localUrl")}
    for o in outcomes:
        if o.status not in ("downloaded", "already-downloaded") or not o.local_path:
            continue
        fmt = Path(o.local_path).suffix.casefold().lstrip(".") or "bin"
        mime = {"txt":"text/plain","pdf":"application/pdf","epub":"application/epub+zip","html":"text/html","htm":"text/html","xml":"application/xml","json":"application/json"}.get(fmt, "application/octet-stream")
        rec = {
            "id": f"{o.work_id}:recovery-{o.sha256[:12]}", "workId": o.work_id,
            "editionId": f"recovery-{o.sha256[:12]}", "titleOriginal": o.title,
            "author": o.author, "language": "", "subjects": ["المصادر والدراسات"],
            "siteSections": ["المصادر والدراسات"], "format": fmt, "mimeType": mime,
            "size": o.size, "sha256": o.sha256, "localUrl": o.local_path,
            "readerUrl": o.local_path, "sourceUrl": o.source_url,
            "archiveIdentifier": o.resolved_identifier or None, "rightsEvidence": o.rights_evidence,
            "capabilities": {"readable": fmt in ("txt","pdf","epub","html","htm"), "searchable": fmt in ("txt","html","htm"), "listenable": fmt in ("txt","html","htm"), "watchable": False},
            "searchMode": "fulltext-browser" if fmt in ("txt","html","htm") else "reader-search",
            "listenMode": "browser-tts" if fmt in ("txt","html","htm") else "none",
            "watchMode": "none", "publishedAsset": True, "recoveryStatus": "recovered",
            "recoveredAt": now_iso(),
        }
        if o.local_path in by_url:
            by_url[o.local_path].update(rec)
        else:
            items.append(rec)
            by_url[o.local_path] = rec
    data["items"] = items
    data["count"] = len(items)
    data["generatedAt"] = now_iso()
    INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    RECOVERY.mkdir(parents=True, exist_ok=True)
    candidates = collect_candidates()
    QUEUE.write_text(json.dumps({"schema":"all-recovery-queue-v2","generatedAt":now_iso(),"count":len(candidates),"items":[asdict(c) for c in candidates]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    outcomes: list[Outcome] = []
    downloaded = 0
    total_bytes = 0
    for i, c in enumerate(candidates, 1):
        if downloaded >= MAX_DOWNLOADS or total_bytes >= MAX_TOTAL_BYTES:
            outcomes.append(Outcome(c.key, c.work_id, c.title, c.author, c.url, "deferred", "run cap reached"))
            continue
        o = process(c)
        outcomes.append(o)
        if o.status in ("downloaded", "already-downloaded"):
            downloaded += 1
            total_bytes += int(o.size or 0)
        if i % 20 == 0:
            print(f"processed {i}/{len(candidates)} downloaded={downloaded} bytes={total_bytes}", flush=True)
        time.sleep(0.08)

    update_index(outcomes)
    counts: dict[str, int] = {}
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
    report = {
        "schema": "all-recovery-report-v2", "generatedAt": now_iso(),
        "candidateCount": len(candidates), "counts": counts,
        "downloadedBytes": total_bytes, "maxFileBytes": MAX_FILE_BYTES,
        "maxTotalBytes": MAX_TOTAL_BYTES, "items": [asdict(o) for o in outcomes],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidateCount": len(candidates), "counts": counts, "downloadedBytes": total_bytes}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
