#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import base64
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
IMAGE_ROOT = ROOT / "assets" / "children" / "generated"
IMAGE_ROOT.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-1").strip() or "gpt-image-1"
MAX_PER_RUN = max(0, int(os.getenv("CHILDREN_IMAGE_MAX_PER_RUN", "100")))
FORCE = os.getenv("CHILDREN_IMAGE_FORCE", "0") == "1"

CHILD_MARKERS = (
    "children", "child", "kids", "kid", "أحباب الله", "الأطفال", "اطفال", "طفل",
)
CONTENT_MARKERS = (
    "story", "article", "animated-story", "children-story", "children-article",
    "قصة", "مقال", "حكاية",
)
IMAGE_KEYS = ("image", "imageUrl", "coverImage", "thumbnail", "heroImage")
TEXT_KEYS = (
    "titleAr", "titleEn", "titleFr", "title", "headline", "name",
    "synopsisAr", "synopsisEn", "synopsisFr", "synopsis", "summary", "excerpt",
    "body", "content", "text", "storyAr", "storyEn", "storyFr",
)


def _flat_text(value, limit: int = 4200) -> str:
    parts: list[str] = []

    def walk(v):
        if len(" ".join(parts)) >= limit:
            return
        if isinstance(v, str):
            s = re.sub(r"\s+", " ", v).strip()
            if s:
                parts.append(s)
        elif isinstance(v, list):
            for item in v[:12]:
                walk(item)
        elif isinstance(v, dict):
            for key in ("text", "title", "narration", "description", "value"):
                if key in v:
                    walk(v[key])

    walk(value)
    return " ".join(parts)[:limit]


def _record_text(record: dict) -> str:
    parts = []
    for key in TEXT_KEYS:
        if key in record:
            t = _flat_text(record.get(key))
            if t and t not in parts:
                parts.append(t)
    return " ".join(parts)[:5000]


def _is_children_record(record: dict, source_path: Path) -> bool:
    p = source_path.as_posix().lower()
    if "/children/" in f"/{p}/" or "children" in source_path.name.lower():
        return True
    probe = " ".join(
        str(record.get(k) or "")
        for k in ("section", "sectionAr", "sectionEn", "sectionFr", "category", "categoryAr", "categoryEn", "categoryFr", "audience", "collection")
    ).lower()
    return any(marker.lower() in probe for marker in CHILD_MARKERS)


def _is_story_or_article(record: dict) -> bool:
    kind = " ".join(str(record.get(k) or "") for k in ("type", "kind", "contentType", "format", "id", "slug")).lower()
    if any(marker.lower() in kind for marker in CONTENT_MARKERS):
        return True
    # Content records often omit a type; a title plus substantial text is enough.
    has_title = any(record.get(k) for k in ("title", "titleAr", "titleEn", "titleFr", "headline"))
    return has_title and len(_record_text(record)) >= 80


def _existing_image(record: dict) -> str:
    for key in IMAGE_KEYS:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, dict):
            for sub in ("path", "url", "src"):
                if isinstance(value.get(sub), str) and value[sub].strip():
                    return value[sub].strip()
    cover = record.get("cover")
    if isinstance(cover, str) and cover.strip():
        return cover.strip()
    if isinstance(cover, dict):
        for sub in ("path", "url", "src", "image"):
            if isinstance(cover.get(sub), str) and cover[sub].strip():
                return cover[sub].strip()
    return ""


def _slug(record: dict, source_path: Path, ordinal: int) -> str:
    raw = str(record.get("slug") or record.get("id") or record.get("titleEn") or record.get("titleAr") or f"{source_path.stem}-{ordinal}")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", raw).strip("-._").lower()
    if not safe:
        safe = f"children-{abs(hash(raw)) % 10**12}"
    return safe[:120]


def _prompt(record: dict) -> str:
    title = next((str(record.get(k)).strip() for k in ("titleEn", "titleAr", "titleFr", "title", "headline") if record.get(k)), "Children story")
    context = _record_text(record)
    return (
        "Create a warm, high-quality editorial illustration for a children's story/article from an educational biography website. "
        "The illustration must visually represent only the supplied source-grounded content; do not add historical claims, named people, events, objects, inscriptions, or religious details that are not supported by the supplied text. "
        "Child-friendly storybook composition, elegant hand-painted digital illustration, expressive environment, culturally respectful clothing and architecture where the text supports them, no written words, no captions, no logos, no watermark. "
        "Do not depict the Prophet Muhammad or other sacred figures directly; when the supplied text concerns them, use respectful symbolic/environmental imagery such as landscape, architecture, light, objects, or silhouettes without facial representation. "
        f"Title: {title}\nSource-grounded content excerpt: {context[:3500]}"
    )


def _generate_png(prompt: str) -> bytes:
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "size": "1536x1024",
        "quality": "medium",
        "output_format": "png",
    }).encode("utf-8")
    req = Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        method="POST",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    with urlopen(req, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))
    item = (body.get("data") or [{}])[0]
    b64 = item.get("b64_json")
    if b64:
        return base64.b64decode(b64)
    url = item.get("url")
    if url:
        with urlopen(Request(url, headers={"User-Agent": "Prophet-children-image-pipeline/1.0"}), timeout=180) as response:
            return response.read()
    raise RuntimeError("image API returned neither b64_json nor url")


def _apply_image(record: dict, source_path: Path, ordinal: int) -> bool:
    if not _is_children_record(record, source_path) or not _is_story_or_article(record):
        return False
    if not FORCE and _existing_image(record):
        return False
    slug = _slug(record, source_path, ordinal)
    rel = Path("assets") / "children" / "generated" / f"{slug}.png"
    dest = ROOT / rel
    if dest.exists() and not FORCE:
        record["image"] = "/" + rel.as_posix()
        record.setdefault("imageSource", "ai-generated")
        return True
    png = _generate_png(_prompt(record))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(png)
    record["image"] = "/" + rel.as_posix()
    record["imageSource"] = "ai-generated"
    record["imageModel"] = MODEL
    record["imageGeneratedAt"] = datetime.now(timezone.utc).isoformat()
    return True


def _walk(value, source_path: Path, counter: list[int], stats: dict) -> bool:
    changed = False
    if isinstance(value, dict):
        if _is_children_record(value, source_path) and _is_story_or_article(value):
            stats["eligible"] += 1
            if _existing_image(value) and not FORCE:
                stats["preserved"] += 1
            elif MAX_PER_RUN and stats["generated"] >= MAX_PER_RUN:
                stats["deferred"] += 1
            else:
                counter[0] += 1
                try:
                    if _apply_image(value, source_path, counter[0]):
                        stats["generated"] += 1
                        changed = True
                except Exception as exc:
                    stats["failed"] += 1
                    print(f"IMAGE WARNING {source_path}: {exc}")
            # Still descend because some story records can contain article-like children blocks.
        for child in value.values():
            if isinstance(child, (dict, list)):
                changed = _walk(child, source_path, counter, stats) or changed
    elif isinstance(value, list):
        for child in value:
            changed = _walk(child, source_path, counter, stats) or changed
    return changed


def main() -> int:
    stats = {"files": 0, "eligible": 0, "preserved": 0, "generated": 0, "deferred": 0, "failed": 0}
    counter = [0]
    if not DATA_ROOT.exists():
        print("Children image pass: no data directory")
        return 0
    for path in sorted(DATA_ROOT.rglob("*.json")):
        try:
            raw = path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except Exception:
            continue
        stats["files"] += 1
        if _walk(data, path, counter, stats):
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Children image pass:", json.dumps(stats, ensure_ascii=False))
    # Image generation is supplementary: never block story/article publication.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
