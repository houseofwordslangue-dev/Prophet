#!/usr/bin/env python3
from __future__ import annotations

import json
import mimetypes
import os
import re
import subprocess
import sys
import threading
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "imported_media.json"
EPUB_INDEX = ROOT / "data" / "generated_epubs.json"
CACHE = ROOT / "media-cache"
CACHE.mkdir(parents=True, exist_ok=True)
HOST = os.getenv("PM_HOST", "127.0.0.1")
PORT = int(os.getenv("PM_PORT", "8080"))
SYNC_ON_START = os.getenv("PM_MEDIA_SYNC_ON_START", "1") == "1"
EPUB_ON_START = os.getenv("PM_EPUB_CONVERT_ON_START", "1") == "1"
MAX_SYNC = int(os.getenv("PM_MEDIA_MAX_PER_SOURCE", "350"))
CACHE_ENABLED = os.getenv("PM_MEDIA_CACHE", "1") == "1"

_MEDIA_LOCK = threading.Lock()
_MEDIA_BY_ID: dict[str, dict] = {}
_CACHE_JOBS: set[str] = set()


def _load_catalogue() -> None:
    global _MEDIA_BY_ID
    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
        items = data.get("items", [])
    except Exception:
        items = []
    with _MEDIA_LOCK:
        _MEDIA_BY_ID = {str(x.get("id")): x for x in items if x.get("id")}


def _sync_catalogue() -> None:
    if not SYNC_ON_START:
        _load_catalogue()
        return
    try:
        from scripts.sync_media import run_expanded_sync
        run_expanded_sync(MAX_SYNC)
    except Exception as exc:
        print("media sync warning:", exc)
    _load_catalogue()


def _publish_epubs() -> None:
    if not EPUB_ON_START:
        return
    script = ROOT / "scripts" / "convert_all_epub.py"
    if not script.exists():
        return
    try:
        cp = subprocess.run([sys.executable, str(script)], cwd=str(ROOT), text=True, capture_output=True, timeout=3600)
        if cp.stdout:
            print(cp.stdout[-20000:])
        if cp.returncode and cp.stderr:
            print("EPUB publication warning:", cp.stderr[-12000:])
    except Exception as exc:
        print("EPUB publication warning:", exc)


def _start_epub_publication() -> None:
    if EPUB_ON_START:
        threading.Thread(target=_publish_epubs, daemon=True, name="epub-publisher").start()


def _epub_status() -> dict:
    try:
        d = json.loads(EPUB_INDEX.read_text(encoding="utf-8"))
        return {"ok": True, "count": int(d.get("count") or 0), "processedThisRun": int(d.get("processedThisRun") or 0), "failedThisRun": d.get("failedThisRun") or [], "generatedAt": d.get("generatedAt")}
    except Exception as exc:
        return {"ok": False, "count": 0, "error": str(exc)}


def _safe_id(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:180]


def _cached_file(item_id: str) -> Path | None:
    stem = _safe_id(item_id)
    for p in CACHE.glob(stem + ".*"):
        if p.is_file() and not p.name.endswith((".part", ".ytdl")):
            return p
    return None


def _medium(item: dict) -> str:
    m = str(item.get("medium") or "").strip().lower()
    if m:
        return m
    if item.get("kind") == "audio":
        return "audio"
    cat = str(item.get("category") or "").lower()
    if cat in {"podcast", "research", "documentary", "audio", "video", "lecture"}:
        return cat
    return "lecture" if cat else "video"


def _yt_info(item: dict) -> dict:
    import yt_dlp
    url = str(item.get("url") or item.get("embed") or "")
    if not url:
        raise RuntimeError("media source URL missing")
    audio_only = _medium(item) in {"audio", "podcast"}
    fmt = "bestaudio/best" if audio_only else "best[ext=mp4][protocol^=http]/best[protocol^=http]/best"
    opts = {
        "quiet": True,
        "skip_download": True,
        "noplaylist": True,
        "format": fmt,
        "socket_timeout": 30,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info:
        raise RuntimeError("media metadata unavailable")
    return info


def _remote_url(item: dict) -> tuple[str, str]:
    direct = str(item.get("audio") or item.get("video") or "")
    if direct and not any(h in direct for h in ("youtube.com", "youtu.be", "youtube-nocookie.com")):
        return direct, ""
    info = _yt_info(item)
    url = str(info.get("url") or "")
    if not url:
        raise RuntimeError("stream URL unavailable")
    return url, str(info.get("http_headers", {}).get("User-Agent") or "")


def _cache_item(item: dict) -> None:
    if not CACHE_ENABLED:
        return
    item_id = str(item.get("id") or "")
    if not item_id or _cached_file(item_id):
        return
    with _MEDIA_LOCK:
        if item_id in _CACHE_JOBS:
            return
        _CACHE_JOBS.add(item_id)
    try:
        import yt_dlp
        audio_only = _medium(item) in {"audio", "podcast"}
        stem = str(CACHE / _safe_id(item_id))
        opts = {
            "quiet": True,
            "noplaylist": True,
            "outtmpl": stem + ".%(ext)s",
            "socket_timeout": 30,
            "retries": 3,
            "fragment_retries": 3,
            "format": "bestaudio/best" if audio_only else "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "merge_output_format": "mp4" if not audio_only else None,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([str(item.get("url") or item.get("embed") or "")])
    except Exception as exc:
        print("cache warning", item_id, exc)
    finally:
        with _MEDIA_LOCK:
            _CACHE_JOBS.discard(item_id)


def _start_cache(item: dict) -> None:
    threading.Thread(target=_cache_item, args=(item,), daemon=True, name="media-cache").start()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "public, max-age=300")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/ready":
            return self._json({"ok": True, "mediaItems": len(_MEDIA_BY_ID), "epubs": _epub_status().get("count", 0)})
        if parsed.path == "/api/epub/status":
            return self._json(_epub_status())
        if parsed.path == "/api/media/status":
            counts = {k: 0 for k in ("video", "lecture", "podcast", "research", "documentary", "audio")}
            with _MEDIA_LOCK:
                items = list(_MEDIA_BY_ID.values())
            for item in items:
                m = _medium(item)
                if m in counts:
                    counts[m] += 1
            return self._json({"ok": True, "total": len(items), "categories": counts})
        if parsed.path == "/api/media/stream":
            item_id = (parse_qs(parsed.query).get("id") or [""])[0]
            return self._media_stream(item_id)
        return super().do_GET()

    def _json(self, data: dict, status: int = 200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _media_stream(self, item_id: str):
        with _MEDIA_LOCK:
            item = _MEDIA_BY_ID.get(item_id)
        if not item:
            return self._json({"ok": False, "error": "unknown media id"}, 404)
        cached = _cached_file(item_id)
        if cached:
            return self._serve_local_file(cached)
        _start_cache(item)
        try:
            remote, ua = _remote_url(item)
            headers = {"User-Agent": ua or "Mozilla/5.0"}
            if self.headers.get("Range"):
                headers["Range"] = self.headers["Range"]
            req = Request(remote, headers=headers)
            upstream = urlopen(req, timeout=45)
            status = getattr(upstream, "status", 200)
            self.send_response(status)
            for h in ("Content-Type", "Content-Length", "Content-Range", "Accept-Ranges", "ETag", "Last-Modified"):
                v = upstream.headers.get(h)
                if v:
                    self.send_header(h, v)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            while True:
                chunk = upstream.read(256 * 1024)
                if not chunk:
                    break
                self.wfile.write(chunk)
            return
        except BrokenPipeError:
            return
        except Exception as exc:
            return self._json({"ok": False, "error": str(exc)}, 502)

    def _serve_local_file(self, path: Path):
        total = path.stat().st_size
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        start, end = 0, total - 1
        range_header = self.headers.get("Range")
        if range_header:
            m = re.match(r"bytes=(\d*)-(\d*)", range_header)
            if m:
                if m.group(1):
                    start = int(m.group(1))
                if m.group(2):
                    end = min(int(m.group(2)), total - 1)
                self.send_response(HTTPStatus.PARTIAL_CONTENT)
                self.send_header("Content-Range", f"bytes {start}-{end}/{total}")
            else:
                self.send_response(HTTPStatus.OK)
        else:
            self.send_response(HTTPStatus.OK)
        length = max(0, end - start + 1)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with path.open("rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(256 * 1024, remaining))
                if not chunk:
                    break
                self.wfile.write(chunk)
                remaining -= len(chunk)


def main() -> None:
    _sync_catalogue()
    _start_epub_publication()
    print(f"Prophet site: http://{HOST}:{PORT}/")
    print(f"Media player: http://{HOST}:{PORT}/media.html")
    print("EPUB publisher: enabled" if EPUB_ON_START else "EPUB publisher: disabled")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
