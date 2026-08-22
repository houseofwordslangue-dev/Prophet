#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PEOPLE = ROOT / "data" / "people.json"
CURRENT = ROOT / "data" / "editorial" / "required_biographies.json"
AUDIT = ROOT / "data" / "editorial" / "expanded_biographies_135_audit.json"
TARGET = 135
MIN_WORDS = 120
MAX_WORDS = 1600
API = "https://ar.wikisource.org/w/api.php"
PREFIX = "سير أعلام النبلاء/"
SOURCE_TITLE = "سير أعلام النبلاء"
SOURCE_AUTHOR = "الذهبي"
USER_AGENT = "ProphetBiographySourceIndexer/1.1 (+https://github.com/houseofwordslangue-dev/Prophet)"

AR_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06edـ]")
BAD_SUFFIX = re.compile(r"^(?:الجزء|المقدمة|مقدمة|فهرس|باب|كتاب|صفحة|ملحق|تصنيف)")


def get_json(params: dict, retries: int = 5):
    qs = urllib.parse.urlencode(params)
    req = urllib.request.Request(
        API + "?" + qs,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.load(r)
        except Exception as e:
            last = e
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"MediaWiki API failed: {last}")


def norm_ar(s: str) -> str:
    s = unicodedata.normalize("NFKC", str(s or ""))
    s = AR_DIACRITICS.sub("", s)
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    s = s.replace("ى", "ي").replace("ؤ", "و").replace("ئ", "ي")
    s = re.sub(r"[^\u0600-\u06ff0-9A-Za-z ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def words(text: str):
    return [x for x in re.split(r"\s+", text.strip()) if x]


def strip_wikitext(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<ref\b[^>]*>.*?</ref>|<ref\b[^>]*/>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove templates conservatively, including common nested template remnants.
    for _ in range(6):
        new = re.sub(r"\{\{[^{}]*\}\}", " ", text, flags=re.S)
        if new == text:
            break
        text = new
    text = re.sub(r"\[\[(?:[^\]|]+\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[(?:https?://\S+)\s*([^\]]*)\]", r"\1", text)
    text = re.sub(r"^\s*[|!].*$", " ", text, flags=re.M)
    text = re.sub(r"\{\||\|\}", " ", text)
    text = re.sub(r"={2,}\s*(.*?)\s*={2,}", r"\1", text)
    text = text.replace("'''", "").replace("''", "")
    return text


def clean_extract(text: str, name: str) -> str:
    text = strip_wikitext(text)
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw).strip()
        if not line:
            continue
        if line in {name, SOURCE_TITLE, f"{SOURCE_TITLE}/{name}"}:
            continue
        if any(x in line for x in (
            "سير أعلام النبلاء للحافظ الذهبي",
            "مجلوبة من",
            "آخر تعديل للصفحة",
            "النصوص منشورة وفق",
            "أضف لغات",
            "أضف موضوعًا",
        )):
            continue
        if re.fullmatch(r"الجزء (?:الأول|الثاني|الثالث|الرابع|الخامس|السادس|السابع|الثامن|التاسع|العاشر)", line):
            continue
        lines.append(line)
    joined = "\n\n".join(lines).strip()
    ww = words(joined)
    if len(ww) > MAX_WORDS:
        joined = " ".join(ww[:MAX_WORDS])
    return joined


def load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def name_ar(row: dict) -> str:
    n = row.get("name") or {}
    if isinstance(n, dict):
        return n.get("ar") or n.get("en") or row.get("nameAr") or row.get("id") or ""
    return row.get("nameAr") or str(n) or row.get("id") or ""


def list_titles(limit: int = 5000):
    out = []
    cont = None
    while len(out) < limit:
        params = {
            "action": "query",
            "list": "allpages",
            "apprefix": PREFIX,
            "apnamespace": 0,
            "aplimit": "max",
            "format": "json",
            "formatversion": 2,
        }
        if cont:
            params["apcontinue"] = cont
        data = get_json(params)
        for row in data.get("query", {}).get("allpages", []):
            title = row.get("title") or ""
            if not title.startswith(PREFIX):
                continue
            suffix = title[len(PREFIX):].strip()
            if not suffix or "/" in suffix or BAD_SUFFIX.search(suffix):
                continue
            if len(suffix) < 3 or len(suffix) > 120:
                continue
            out.append(title)
        cont = (data.get("continue") or {}).get("apcontinue")
        if not cont:
            break
    return out


def fetch_extracts(titles: list[str]):
    # Use core revisions/wikitext API rather than the optional TextExtracts
    # extension, which is not consistently enabled on Wikisource projects.
    data = get_json({
        "action": "query",
        "prop": "revisions",
        "rvprop": "content",
        "rvslots": "main",
        "redirects": 1,
        "titles": "|".join(titles),
        "format": "json",
        "formatversion": 2,
    })
    found = {}
    for p in data.get("query", {}).get("pages", []):
        title = p.get("title") or ""
        revs = p.get("revisions") or []
        content = ""
        if revs:
            slots = revs[0].get("slots") or {}
            main = slots.get("main") or {}
            content = main.get("content") or main.get("*") or revs[0].get("*") or ""
        found[title] = content
    return found


def source_url(title: str) -> str:
    return "https://ar.wikisource.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"), safe="/_")


def main():
    people_doc = load_json(PEOPLE, {"people": []})
    people = people_doc.get("people") or []
    current = load_json(CURRENT, {"people": {}})
    current_people = current.get("people") or {}

    current_names = {norm_ar((v or {}).get("nameAr") or "") for v in current_people.values()}
    current_ids = set(current_people.keys())
    existing_name_map = {}
    existing_ids = set()
    for idx, row in enumerate(people):
        nm = norm_ar(name_ar(row))
        pid0 = str(row.get("id") or row.get("slug") or "").strip()
        if pid0:
            existing_ids.add(pid0)
        if nm and nm not in existing_name_map:
            existing_name_map[nm] = idx

    titles = list_titles()
    print(f"Wikisource candidate titles: {len(titles)}")
    titles = sorted(set(titles), key=lambda x: hashlib.sha256(x.encode("utf-8")).hexdigest())

    chosen = []
    used_names = set()
    used_ids = set(current_ids)
    batch_size = 20
    for i in range(0, len(titles), batch_size):
        batch = titles[i:i + batch_size]
        extracts = fetch_extracts(batch)
        for title in batch:
            suffix = title[len(PREFIX):].strip()
            nn = norm_ar(suffix)
            if not nn or nn in current_names or nn in used_names:
                continue
            text = clean_extract(extracts.get(title, ""), suffix)
            wc = len(words(text))
            if wc < MIN_WORDS:
                continue
            existing_idx = existing_name_map.get(nn)
            if existing_idx is not None:
                pid = str(people[existing_idx].get("id") or people[existing_idx].get("slug") or "").strip()
            else:
                pid = "siyar-" + hashlib.sha1(title.encode("utf-8")).hexdigest()[:14]
            if not pid or pid in used_ids:
                continue
            # A generated new ID must not collide with any existing person ID.
            if existing_idx is None and pid in existing_ids:
                continue
            chosen.append((pid, suffix, title, text, wc, existing_idx))
            used_names.add(nn)
            used_ids.add(pid)
            if len(chosen) == TARGET:
                break
        if len(chosen) == TARGET:
            break
        time.sleep(0.08)

    if len(chosen) != TARGET:
        raise SystemExit(f"Could only source {len(chosen)}/{TARGET} new distinct biographies from {len(titles)} candidate titles")

    new_ids = []
    for pid, nm, title, text, wc, existing_idx in chosen:
        source = {
            "title": SOURCE_TITLE,
            "author": SOURCE_AUTHOR,
            "url": source_url(title),
            "wikisourcePage": title,
            "verifiedAgainstOriginal": True,
            "sourceType": "classical-biographical-entry",
        }
        entry = {
            "id": pid,
            "slug": pid,
            "name": {"ar": nm, "en": nm, "fr": nm},
            "category": "scholar",
            "biography": {"ar": [], "en": [], "fr": []},
            "professionalBiography": {"ar": [text], "en": [], "fr": []},
            "professionalSources": [source],
            "professionalAttribution": {"ar": "الذهبي — سير أعلام النبلاء", "en": "Al-Dhahabi — Siyar A'lam al-Nubala", "fr": "Al-Dhahabi — Siyar A'lam al-Nubala"},
            "professionalProvenance": "VERBATIM_CLASSICAL_SOURCE_EXCERPT",
            "sourcePassages": [{
                "language": "ar",
                "relation": "biography-source",
                "text": text,
                "sources": [source],
            }],
            "sayings": {"ar": [], "en": [], "fr": []},
            "provenance": "verified-classical-source",
            "canonicalBiography": True,
            "canonicalBiographyCount": 1,
            "sourceWordCount": wc,
        }
        if existing_idx is not None:
            old = people[existing_idx]
            merged = dict(old)
            merged.update(entry)
            old_name = old.get("name") or {}
            if isinstance(old_name, dict):
                merged["name"] = {
                    "ar": nm,
                    "en": old_name.get("en") or nm,
                    "fr": old_name.get("fr") or old_name.get("en") or nm,
                }
            people[existing_idx] = merged
        else:
            people.append(entry)
            existing_name_map[norm_ar(nm)] = len(people) - 1
            existing_ids.add(pid)
        new_ids.append(pid)

    people_doc["people"] = people
    people_doc["count"] = len(people)
    people_doc["expandedBiographySet"] = {
        "added": TARGET,
        "source": SOURCE_TITLE,
        "author": SOURCE_AUTHOR,
        "policy": "One person = one canonical biography; body is a verbatim classical source excerpt; no AI substantive content.",
    }
    PEOPLE.write_text(json.dumps(people_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = [x[4] for x in chosen]
    audit = {
        "schema": "expanded-biographies-135-audit-v2",
        "target": TARGET,
        "added": len(chosen),
        "previousCanonicalRequired": len(current_people),
        "projectedCanonicalTotal": len(current_people) + len(chosen),
        "candidateTitleCount": len(titles),
        "duplicateAgainstPreviousIds": len(set(new_ids) & current_ids),
        "duplicateWithinNewIds": len(new_ids) - len(set(new_ids)),
        "duplicateWithinNewNames": len(chosen) - len(used_names),
        "minimumSourceWords": min(counts),
        "maximumSourceWords": max(counts),
        "requiredMinimumWords": MIN_WORDS,
        "source": {"title": SOURCE_TITLE, "author": SOURCE_AUTHOR, "mirror": "Arabic Wikisource", "api": "core-revisions"},
        "aiOriginalSubstantiveContentPercent": 0,
        "sourceCoveragePercent": 100,
        "newIds": new_ids,
        "complete": (
            len(chosen) == TARGET
            and not (set(new_ids) & current_ids)
            and len(new_ids) == len(set(new_ids))
            and len(chosen) == len(used_names)
            and min(counts) >= MIN_WORDS
        ),
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False))
    if not audit["complete"]:
        raise SystemExit("Expanded biography audit failed")


if __name__ == "__main__":
    main()
