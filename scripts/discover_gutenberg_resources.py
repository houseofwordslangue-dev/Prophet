#!/usr/bin/env python3
"""Conservatively discover more public-domain Islam/Prophet research works on Project Gutenberg.

Discovery is intentionally narrow:
- only official gutenberg.org pages;
- only Project Gutenberg subject catalogues relevant to Islam, the Prophet, teachings, history, and Qur'an;
- each candidate page must explicitly state "Public domain in the USA";
- obvious fiction is rejected;
- the actual UTF-8 plain-text download link must be present on the item page;
- existing source identifiers and work IDs are never duplicated.
"""
from __future__ import annotations

from html import unescape
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import argparse
import json
import re
import time

ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "private" / "acquisition_candidates.json"
SUBJECT_URLS = [
    "https://www.gutenberg.org/ebooks/subject/4438",   # Islam
    "https://www.gutenberg.org/ebooks/subject/37228",  # Islam -- History
    "https://www.gutenberg.org/ebooks/subject/1080",   # Qur'an
    "https://www.gutenberg.org/ebooks/subject/12613",  # Muhammad, Prophet, -632
    "https://www.gutenberg.org/ebooks/subject/33023",  # Muhammad -- Teachings
]
UA = "ProphetBiographyLibrary/6.8 GutenbergDiscovery"


def fetch_text(url: str, timeout: int = 45) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/xhtml+xml"})
    with urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def read_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def clean_html(s: str) -> str:
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", unescape(s)).strip()


def subject_ids(html: str):
    seen = set()
    for m in re.finditer(r'href=["\'](?:https://www\.gutenberg\.org)?/ebooks/(\d+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        ebook_id = m.group(1)
        if ebook_id in seen:
            continue
        seen.add(ebook_id)
        yield ebook_id, clean_html(m.group(2))


def plain_text_url(ebook_id: str, html: str) -> str:
    patterns = [
        r'href=["\']([^"\']*?/ebooks/' + re.escape(ebook_id) + r'\.txt\.utf-8)["\']',
        r'href=["\']([^"\']*?/cache/epub/' + re.escape(ebook_id) + r'/pg' + re.escape(ebook_id) + r'\.txt)["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, html, re.I)
        if m:
            return urljoin(f"https://www.gutenberg.org/ebooks/{ebook_id}", unescape(m.group(1)))
    return ""


def metadata_from_page(ebook_id: str, html: str):
    text = clean_html(html)
    if "Public domain in the USA" not in text and "Copyright Status Public domain in the USA" not in text:
        return None
    lowered = text.lower()
    if "-- fiction" in lowered or "category fiction" in lowered or "subject fiction" in lowered:
        return None
    download_url = plain_text_url(ebook_id, html)
    if not download_url:
        return None
    h1m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    heading = clean_html(h1m.group(1)) if h1m else f"Project Gutenberg eBook {ebook_id}"
    heading = re.sub(r"\s*\|\s*Project Gutenberg.*$", "", heading, flags=re.I)
    title = heading
    author = ""
    m = re.match(r"(.+?)\s+by\s+(.+)$", heading, re.I)
    if m:
        title, author = m.group(1).strip(), m.group(2).strip()
    lang = "fr" if re.search(r"\bLanguage\s+French\b", text, re.I) else "en"
    subjects = ["الدراسات الإسلامية", "المصادر والدراسات"]
    if re.search(r"Muhammad|Mohammed|Mahomet|Prophet", text, re.I):
        subjects.insert(0, "السيرة النبوية")
    if re.search(r"Qur.?an|Koran|Kur-an", text, re.I):
        subjects.insert(0, "القرآن وعلومه")
    return {
        "workId": f"gutenberg-{ebook_id}",
        "titleOriginal": title,
        "author": author,
        "language": lang,
        "format": "txt",
        "sourceRepository": "Project Gutenberg",
        "sourceIdentifier": ebook_id,
        "sourceUrl": f"https://www.gutenberg.org/ebooks/{ebook_id}",
        "downloadUrl": download_url,
        "rightsEvidence": "Public domain in the USA",
        "rightsEvidenceUrl": f"https://www.gutenberg.org/ebooks/{ebook_id}",
        "subjects": subjects,
        "siteSections": ["المصادر والدراسات"],
        "discoveredBy": "official-gutenberg-relevant-subjects",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--sleep", type=float, default=0.15)
    args = ap.parse_args()
    q = read_json(QUEUE, {"schema": "strict-unrestricted-candidates-v1", "rotationEnabled": True, "items": []})
    items = q.setdefault("items", [])
    seen_ids = {str(x.get("sourceIdentifier") or "") for x in items if x.get("sourceRepository") == "Project Gutenberg"}
    seen_work = {str(x.get("workId") or "") for x in items}
    added = []
    inspected = 0
    failures = []
    for subject_url in SUBJECT_URLS:
        try:
            listing = fetch_text(subject_url)
        except Exception as exc:
            failures.append({"url": subject_url, "error": type(exc).__name__})
            continue
        for ebook_id, _label in subject_ids(listing):
            if len(added) >= max(0, args.limit):
                break
            if ebook_id in seen_ids or f"gutenberg-{ebook_id}" in seen_work:
                continue
            inspected += 1
            try:
                page = fetch_text(f"https://www.gutenberg.org/ebooks/{ebook_id}")
                candidate = metadata_from_page(ebook_id, page)
            except Exception as exc:
                failures.append({"id": ebook_id, "error": type(exc).__name__})
                continue
            if not candidate:
                continue
            items.append(candidate)
            added.append(candidate["sourceIdentifier"])
            seen_ids.add(ebook_id)
            seen_work.add(candidate["workId"])
            if args.sleep:
                time.sleep(args.sleep)
        if len(added) >= max(0, args.limit):
            break
    if added:
        q["lastDiscoveryAt"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        QUEUE.write_text(json.dumps(q, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inspected": inspected, "added": len(added), "addedIds": added, "queueTotal": len(items), "failures": failures[:10]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
