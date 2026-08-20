#!/usr/bin/env python3
import hashlib
import json
import pathlib
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "recovery" / "direct_downloads.json"
INDEX = ROOT / "data" / "ingested_library.json"
REPORT = ROOT / "data" / "recovery" / "last_recovery_report.json"


def fetch(url: str, attempts: int = 3) -> bytes:
    last = None
    for attempt in range(1, attempts + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ProphetLibraryRecovery/1.1"})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
            if attempt < attempts:
                time.sleep(min(10, 2 ** attempt))
    raise last


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {"schema": "ingested-library-v2", "items": []}
    items = index.setdefault("items", [])
    by_work = {item.get("workId"): item for item in items}
    recovered, failed = [], []

    for rec in manifest.get("items", []):
        try:
            raw = fetch(rec["sourceUrl"])
            if len(raw) < 1000:
                raise RuntimeError(f"Downloaded payload too small: {len(raw)} bytes")
            digest = hashlib.sha256(raw).hexdigest()
            edition_id = f"ed-{digest[:12]}"
            target_dir = ROOT / "library" / "works" / rec["workId"] / "editions" / edition_id
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / "original.txt"
            target.write_bytes(raw)
            local_url = f"/library/works/{rec['workId']}/editions/{edition_id}/original.txt"
            item = {
                "id": f"{rec['workId']}:{edition_id}",
                "workId": rec["workId"],
                "editionId": edition_id,
                "titleOriginal": rec["title"],
                "titleAr": None,
                "titleEn": rec["title"],
                "titleFr": None,
                "author": rec["author"],
                "language": rec["language"],
                "subjects": rec["subjects"],
                "siteSections": ["المصادر والدراسات"],
                "format": "txt",
                "mimeType": "text/plain",
                "size": len(raw),
                "sha256": digest,
                "localUrl": local_url,
                "readerUrl": local_url,
                "sourceUrl": rec["sourceUrl"],
                "sourcePage": rec["sourcePage"],
                "capabilities": {"readable": True, "searchable": True, "listenable": True, "watchable": False},
                "searchMode": "fulltext-browser",
                "listenMode": "browser-tts",
                "watchMode": "none",
                "publishedAsset": True,
                "recoveryStatus": "recovered-from-failed-download-list"
            }
            if rec["workId"] in by_work:
                old = by_work[rec["workId"]]
                items[items.index(old)] = item
            else:
                items.append(item)
            by_work[rec["workId"]] = item
            recovered.append(item)
        except Exception as exc:
            # A remote host outage/504 is a source-level retry condition, not a
            # repository-integrity failure. Record it and continue so one host
            # cannot generate repeated failed-workflow notifications.
            failed.append({
                "workId": rec.get("workId"),
                "sourceUrl": rec.get("sourceUrl"),
                "errorType": type(exc).__name__,
                "error": str(exc),
                "retryable": isinstance(exc, (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError)),
            })
            print(f"WARNING: recovery deferred for {rec.get('workId')}: {type(exc).__name__}: {exc}")

    index["count"] = len(items)
    index["currentBatchCount"] = len(recovered)
    index["generatedAt"] = datetime.now(timezone.utc).isoformat()
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "recoveredAt": datetime.now(timezone.utc).isoformat(),
        "requested": len(manifest.get("items", [])),
        "recoveredCount": len(recovered),
        "deferredCount": len(failed),
        "status": "COMPLETE" if not failed else "PARTIAL_RETRY_PENDING",
        "items": [{"workId": x["workId"], "editionId": x["editionId"], "size": x["size"], "sha256": x["sha256"], "localUrl": x["localUrl"]} for x in recovered],
        "deferred": failed,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
