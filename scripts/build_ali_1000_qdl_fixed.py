#!/usr/bin/env python3
from __future__ import annotations

import build_ali_1000_qdl as qdl

PAGE_FILES = {
55:'43890115-0114',56:'43890117-0116',57:'43890119-0118',58:'43890125-0124',59:'43890127-0126',60:'43890129-0128',61:'43890131-0130',62:'43890133-0132',63:'43890135-0134',64:'43890137-0136',65:'43890139-0138',66:'43890141-0140',67:'43890143-0142',68:'43890145-0144',69:'43890147-0146',70:'43890149-0148',71:'43890151-0150',72:'43890153-0152',73:'43890155-0154',74:'43890157-0156',75:'43890159-0158',76:'43890161-0160',77:'43890163-0162',78:'43890165-0164',79:'43890167-0166',80:'43890169-0168',81:'43890171-0170',82:'43890173-0172',83:'43890175-0174',84:'43890177-0176',85:'43890179-0178',86:'43890183-0182',87:'43890185-0184',88:'43890187-0186',89:'43890189-0188',90:'43890191-0190'
}
ROWS=[(p,f'https://iiif.qdl.qa/iiif/images/qnlhc/12969/{fid}.jp2/full/1800,/0/default.jpg') for p,fid in PAGE_FILES.items()]

def fixed_manifest():
    return ({'resolvedPages':'55-90'},'https://www.qdl.qa/en/iiif/qnlhc/12969/manifest (page IDs resolved from public record page)')

def fixed_canvases(_manifest):
    return ROWS

qdl.load_manifest=fixed_manifest
qdl.canvas_image_urls=fixed_canvases
qdl.main()
