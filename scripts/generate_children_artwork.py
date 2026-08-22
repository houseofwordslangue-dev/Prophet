#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MODEL = os.getenv("IMAGE_MODEL", "gpt-image-2")
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
SIZE = os.getenv("CHILDREN_IMAGE_SIZE", "1536x1024")
QUALITY = os.getenv("CHILDREN_IMAGE_QUALITY", "medium")
MAX_RETRIES = int(os.getenv("CHILDREN_IMAGE_RETRIES", "4"))

CHILD_ROOTS = [
    ROOT / "data" / "children",
    ROOT / "content" / "children",
    ROOT / "public" / "data" / "children",
]

TEXT_KEYS = (
    "titleAr", "titleEn", "titleFr", "title", "headline",
    "synopsisAr", "synopsisEn", "synopsisFr", "synopsis", "summary",
    "bodyAr", "bodyEn", "bodyFr", "body", "contentAr", "contentEn", "contentFr", "content",
)
IMAGE_KEYS = ("image", "featuredImage", "heroImage", "thumbnail", "artwork")


def _safe_slug(value: str) -> str:
    value = re.sub(r"[^\w\-]+", "-", value.strip(), flags=re.UNICODE).strip("-")
    return value[:100] or "children-item"


def _text(item: dict[str, Any], limit: int = 4200) -> str:
    parts: list[str] = []
    for key in TEXT_KEYS:
        val = item.get(key)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    if not parts:
        for key in ("storyAr", "storyEn", "storyFr", "scenes"):
            val = item.get(key)
            if isinstance(val, list):
                for row in val[:4]:
                    if isinstance(row, dict):
                        for k in ("text", "narration", "narrationEn", "narrationFr", "visualDescriptionAr", "visualDescriptionEn", "visualDescriptionFr"):
                            if isinstance(row.get(k), str) and row[k].strip():
                                parts.append(row[k].strip())
    return "\n".join(parts)[:limit]


def _base_prompt(item: dict[str, Any], extra: str = "") -> str:
    source = _text(item)
    return f"""Create a polished, original illustration for a children's educational story/article on the Prophet biography website, section أحباب الله.
Use ONLY the supplied source content as narrative grounding. Do not add historical claims, quotations, names, events, symbols, locations, clothing details, architecture, or objects not reasonably supported by the source.
Style: warm premium children's-book illustration, sophisticated but welcoming, cinematic composition, expressive light, rich detail, age-appropriate, culturally respectful, no text, no lettering, no logos, no watermarks.
If the source concerns Prophet Muhammad or another named sacred/historical figure whose direct depiction would be inappropriate, DO NOT depict that person. Use respectful indirect visual storytelling: setting, landscape, objects, architecture, light, hands without identifying features, silhouettes only when non-identifying, or other contextual imagery.
Never imitate an existing copyrighted artwork or living artist's signature style.
{extra}
SOURCE CONTENT:\n{source}""".strip()


def _api_generate(prompt: str) -> bytes:
    if not API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required")
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "size": SIZE,
        "quality": QUALITY,
        "output_format": "png",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    last: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=240) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            b64 = data["data"][0].get("b64_json")
            if not b64:
                raise RuntimeError("Image API returned no b64_json")
            return base64.b64decode(b64)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, KeyError, ValueError, RuntimeError) as exc:
            last = exc
            if attempt + 1 >= MAX_RETRIES:
                break
            time.sleep(min(30, 2 ** (attempt + 1)))
    raise RuntimeError(f"image generation failed: {last}")


def _write_png(rel: str, prompt: str, dry_run: bool) -> str:
    rel = rel.replace("\\", "/")
    p = ROOT / rel
    p = p.with_suffix(".png")
    if dry_run:
        print(f"DRY-RUN {p.relative_to(ROOT)}")
        return p.relative_to(ROOT).as_posix()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(_api_generate(prompt))
    return p.relative_to(ROOT).as_posix()


def _replace_story_art(item: dict[str, Any], index: int, dry_run: bool) -> int:
    count = 0
    ident = str(item.get("id") or item.get("slug") or item.get("titleEn") or item.get("titleAr") or f"item-{index}")
    slug = _safe_slug(ident)
    cover = item.get("cover")
    if isinstance(cover, dict):
        old = str(cover.get("path") or f"public/images/children/generated/{slug}/cover.png")
        new = _write_png(old, _base_prompt(item, "Create the cover image. Strong single focal composition suitable for a story/article card and opening page."), dry_run)
        cover["path"] = new
        cover["generated"] = True
        cover["generator"] = MODEL
        cover["replacementArtwork"] = True
        count += 1
    else:
        new = _write_png(f"public/images/children/generated/{slug}/cover.png", _base_prompt(item, "Create the main cover image."), dry_run)
        item["cover"] = {"path": new, "generated": True, "generator": MODEL, "replacementArtwork": True}
        count += 1

    scenes = item.get("scenes")
    if isinstance(scenes, list):
        for n, scene in enumerate(scenes, 1):
            if not isinstance(scene, dict):
                continue
            scene_source = dict(item)
            scene_source.update(scene)
            old = str(scene.get("illustration") or f"public/images/children/generated/{slug}/scene-{n:02d}.png")
            extra = f"Create scene {n}. Follow this scene's visual description and narration closely. Preserve visual continuity with the story but do not copy any old artwork."
            new = _write_png(old, _base_prompt(scene_source, extra), dry_run)
            scene["illustration"] = new
            scene["illustrationGenerated"] = True
            scene["illustrationGenerator"] = MODEL
            scene["replacementArtwork"] = True
            count += 1
    return count


def _replace_generic_art(item: dict[str, Any], index: int, dry_run: bool) -> int:
    ident = str(item.get("id") or item.get("slug") or item.get("titleEn") or item.get("titleAr") or f"article-{index}")
    slug = _safe_slug(ident)
    target_key = next((k for k in IMAGE_KEYS if isinstance(item.get(k), str)), "featuredImage")
    old = str(item.get(target_key) or f"public/images/children/generated/{slug}/article.png")
    item[target_key] = _write_png(old, _base_prompt(item, "Create a feature image for this children's article/story. It must work well in a card and at the top of an article page."), dry_run)
    item["imageGenerated"] = True
    item["imageGenerator"] = MODEL
    item["replacementArtwork"] = True
    return 1


def _looks_like_content(item: dict[str, Any]) -> bool:
    return bool(_text(item)) and any(k in item for k in ("titleAr", "titleEn", "titleFr", "title", "storyAr", "storyEn", "storyFr", "body", "content"))


def _process_json(path: Path, dry_run: bool) -> tuple[int, int]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0, 0
    changed = 0
    images = 0

    def visit(node: Any, idx: list[int]) -> None:
        nonlocal changed, images
        if isinstance(node, dict):
            if _looks_like_content(node):
                idx[0] += 1
                images += _replace_story_art(node, idx[0], dry_run) if isinstance(node.get("scenes"), list) else _replace_generic_art(node, idx[0], dry_run)
                changed += 1
                return
            for val in node.values():
                visit(val, idx)
        elif isinstance(node, list):
            for val in node:
                visit(val, idx)

    visit(data, [0])
    if changed and not dry_run:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed, images


def main() -> None:
    ap = argparse.ArgumentParser(description="Replace all children-section artwork with source-grounded generated images.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Maximum JSON files to process; 0 means all")
    args = ap.parse_args()

    files: list[Path] = []
    for root in CHILD_ROOTS:
        if root.exists():
            files.extend(sorted(root.rglob("*.json")))
    files = sorted(set(files))
    if args.limit:
        files = files[: args.limit]

    total_items = total_images = 0
    for path in files:
        items, images = _process_json(path, args.dry_run)
        total_items += items
        total_images += images
        if items:
            print(f"UPDATED {path.relative_to(ROOT)} items={items} images={images}")

    print(f"COMPLETE files={len(files)} content_items={total_items} replacement_images={total_images} model={MODEL}")


if __name__ == "__main__":
    main()
