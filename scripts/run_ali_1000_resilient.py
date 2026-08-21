#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'data' / 'editorial' / 'publication_manifest.json'
SUPPLEMENT = ROOT / 'data' / 'editorial' / 'publication_supplement.json'
TARGET_SCRIPT = ROOT / 'scripts' / 'apply_master_structure_and_ali_1000.py'


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def is_valid_batch(rel: str) -> bool:
    p = ROOT / rel
    if not p.exists():
        return False
    try:
        obj = json.loads(p.read_text(encoding='utf-8'))
        return isinstance(obj, dict) and isinstance(obj.get('drafts', []), list)
    except Exception as exc:
        print(f'SKIP malformed legacy batch: {rel}: {type(exc).__name__}: {exc}', file=sys.stderr)
        return False


def main() -> int:
    originals = {}
    for path in (MANIFEST, SUPPLEMENT):
        if path.exists():
            originals[path] = path.read_text(encoding='utf-8')

    manifest = load(MANIFEST) if MANIFEST.exists() else {}
    supplement = load(SUPPLEMENT) if SUPPLEMENT.exists() else {}
    original_supplement = json.loads(json.dumps(supplement))

    manifest['draftBatchPaths'] = [p for p in manifest.get('draftBatchPaths', []) if is_valid_batch(p)]
    supplement['draftBatchPaths'] = [p for p in supplement.get('draftBatchPaths', []) if is_valid_batch(p)]
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    SUPPLEMENT.write_text(json.dumps(supplement, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    cp = subprocess.run([sys.executable, str(TARGET_SCRIPT)], cwd=str(ROOT))
    if cp.returncode:
        for p, text in originals.items():
            p.write_text(text, encoding='utf-8')
        return cp.returncode

    generated = load(SUPPLEMENT)
    # Preserve every legacy publication reference exactly; append only the newly generated Ali publication.
    old_paths = list(original_supplement.get('draftBatchPaths', []))
    old_ids = list(original_supplement.get('publishedIds', []))
    ali_paths = [p for p in generated.get('draftBatchPaths', []) if '/ali-batch-' in p]
    ali_ids = [i for i in generated.get('publishedIds', []) if str(i).startswith('20260821-ali-source-')]
    merged = original_supplement
    merged['version'] = generated.get('version', merged.get('version'))
    merged['publishedAt'] = generated.get('publishedAt', merged.get('publishedAt'))
    merged['draftBatchPaths'] = old_paths + [p for p in ali_paths if p not in old_paths]
    merged['publishedIds'] = old_ids + [i for i in ali_ids if i not in old_ids]
    merged['ali1000'] = generated.get('ali1000')
    SUPPLEMENT.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    if MANIFEST in originals:
        MANIFEST.write_text(originals[MANIFEST], encoding='utf-8')

    if len(ali_paths) != 20 or len(ali_ids) != 1000:
        print(f'Invalid Ali output: paths={len(ali_paths)}, ids={len(ali_ids)}', file=sys.stderr)
        return 2
    print(f'ALI1000 resilient publication OK: {len(ali_ids)} articles, {len(ali_paths)} batches')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
