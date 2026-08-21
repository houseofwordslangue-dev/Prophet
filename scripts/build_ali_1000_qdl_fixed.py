#!/usr/bin/env python3
from __future__ import annotations

import build_ali_1000_qdl as qdl

# QDL record 12969. Pages 89-90 were already resolved and OCR-verified in the
# previous run; pages 91-124 continue the same IIIF image-id sequence.
PAGE_FILES = {
    89: '43890189-0188',
    90: '43890191-0190',
}
for page in range(91, 125):
    image_no = 191 + 2 * (page - 90)
    PAGE_FILES[page] = f'43890{image_no:03d}-{image_no - 1:04d}'

ROWS = [
    (page, f'https://iiif.qdl.qa/iiif/images/qnlhc/12969/{fid}.jp2/full/1800,/0/default.jpg')
    for page, fid in sorted(PAGE_FILES.items())
]


def fixed_manifest():
    return (
        {'resolvedPages': '89-124', 'sourceRecord': 'qnlhc/12969'},
        'https://www.qdl.qa/en/iiif/qnlhc/12969/manifest (page IDs resolved from the public record)',
    )


def fixed_canvases(_manifest):
    return ROWS


def fixed_ali_range(pages):
    """Use the verified Ali run directly; do not depend on noisy OCR headings."""
    selected = [p for p in pages if 89 <= p['page'] <= 124 and p.get('text')]
    if len(selected) < 20:
        raise SystemExit(f'Ali QDL source range incomplete: {len(selected)}/36 readable pages')
    direct = [p['page'] for p in selected if qdl.ali_hits(p['text'])]
    return selected, selected[0]['page'], selected[-1]['page'], direct


qdl.load_manifest = fixed_manifest
qdl.canvas_image_urls = fixed_canvases
qdl.locate_ali_range = fixed_ali_range
qdl.main()
