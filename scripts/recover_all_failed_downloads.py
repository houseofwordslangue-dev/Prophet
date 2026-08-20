#!/usr/bin/env python3
"""Recover every verifiable public asset referenced by unresolved project catalogue records.

The resolver is deliberately conservative: it downloads exact direct URLs and high-confidence
Archive.org matches, records ambiguous/restricted/oversized records, and never marks an item
as locally available unless a real asset exists in library/works.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
LIBRARY = ROOT / "library" / "works"
RECOVERY = DATA / "recovery"
REPORT = RECOVERY / "all_recovery_report.json"
QUEUE = RECOVERY / "all_recovery_queue.json"
INDEX = DATA / "ingested_library.json"

MAX_FILE_BYTES = int(os.getenv("RECOVERY_MAX_FILE_BYTES", str(95 * 1024 * 1024)))
MAX_DOWNLOADS = int(os.getenv("RECOVERY_MAX_DOWNLOADS", "2000"))
TIMEOUT = int(os.getenv("RECOVERY_HTTP_TIMEOUT", "45"))
USER_AGENT = "ProphetLibraryRecovery/1.0 (+https://github.com/houseofwordslangue-dev/Prophet)"
ARCHIVE_SEARCH = "https://archive.org/advancedsearch.php"
ARCHIVE_META = "https://archive.org/metadata/{identifier}"

STATUS_WORDS = ("awaiting", "unresolved", "failed", "discovered", "missing", "undownloaded", "not-mirrored", "not_mirrored")
URL_KEYS = ("sourceUrl", "source_url", "downloadUrl", "download_url", "directUrl", "direct_url", "url", "manualLink", "manual_link", "sourcePage", "source_page", "archiveUrl", "archive_url")
TITLE_KEYS = ("titleOriginal", "title", "name", "work", "label", "titleAr", "titleEn", "titleFr")
AUTHOR_KEYS = ("author", "creator", "editor")
ID_KEYS = ("workId", "work_id", "id", "queueId", "queue_id")

@dataclass
class Candidate:
    key: str
    work_id: str
    title: str
    author: str
    url: str
    status: str
    origin: str

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


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def walk(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def first_text(d: dict[str, Any], keys: tuple[str, ...]) -> str:
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def all_urls(d: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for k in URL_KEYS:
        v = d.get(k)
        vals = v if isinstance(v, list) else [v]
        for x in vals:
            if isinstance(x, str) and x.startswith(("http://", "https://")) and x not in out:
                out.append(x)
    return out


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
    return len(aa & bb) / len(aa | bb)


def safe_slug(s: str, fallback: str = "work") -> str:
    s = normalize(s)
    s = re.sub(r"[^\w\u0600-\u06ff]+", "-", s).strip("-")
    return (s[:80] or fallback)


def stable_id(title: str, author: str, url: str) -> str:
    digest = hashlib.sha1(f"{title}|{author}|{url}".encode("utf-8")).hexdigest()[:12]
    return f"recovered-{digest}"


def http_json(url: str) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def head_or_get_size(url: str) -> tuple[int, str]:
    for method in ("HEAD", "GET"):
        try:
            req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"} if method == "GET" else {"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                size = r.headers.get("Content-Length")
                ctype = r.headers.get("Content-Type", "")
                if size:
                    n = int(size)
                    if method == "GET" and r.status == 206:
                        cr = r.headers.get("Content-Range", "")
                        m = re.search(r"/(\d+)$", cr)
                        if m:
                            n = int(m.group(1))
                    return n, ctype
                return 0, ctype
        except Exception:
            continue
    return 0, ""


def download(url: str, dest: Path) -> tuple[int, str]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    h = hashlib.sha256()
    total = 0
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r, tmp.open("wb") as f:
            declared = r.headers.get("Content-Length")
            if declared and int(declared) > MAX_FILE_BYTES:
                raise ValueError(f"oversized:{declared}")
            while True:
                chunk = r.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_FILE_BYTES:
                    raise ValueError(f"oversized:{total}")
                h.update(chunk)
                f.write(chunk)
        tmp.replace(dest)
        return total, h.hexdigest()
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def collect_candidates() -> list[Candidate]:
    found: dict[str, Candidate] = {}
    for path in sorted(DATA.rglob("*.json")):
        if path == REPORT:
            continue
        data = load_json(path)
        if data is None:
            continue
        for d in walk(data):
            status = first_text(d, ("status", "state", "queueStatus", "queue_status", "recordedState", "recorded_state"))
            title = first_text(d, TITLE_KEYS)
            author = first_text(d, AUTHOR_KEYS)
            urls = all_urls(d)
            unresolved = any(w in status.casefold() for w in STATUS_WORDS)
            published = d.get("publishedAsset") is True or d.get("published") is True
            local = first_text(d, ("localUrl", "local_url", "localPath", "local_path"))
            if not title:
                continue
            # Include explicit recovery manifests even if status is absent; otherwise unresolved records only.
            explicit = "recovery" in path.parts
            if not explicit and not unresolved:
                continue
            if published and local:
                continue
            work_id = first_text(d, ID_KEYS)
            if not urls:
                # Search Archive.org later using title/author.
                urls = [""]
            for url in urls:
                key = hashlib.sha1(f"{title}|{author}|{url}".encode("utf-8")).hexdigest()
                found[key] = Candidate(key, work_id or stable_id(title, author, url), title, author, url, status, str(path.relative_to(ROOT)))

    # Also discover unresolved rows in retained markdown recovery files if present in the repository.
    link_re = re.compile(r"\[[^\]]*\]\((https?://[^)]+)\)")
    for path in sorted(ROOT.rglob("FAILED_DOWNLOADS_MANUAL*.md")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if not line.startswith("|") or "---" in line:
                continue
            parts = [x.strip().strip("`") for x in line.strip().strip("|").split("|")]
            urls = link_re.findall(line)
            if not urls or len(parts) < 2:
                continue
            # Prefer the first human-readable table column after the numeric row index.
            title = re.sub(r"\[[^\]]*\]\([^)]+\)", "", parts[1]).strip(" -—") or parts[1]
            author = parts[2] if len(parts) > 2 else ""
            for url in urls:
                key = hashlib.sha1(f"md|{path}|{lineno}|{url}".encode()).hexdigest()
                found.setdefault(key, Candidate(key, stable_id(title, author, url), title, author, url, "manual-recovery", f"{path.relative_to(ROOT)}:{lineno}"))
    return list(found.values())


def archive_identifier_from_url(url: str) -> str:
    try:
        u = urllib.parse.urlparse(url)
        if u.netloc.endswith("archive.org"):
            m = re.search(r"/details/([^/?#]+)", u.path)
            if m:
                return urllib.parse.unquote(m.group(1))
    except Exception:
        pass
    return ""


def archive_search_query_from_url(url: str) -> str:
    try:
        u = urllib.parse.urlparse(url)
        if u.netloc.endswith("archive.org") and u.path.startswith("/search"):
            return urllib.parse.parse_qs(u.query).get("query", [""])[0]
    except Exception:
        pass
    return ""


def archive_search(title: str, author: str, hinted_query: str = "") -> tuple[str, str, float, float]:
    phrase = hinted_query.strip() or " ".join(x for x in (title, author) if x)
    if not phrase:
        return "", "", 0.0, 0.0
    params = [
        ("q", phrase), ("fl[]", "identifier"), ("fl[]", "title"), ("fl[]", "creator"),
        ("rows", "10"), ("page", "1"), ("output", "json"), ("sort[]", "downloads desc")
    ]
    data = http_json(ARCHIVE_SEARCH + "?" + urllib.parse.urlencode(params))
    docs = data.get("response", {}).get("docs", []) if isinstance(data, dict) else []
    scored: list[tuple[float, str, str]] = []
    for doc in docs:
        ident = str(doc.get("identifier", ""))
        dt = doc.get("title", "")
        if isinstance(dt, list): dt = " ".join(map(str, dt))
        creator = doc.get("creator", "")
        if isinstance(creator, list): creator = " ".join(map(str, creator))
        ts = similarity(title or phrase, str(dt))
        ascore = similarity(author, str(creator)) if author else 0.0
        score = ts * 0.85 + ascore * 0.15
        # exact normalized title receives a strong boost.
        if title and normalize(title) == normalize(str(dt)):
            score = max(score, 0.96)
        scored.append((score, ident, str(dt)))
    scored.sort(reverse=True)
    if not scored:
        return "", "", 0.0, 0.0
    best = scored[0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    return best[1], best[2], best[0], second


def choose_archive_file(identifier: str) -> tuple[str, str, int, str]:
    meta = http_json(ARCHIVE_META.format(identifier=urllib.parse.quote(identifier, safe="")))
    metadata = meta.get("metadata", {}) if isinstance(meta, dict) else {}
    if str(metadata.get("is_dark", "")).lower() in ("true", "1"):
        return "", "", 0, "restricted"
    files = meta.get("files", []) if isinstance(meta, dict) else []
    choices: list[tuple[int, int, str, str]] = []
    for f in files:
        if not isinstance(f, dict):
            continue
        name = str(f.get("name", ""))
        if not name or name.endswith(("_meta.xml", "_files.xml", "_reviews.xml")):
            continue
        try: size = int(f.get("size") or 0)
        except Exception: size = 0
        if size and size > MAX_FILE_BYTES:
            continue
        low = name.casefold()
        fmt = str(f.get("format", "")).casefold()
        # Prefer useful searchable/readable derivatives; PDF is retained when text/EPUB is unavailable.
        if low.endswith(".txt") or "full text" in fmt or low.endswith("_djvu.txt"):
            rank = 0
        elif low.endswith(".epub") or "epub" in fmt:
            rank = 1
        elif low.endswith(".pdf") or "pdf" in fmt:
            rank = 2
        elif low.endswith(".html") or low.endswith(".htm"):
            rank = 3
        else:
            continue
        # Avoid tiny metadata/readme-like text artifacts.
        if size and size < 1024 and rank <= 2:
            continue
        choices.append((rank, size or MAX_FILE_BYTES, name, fmt))
    if not choices:
        return "", "", 0, "no-downloadable-file"
    choices.sort(key=lambda x: (x[0], x[1]))
    _, size, name, fmt = choices[0]
    url = f"https://archive.org/download/{urllib.parse.quote(identifier)}/{urllib.parse.quote(name)}"
    return url, name, 0 if size == MAX_FILE_BYTES else size, fmt


def extension_from(url: str, ctype: str = "") -> str:
    path = urllib.parse.urlparse(url).path.casefold()
    for ext in (".djvu.txt", ".txt", ".epub", ".pdf", ".html", ".htm", ".json", ".xml", ".mp3", ".ogg", ".m4a", ".mp4", ".webm"):
        if path.endswith(ext):
            return ".txt" if ext == ".djvu.txt" else ext
    c = ctype.casefold()
    if "text/plain" in c: return ".txt"
    if "application/pdf" in c: return ".pdf"
    if "epub" in c: return ".epub"
    if "html" in c: return ".html"
    return ".bin"


def ingest_file(candidate: Candidate, source_url: str, resolved_identifier: str = "", resolved_title: str = "") -> Outcome:
    size_hint, ctype = head_or_get_size(source_url)
    if size_hint > MAX_FILE_BYTES:
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, source_url, "oversized", f"{size_hint}>{MAX_FILE_BYTES}", resolved_identifier=resolved_identifier, resolved_title=resolved_title)
    ext = extension_from(source_url, ctype)
    work_id = candidate.work_id or stable_id(candidate.title, candidate.author, source_url)
    edition_seed = hashlib.sha1(source_url.encode()).hexdigest()[:12]
    rel = Path("library") / "works" / safe_slug(work_id, "recovered") / "editions" / f"ed-{edition_seed}" / f"original{ext}"
    dest = ROOT / rel
    if dest.exists() and dest.stat().st_size > 0:
        h = hashlib.sha256(dest.read_bytes()).hexdigest()
        return Outcome(candidate.key, work_id, candidate.title, candidate.author, source_url, "already-downloaded", local_path="/" + rel.as_posix(), size=dest.stat().st_size, sha256=h, resolved_identifier=resolved_identifier, resolved_title=resolved_title)
    try:
        size, sha = download(source_url, dest)
    except urllib.error.HTTPError as e:
        return Outcome(candidate.key, work_id, candidate.title, candidate.author, source_url, "failed", f"HTTP {e.code}", resolved_identifier=resolved_identifier, resolved_title=resolved_title)
    except Exception as e:
        reason = str(e)
        status = "oversized" if reason.startswith("oversized:") else "failed"
        return Outcome(candidate.key, work_id, candidate.title, candidate.author, source_url, status, reason[:300], resolved_identifier=resolved_identifier, resolved_title=resolved_title)
    return Outcome(candidate.key, work_id, candidate.title, candidate.author, source_url, "downloaded", local_path="/" + rel.as_posix(), size=size, sha256=sha, resolved_identifier=resolved_identifier, resolved_title=resolved_title)


def process(candidate: Candidate) -> Outcome:
    url = candidate.url.strip()
    if url:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.casefold()
        if "youtube.com" in host or "youtu.be" in host:
            return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "media-metadata-queued", "handled by yt-dlp metadata/subtitle recovery step")
        ident = archive_identifier_from_url(url)
        if ident:
            try:
                dl, name, _, reason = choose_archive_file(ident)
                if not dl:
                    return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "unresolved", reason, resolved_identifier=ident)
                return ingest_file(candidate, dl, ident, candidate.title)
            except Exception as e:
                return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "failed", f"archive metadata: {e}"[:300], resolved_identifier=ident)
        hinted = archive_search_query_from_url(url)
        if hinted:
            try:
                ident, rt, score, second = archive_search(candidate.title, candidate.author, hinted)
                if not ident or score < 0.58 or (second and score - second < 0.08 and score < 0.90):
                    return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "ambiguous", f"archive match score={score:.3f}, second={second:.3f}", resolved_identifier=ident, resolved_title=rt)
                dl, _, _, reason = choose_archive_file(ident)
                if not dl:
                    return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "unresolved", reason, resolved_identifier=ident, resolved_title=rt)
                return ingest_file(candidate, dl, ident, rt)
            except Exception as e:
                return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "failed", f"archive search: {e}"[:300])
        # Direct file-like public HTTP URL.
        if re.search(r"\.(?:txt|pdf|epub|html?|xml|json)(?:$|[?#])", url, re.I) or "gutenberg.org/ebooks/" in url:
            return ingest_file(candidate, url)
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, url, "unresolved", "non-file source page requires source-specific resolver")

    # No retained URL: attempt conservative Archive.org title/author resolution.
    try:
        ident, rt, score, second = archive_search(candidate.title, candidate.author)
        if not ident or score < 0.68 or (second and score - second < 0.10 and score < 0.92):
            return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, "", "ambiguous", f"archive match score={score:.3f}, second={second:.3f}", resolved_identifier=ident, resolved_title=rt)
        dl, _, _, reason = choose_archive_file(ident)
        if not dl:
            return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, "", "unresolved", reason, resolved_identifier=ident, resolved_title=rt)
        return ingest_file(candidate, dl, ident, rt)
    except Exception as e:
        return Outcome(candidate.key, candidate.work_id, candidate.title, candidate.author, "", "failed", f"archive search: {e}"[:300])


def recover_youtube(candidates: list[Candidate], outcomes: list[Outcome]) -> None:
    yt = [c for c in candidates if c.url and ("youtube.com" in c.url or "youtu.be" in c.url)]
    if not yt:
        return
    if shutil.which("yt-dlp") is None:
        return
    outroot = RECOVERY / "media_metadata"
    outroot.mkdir(parents=True, exist_ok=True)
    for c in yt:
        # Save metadata/subtitles only. Binary video/audio is intentionally not committed to avoid
        # GitHub hard limits and rights ambiguity; exact URLs remain in the report/site catalogue.
        folder = outroot / safe_slug(c.work_id or c.title, "media")
        folder.mkdir(parents=True, exist_ok=True)
        cmd = [
            "yt-dlp", "--skip-download", "--write-info-json", "--write-subs", "--write-auto-subs",
            "--sub-langs", "all,-live_chat", "--convert-subs", "vtt", "--ignore-errors",
            "--no-overwrites", "--playlist-end", os.getenv("RECOVERY_YOUTUBE_PLAYLIST_END", "1000"),
            "-o", str(folder / "%(id)s.%(ext)s"), c.url,
        ]
        try:
            p = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=60 * 60)
            (folder / "yt-dlp.log").write_text(p.stdout[-20000:], encoding="utf-8", errors="replace")
        except Exception as e:
            (folder / "yt-dlp.log").write_text(str(e), encoding="utf-8")


def update_ingested_index(outcomes: list[Outcome]) -> None:
    data = load_json(INDEX)
    if not isinstance(data, dict):
        data = {"schema": "ingested-library-v2", "items": []}
    items = data.get("items")
    if not isinstance(items, list):
        items = []
    by_path = {str(i.get("localUrl")): i for i in items if isinstance(i, dict) and i.get("localUrl")}
    for o in outcomes:
        if o.status not in ("downloaded", "already-downloaded") or not o.local_path:
            continue
        ext = Path(o.local_path).suffix.casefold()
        fmt = ext.lstrip(".") or "bin"
        mime = {"txt":"text/plain","pdf":"application/pdf","epub":"application/epub+zip","html":"text/html","htm":"text/html","json":"application/json","xml":"application/xml"}.get(fmt, "application/octet-stream")
        record = {
            "id": f"{o.work_id}:recovery-{o.sha256[:12]}",
            "workId": o.work_id,
            "editionId": f"recovery-{o.sha256[:12]}",
            "titleOriginal": o.title,
            "author": o.author,
            "language": "",
            "subjects": ["المصادر والدراسات"],
            "siteSections": ["المصادر والدراسات"],
            "format": fmt,
            "mimeType": mime,
            "size": o.size,
            "sha256": o.sha256,
            "localUrl": o.local_path,
            "readerUrl": o.local_path,
            "sourceUrl": o.source_url,
            "archiveIdentifier": o.resolved_identifier or None,
            "capabilities": {"readable": fmt in ("txt","pdf","epub","html","htm"), "searchable": fmt in ("txt","html","htm"), "listenable": fmt in ("txt","html","htm"), "watchable": False},
            "searchMode": "fulltext-browser" if fmt in ("txt","html","htm") else "reader-search",
            "listenMode": "browser-tts" if fmt in ("txt","html","htm") else "none",
            "watchMode": "none",
            "publishedAsset": True,
            "recoveredAt": now_iso(),
        }
        if o.local_path in by_path:
            by_path[o.local_path].update(record)
        else:
            items.append(record)
            by_path[o.local_path] = record
    data["items"] = items
    data["count"] = len(items)
    data["generatedAt"] = now_iso()
    INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    RECOVERY.mkdir(parents=True, exist_ok=True)
    candidates = collect_candidates()
    QUEUE.write_text(json.dumps({"schema":"all-recovery-queue-v1","generatedAt":now_iso(),"count":len(candidates),"items":[asdict(c) for c in candidates]}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    prior = load_json(REPORT)
    prior_map: dict[str, dict[str, Any]] = {}
    if isinstance(prior, dict):
        for x in prior.get("items", []):
            if isinstance(x, dict) and x.get("key"):
                prior_map[str(x["key"])] = x

    outcomes: list[Outcome] = []
    download_count = 0
    for idx, c in enumerate(candidates, 1):
        old = prior_map.get(c.key)
        if old and old.get("status") in ("downloaded", "already-downloaded") and old.get("local_path"):
            local = ROOT / str(old["local_path"]).lstrip("/")
            if local.exists():
                outcomes.append(Outcome(**{k: old.get(k, "") for k in Outcome.__dataclass_fields__.keys()}))
                continue
        if download_count >= MAX_DOWNLOADS:
            outcomes.append(Outcome(c.key, c.work_id, c.title, c.author, c.url, "deferred", f"run download cap {MAX_DOWNLOADS}"))
            continue
        o = process(c)
        outcomes.append(o)
        if o.status == "downloaded":
            download_count += 1
        if idx % 25 == 0:
            print(f"processed {idx}/{len(candidates)}; downloaded={download_count}", flush=True)
        time.sleep(0.05)

    recover_youtube(candidates, outcomes)
    update_ingested_index(outcomes)
    counts: dict[str, int] = {}
    total_bytes = 0
    for o in outcomes:
        counts[o.status] = counts.get(o.status, 0) + 1
        if o.status in ("downloaded", "already-downloaded"):
            total_bytes += int(o.size or 0)
    REPORT.write_text(json.dumps({
        "schema":"all-recovery-report-v1", "generatedAt":now_iso(), "candidateCount":len(candidates),
        "counts":counts, "downloadedBytes":total_bytes, "maxFileBytes":MAX_FILE_BYTES,
        "items":[asdict(o) for o in outcomes]
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidateCount":len(candidates),"counts":counts,"downloadedBytes":total_bytes}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
