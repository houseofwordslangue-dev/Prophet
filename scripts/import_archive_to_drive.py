# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
# Archive.org -> Prophet-Library-Ingestion/Drive importer
# Run in Google Colab. It mounts Drive, verifies public Archive.org files,
# prefers EPUB, falls back to PDF, validates downloads, and writes a report.

import json, os, re, sys, time, hashlib, zipfile
from pathlib import Path
from urllib.parse import quote

import requests

try:
    from google.colab import drive
except Exception:
    drive = None

CATALOGUE = [
    {
        "catalogue_id": "family-companions-029",
        "title": "الاستيعاب في معرفة الأصحاب — ابن عبد البر",
        "archive_id": "fp5294_202505",
    },
    {
        "catalogue_id": "family-companions-031",
        "title": "معرفة الصحابة — أبو نعيم الأصبهاني",
        "archive_id": "fp37408_202504",
    },
    {
        "catalogue_id": "family-companions-010",
        "title": "خصائص أمير المؤمنين علي بن أبي طالب — النسائي",
        "archive_id": "FP26057",
    },
    {
        "catalogue_id": "family-companions-006",
        "title": "الرياض النضرة في مناقب العشرة — محب الدين الطبري",
        "archive_id": "FP17105",
    },
    {
        "catalogue_id": "life-seerah-009",
        "title": "دلائل النبوة ومعرفة أحوال صاحب الشريعة — البيهقي",
        "archive_id": "FP100511",
    },
    {
        "catalogue_id": "teachings-wisdom-012",
        "title": "الشمائل المحمدية — الترمذي",
        "archive_id": "3840waq",
    },
    {
        "catalogue_id": "life-seerah-018",
        "title": "عيون الأثر في فنون المغازي والشمائل والسير — ابن سيد الناس",
        "archive_id": "FPoafmssoafmss",
    },
    {
        "catalogue_id": "life-seerah-020",
        "title": "الوفا بأحوال المصطفى — ابن الجوزي",
        "archive_id": "fp9583_202507",
    },
    {
        "catalogue_id": "life-seerah-024",
        "title": "الخصائص الكبرى — السيوطي",
        "archive_id": "waq9670",
    },
    {
        "catalogue_id": "life-seerah-033",
        "title": "زاد المعاد في هدي خير العباد — ابن قيم الجوزية",
        "archive_id": "fp37672_202501",
    },
]

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Prophet-Library-Ingestion/1.0 (+personal research import)"})


def find_books_root():
    candidates = [
        Path('/content/drive/MyDrive/Prophet-Library-Ingestion/books'),
        Path('/content/drive/My Drive/Prophet-Library-Ingestion/books'),
    ]
    for p in candidates:
        if p.is_dir():
            return p
    base = Path('/content/drive')
    for p in base.rglob('Prophet-Library-Ingestion'):
        q = p / 'books'
        if q.is_dir():
            return q
    raise FileNotFoundError('Could not find Prophet-Library-Ingestion/books in mounted Drive')


def valid_epub(path: Path):
    try:
        if path.stat().st_size < 1024 or not zipfile.is_zipfile(path):
            return False
        with zipfile.ZipFile(path) as z:
            names = set(z.namelist())
            return ('META-INF/container.xml' in names) and any(n.lower().endswith(('.xhtml','.html','.htm')) for n in names)
    except Exception:
        return False


def valid_pdf(path: Path):
    try:
        if path.stat().st_size < 1024:
            return False
        with open(path, 'rb') as f:
            return f.read(5) == b'%PDF-'
    except Exception:
        return False


def existing_valid(dest: Path):
    epubs = [p for p in dest.glob('*.epub') if valid_epub(p)]
    if epubs:
        return ('epub', epubs)
    pdfs = [p for p in dest.glob('*.pdf') if valid_pdf(p)]
    if pdfs:
        return ('pdf', pdfs)
    return (None, [])


def fetch_metadata(identifier: str):
    u = f'https://archive.org/metadata/{identifier}'
    r = SESSION.get(u, timeout=60)
    r.raise_for_status()
    data = r.json()
    if not data.get('files'):
        raise RuntimeError('Archive item returned no files')
    return data


def select_file(meta):
    files = meta.get('files', [])
    def score_epub(f):
        name = f.get('name','')
        fmt = f.get('format','') or ''
        if not name.lower().endswith('.epub') and 'epub' not in fmt.lower():
            return None
        size = int(f.get('size') or 0)
        return (1 if 'epub' in fmt.lower() else 0, size)
    epub = [(score_epub(f), f) for f in files]
    epub = [(s,f) for s,f in epub if s is not None]
    if epub:
        epub.sort(key=lambda x: x[0], reverse=True)
        return 'epub', epub[0][1]

    def score_pdf(f):
        name = f.get('name','')
        fmt = (f.get('format','') or '').lower()
        if not name.lower().endswith('.pdf'):
            return None
        size = int(f.get('size') or 0)
        fmt_score = 3 if 'text pdf' in fmt else 2 if fmt == 'pdf' else 1
        return (fmt_score, size)
    pdf = [(score_pdf(f), f) for f in files]
    pdf = [(s,f) for s,f in pdf if s is not None]
    if pdf:
        pdf.sort(key=lambda x: x[0], reverse=True)
        return 'pdf', pdf[0][1]
    return None, None


def download(identifier, file_rec, dest_dir: Path):
    remote_name = file_rec['name']
    ext = Path(remote_name).suffix.lower()
    out = dest_dir / f'archive-{identifier}{ext}'
    url = f'https://archive.org/download/{identifier}/{quote(remote_name, safe="")}'
    tmp = out.with_suffix(out.suffix + '.part')
    with SESSION.get(url, stream=True, timeout=(30, 300), allow_redirects=True) as r:
        r.raise_for_status()
        with open(tmp, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
    tmp.replace(out)
    return out, url


def sha256(path: Path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main(force=False):
    if drive is not None and not Path('/content/drive/MyDrive').exists():
        drive.mount('/content/drive')
    elif drive is not None:
        try:
            drive.mount('/content/drive', force_remount=False)
        except Exception:
            pass

    books_root = find_books_root()
    report = {
        'started_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'books_root': str(books_root),
        'items': []
    }

    for item in CATALOGUE:
        rec = dict(item)
        dest = books_root / item['catalogue_id']
        dest.mkdir(parents=True, exist_ok=True)
        rec['destination'] = str(dest)
        try:
            fmt0, existing = existing_valid(dest)
            if fmt0 == 'epub' and not force:
                rec.update(status='SKIPPED_VALID_EPUB_EXISTS', existing=[p.name for p in existing])
                print('SKIP EPUB exists:', item['catalogue_id'], item['title'])
                report['items'].append(rec); continue

            meta = fetch_metadata(item['archive_id'])
            md = meta.get('metadata', {}) or {}
            restricted = str(md.get('access-restricted-item','')).lower() in ('true','1','yes')
            if restricted:
                rec.update(status='SKIPPED_RESTRICTED_ARCHIVE_ITEM')
                print('RESTRICTED:', item['archive_id'])
                report['items'].append(rec); continue

            fmt, f = select_file(meta)
            if not f:
                rec.update(status='NO_EPUB_OR_PDF')
                print('NO EPUB/PDF:', item['archive_id'])
                report['items'].append(rec); continue

            if fmt == 'pdf' and fmt0 == 'pdf' and not force:
                rec.update(status='SKIPPED_VALID_PDF_EXISTS_NO_EPUB', existing=[p.name for p in existing])
                print('SKIP PDF exists:', item['catalogue_id'])
                report['items'].append(rec); continue

            out, url = download(item['archive_id'], f, dest)
            ok = valid_epub(out) if fmt == 'epub' else valid_pdf(out)
            if not ok:
                out.unlink(missing_ok=True)
                raise RuntimeError(f'Downloaded {fmt.upper()} failed validation')

            provenance = {
                'catalogue_id': item['catalogue_id'],
                'title': item['title'],
                'source': 'Internet Archive',
                'archive_id': item['archive_id'],
                'item_url': f"https://archive.org/details/{item['archive_id']}",
                'download_url': url,
                'archive_filename': f.get('name'),
                'archive_format': f.get('format'),
                'local_filename': out.name,
                'bytes': out.stat().st_size,
                'sha256': sha256(out),
                'imported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            }
            with open(dest / 'archive_source.json', 'w', encoding='utf-8') as pf:
                json.dump(provenance, pf, ensure_ascii=False, indent=2)

            rec.update(status='IMPORTED', format=fmt, filename=out.name,
                       bytes=out.stat().st_size, archive_filename=f.get('name'),
                       archive_format=f.get('format'), download_url=url)
            print('IMPORTED:', item['catalogue_id'], fmt, out.name, out.stat().st_size)
        except Exception as e:
            rec.update(status='ERROR', error=f'{type(e).__name__}: {e}')
            print('ERROR:', item['catalogue_id'], e)
        report['items'].append(rec)

    report['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    report_path = books_root.parent / 'status' / 'archive_import_report.json'
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print('\nReport:', report_path)
    print(json.dumps({x['catalogue_id']: x['status'] for x in report['items']}, ensure_ascii=False, indent=2))
    return report

if __name__ == '__main__':
    main(force=False)
