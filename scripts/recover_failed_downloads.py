#!/usr/bin/env python3
import hashlib
import json
import mimetypes
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "recovery" / "direct_downloads.json"
INDEX = ROOT / "data" / "ingested_library.json"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ProphetLibraryRecovery/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {"schema": "ingested-library-v2", "items": []}
    items = index.setdefault("items", [])
    by_work = {item.get("workId"): item for item in items}
    recovered = []

    for rec in manifest["items"]:
        raw = fetch(rec["sourceUrl"])
        if len(raw) < 1000:
            raise RuntimeError(f"Downloaded payload too small for {rec['workId']}: {len(raw)} bytes")
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

    index["count"] = len(items)
    index["currentBatchCount"] = len(recovered)
    index["generatedAt"] = datetime.now(timezone.utc).isoformat()
    INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "recoveredAt": datetime.now(timezone.utc).isoformat(),
        "count": len(recovered),
        "items": [{"workId": x["workId"], "editionId": x["editionId"], "size": x["size"], "sha256": x["sha256"], "localUrl": x["localUrl"]} for x in recovered]
    }
    report_path = ROOT / "data" / "recovery" / "last_recovery_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
