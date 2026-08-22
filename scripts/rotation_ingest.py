#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
"""Persistent round-robin ingestion orchestrator.

Each invocation advances durable cursors across independent queues instead of starting
from the first source again. It is safe to run from cron/GitHub Actions because a lock
prevents overlapping cycles and state is written atomically.

Repository policy:
- Commit source code, metadata, manifests, text indexes and processing state.
- Do not commit large acquired book/audio/video binaries.
- Local mirroring/transcription is allowed only when source metadata explicitly marks
  the asset public-domain/open/owned (or another deployment-specific approved right).
"""
from __future__ import annotations
from pathlib import Path
import argparse, contextlib, datetime as dt, json, os, subprocess, sys, tempfile, time

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = ROOT / "private"
DATA = ROOT / "data"
STATE = PRIVATE / "rotation_ingest_state.json"
LOCK = PRIVATE / ".rotation_ingest.lock"
REPORT = ROOT / "reports" / "ROTATION_INGEST_LATEST.json"

QUEUES = {
    "books": PRIVATE / "acquisition_candidates.json",
    "pages": PRIVATE / "source_import_config.json",
    "media": PRIVATE / "media_sources.json",
    "references": DATA / "references.json",
}
DEFAULT_BATCH = {"books": 2, "pages": 4, "media": 3, "references": 25}


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def atomic_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(tmp)


def queue_items(kind: str):
    doc = read_json(QUEUES[kind], {})
    if kind in {"books", "references"}:
        return doc.get("items", []) if isinstance(doc, dict) else []
    return doc.get("sources", []) if isinstance(doc, dict) else []


def state_default():
    return {
        "schema": "rotation-ingest-v1",
        "createdAt": now(),
        "updatedAt": now(),
        "cycle": 0,
        "cursors": {k: 0 for k in QUEUES},
        "stats": {k: {"attempted": 0, "succeeded": 0, "failed": 0, "skipped": 0} for k in QUEUES},
        "lastRun": None,
    }


def acquire_lock(stale_seconds=7200):
    PRIVATE.mkdir(parents=True, exist_ok=True)
    if LOCK.exists():
        age = time.time() - LOCK.stat().st_mtime
        if age < stale_seconds:
            raise RuntimeError(f"rotation already active (lock age {int(age)}s)")
        LOCK.unlink(missing_ok=True)
    LOCK.write_text(json.dumps({"pid": os.getpid(), "startedAt": now()}), encoding="utf-8")


def release_lock():
    LOCK.unlink(missing_ok=True)


def run(cmd, timeout=900):
    started = time.time()
    cp = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    return {
        "ok": cp.returncode == 0,
        "returncode": cp.returncode,
        "seconds": round(time.time() - started, 2),
        "stdout": cp.stdout[-6000:],
        "stderr": cp.stderr[-6000:],
    }


def take_rotating(items, cursor, count):
    n = len(items)
    if not n or count <= 0:
        return [], 0
    count = min(count, n)
    picked = [items[(cursor + i) % n] for i in range(count)]
    return picked, (cursor + count) % n


def id_of(item, fallback):
    return str(item.get("id") or item.get("workId") or item.get("sourceIdentifier") or item.get("titleOriginal") or fallback)


def temporary_registry(path: Path, key: str, selected, command, dry=False, timeout=900):
    if not selected:
        return {"ok": True, "selected": 0, "result": None}
    if dry:
        return {"ok": True, "selected": len(selected), "result": {"ok": True, "dryRun": True}}
    if not Path(ROOT / command[0]).exists() and command[0].endswith('.py'):
        return {"ok": True, "selected": len(selected), "result": {"ok": True, "skipped": "worker-not-restored-yet"}}
    original = path.read_bytes() if path.exists() else json.dumps({key: []}).encode()
    try:
        atomic_json(path, {key: selected})
        result = run([sys.executable, *command], timeout=timeout)
    finally:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)
    return {"ok": result["ok"], "selected": len(selected), "result": result}


def run_books(selected, dry=False):
    return temporary_registry(QUEUES["books"], "items", selected,
                              ["scripts/acquire_unrestricted_library.py", "--limit", str(len(selected))] + (["--dry-run"] if dry else []),
                              dry=False if dry else False, timeout=1800) if selected else {"ok": True, "selected": 0, "result": None}


def run_pages(selected, dry=False):
    if dry:
        return {"ok": True, "selected": len(selected), "result": {"ok": True, "dryRun": True}}
    return temporary_registry(QUEUES["pages"], "sources", selected,
                              ["scripts/import_content.py", "--limit", str(len(selected))], timeout=900)


def run_media(selected, dry=False):
    if dry:
        return {"ok": True, "selected": len(selected), "result": {"ok": True, "dryRun": True}}
    return temporary_registry(QUEUES["media"], "sources", selected,
                              ["scripts/sync_media.py"], timeout=1800)


def run_references(selected, dry=False):
    if dry:
        return {"ok": True, "selected": len(selected), "result": {"ok": True, "dryRun": True}}
    return temporary_registry(QUEUES["references"], "items", selected,
                              ["scripts/sync_references.py", "--limit", str(len(selected)), "--sleep", "0.05"], timeout=1200)


def postprocess(dry=False):
    if dry:
        return {"books": {"ok": True, "dryRun": True}, "manifest": {"ok": True, "dryRun": True}}
    out = {}
    book_worker = ROOT / "scripts/process_local_books.py"
    manifest_worker = ROOT / "scripts/generate_content_manifest.py"
    out["books"] = run([sys.executable, str(book_worker.relative_to(ROOT)), "--all", "--dpi", os.getenv("PM_OCR_DPI", "90")], timeout=3600) if book_worker.exists() else {"ok": True, "skipped": "worker-not-restored-yet"}
    out["manifest"] = run([sys.executable, str(manifest_worker.relative_to(ROOT))], timeout=300) if manifest_worker.exists() else {"ok": True, "skipped": "worker-not-restored-yet"}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--books", type=int, default=int(os.getenv("PM_ROTATE_BOOKS", DEFAULT_BATCH["books"])))
    ap.add_argument("--pages", type=int, default=int(os.getenv("PM_ROTATE_PAGES", DEFAULT_BATCH["pages"])))
    ap.add_argument("--media", type=int, default=int(os.getenv("PM_ROTATE_MEDIA", DEFAULT_BATCH["media"])))
    ap.add_argument("--references", type=int, default=int(os.getenv("PM_ROTATE_REFERENCES", DEFAULT_BATCH["references"])))
    ap.add_argument("--no-postprocess", action="store_true")
    a = ap.parse_args()

    acquire_lock()
    try:
        state = read_json(STATE, state_default())
        state.setdefault("cursors", {})
        state.setdefault("stats", {})
        cycle = int(state.get("cycle", 0)) + 1
        report = {"schema": "rotation-ingest-report-v1", "cycle": cycle, "startedAt": now(), "dryRun": a.dry_run, "queues": {}, "postprocess": {}}
        counts = {"books": a.books, "pages": a.pages, "media": a.media, "references": a.references}
        runners = {"books": run_books, "pages": run_pages, "media": run_media, "references": run_references}

        for kind in ("books", "pages", "media", "references"):
            items = queue_items(kind)
            cursor = int(state["cursors"].get(kind, 0))
            selected, next_cursor = take_rotating(items, cursor, counts[kind])
            ids = [id_of(x, f"{kind}-{i}") for i, x in enumerate(selected)]
            result = runners[kind](selected, a.dry_run)
            report["queues"][kind] = {"total": len(items), "cursorBefore": cursor, "cursorAfter": next_cursor, "selected": ids, "result": result}
            state["cursors"][kind] = next_cursor
            stats = state["stats"].setdefault(kind, {"attempted": 0, "succeeded": 0, "failed": 0, "skipped": 0})
            stats["attempted"] += len(selected)
            if result.get("ok"):
                stats["succeeded"] += len(selected)
            else:
                stats["failed"] += len(selected)

        if not a.no_postprocess:
            report["postprocess"] = postprocess(a.dry_run)
        report["finishedAt"] = now()
        report["success"] = all(v["result"].get("ok", False) for v in report["queues"].values()) and all(v.get("ok", False) for v in report["postprocess"].values())
        state["cycle"] = cycle
        state["updatedAt"] = report["finishedAt"]
        state["lastRun"] = {"cycle": cycle, "success": report["success"], "finishedAt": report["finishedAt"], "report": str(REPORT.relative_to(ROOT)).replace("\\", "/")}
        atomic_json(STATE, state)
        atomic_json(REPORT, report)
        print(json.dumps({"cycle": cycle, "success": report["success"], "state": str(STATE.relative_to(ROOT)), "report": str(REPORT.relative_to(ROOT))}, ensure_ascii=False))
        return 0 if report["success"] else 2
    finally:
        release_lock()


if __name__ == "__main__":
    raise SystemExit(main())
