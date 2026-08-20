#!/usr/bin/env python3
"""Strict validator for genuine-source editorial articles.

This script does not generate articles. It only validates article records and
rolling 24-hour coverage. Any unsupported substantive paragraph or unverified
quotation fails publication eligibility.
"""
from __future__ import annotations
import argparse
import datetime as dt
import difflib
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "data" / "editorial_policy.json"
ARTICLES_DIR = ROOT / "data" / "editorial" / "articles"
SECTIONS_PATH = ROOT / "data" / "editorial_sections.json"
STATE_PATH = ROOT / "data" / "editorial_coverage_state.json"
REPORT_DIR = ROOT / "data" / "editorial" / "reports"


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def parse_time(value: str | None):
    if not value:
        return None
    try:
        v = value.replace("Z", "+00:00")
        t = dt.datetime.fromisoformat(v)
        return t if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def norm_text(text: str) -> str:
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text or "")
    text = text.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}))
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()


def fingerprint(article: dict) -> str:
    body = "\n".join(str(p.get("text", "")) for p in article.get("paragraphs", []))
    return hashlib.sha256(norm_text(body).encode("utf-8")).hexdigest()


def discover_sections() -> list[dict]:
    configured = load_json(SECTIONS_PATH, {})
    rows = configured.get("sections", []) if isinstance(configured, dict) else []
    out = []
    seen = set()
    for r in rows:
        if not r.get("active", True) or not r.get("editorial", True):
            continue
        key = str(r.get("id") or r.get("slug") or r.get("name") or "").strip()
        if key and key not in seen:
            seen.add(key); out.append(r)
    # Optional HTML discovery: pages can opt in with data-editorial-section.
    for html in ROOT.glob("*.html"):
        try:
            text = html.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for key in re.findall(r'data-editorial-section=["\']([^"\']+)', text):
            if key not in seen:
                seen.add(key); out.append({"id": key, "name": key, "active": True, "editorial": True, "discoveredFrom": html.name})
    return out


def load_articles() -> list[dict]:
    rows = []
    if ARTICLES_DIR.exists():
        for path in sorted(ARTICLES_DIR.glob("*.json")):
            obj = load_json(path, None)
            if isinstance(obj, dict):
                obj["_path"] = str(path.relative_to(ROOT)); rows.append(obj)
    return rows


def validate_article(a: dict, policy: dict) -> list[str]:
    errors = []
    gates = policy["publicationGates"]
    if a.get("contentType") not in policy.get("approvedContentTypes", []):
        errors.append("invalid contentType")
    if float(a.get("sourceCoveragePercent", -1)) != float(gates["sourceCoveragePercent"]):
        errors.append("source coverage is not 100%")
    if float(a.get("aiOriginalSubstantiveContentPercent", -1)) != 0:
        errors.append("AI-original substantive content is not 0%")
    if a.get("quotationVerification") != "PASS":
        errors.append("quotation verification failed")
    if a.get("provenanceStatus") != "PASS":
        errors.append("provenance failed")
    if int(a.get("unsupportedFactualParagraphs", -1)) != 0:
        errors.append("unsupported factual paragraphs present")
    if int(a.get("unverifiedQuotations", -1)) != 0:
        errors.append("unverified quotations present")
    paragraphs = a.get("paragraphs", [])
    if not paragraphs:
        errors.append("no substantive paragraphs")
    for i, p in enumerate(paragraphs, 1):
        if not str(p.get("text", "")).strip():
            errors.append(f"paragraph {i}: empty")
            continue
        refs = p.get("sourceRefs", [])
        if not refs:
            errors.append(f"paragraph {i}: no sourceRefs")
        if p.get("substantive", True) and p.get("aiOriginal", False):
            errors.append(f"paragraph {i}: AI-original substantive paragraph")
        if p.get("quotation") and p.get("quotationVerified") is not True:
            errors.append(f"paragraph {i}: quotation not verified")
    sources = a.get("sources", [])
    if not sources:
        errors.append("no provenance sources")
    for i, s in enumerate(sources, 1):
        if not (s.get("title") or s.get("resourceId") or s.get("originalUrl")):
            errors.append(f"source {i}: missing identifying provenance")
    return errors


def duplicate_pairs(articles: list[dict], threshold: float = 0.88):
    texts = [(a, norm_text(" ".join(str(p.get("text", "")) for p in a.get("paragraphs", [])))) for a in articles]
    out = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            ai, ti = texts[i]; aj, tj = texts[j]
            if not ti or not tj: continue
            ratio = difflib.SequenceMatcher(None, ti, tj).ratio()
            if ratio >= threshold:
                out.append({"a": ai.get("id") or ai.get("slug"), "b": aj.get("id") or aj.get("slug"), "similarity": round(ratio, 4)})
    return out


def audit(now: dt.datetime | None = None):
    policy = load_json(POLICY_PATH, None)
    if not policy:
        raise SystemExit("Missing data/editorial_policy.json")
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=int(policy.get("coverageWindowHours", 24)))
    sections = discover_sections()
    articles = load_articles()
    results = []
    qualifying = []
    rejected = []
    for a in articles:
        errs = validate_article(a, policy)
        if errs:
            rejected.append({"id": a.get("id") or a.get("slug"), "path": a.get("_path"), "errors": errs})
        else:
            qualifying.append(a)
    dups = duplicate_pairs(qualifying)
    dup_ids = {x["a"] for x in dups} | {x["b"] for x in dups}
    qualifying = [a for a in qualifying if (a.get("id") or a.get("slug")) not in dup_ids]
    for s in sections:
        key = str(s.get("id") or s.get("slug") or s.get("name"))
        candidates = []
        for a in qualifying:
            assigned = [str(x) for x in (a.get("sections") or [a.get("section")]) if x]
            published = parse_time(a.get("publishedAt"))
            if key in assigned and published and published >= cutoff:
                candidates.append(a)
        latest = max(candidates, key=lambda x: parse_time(x.get("publishedAt"))) if candidates else None
        results.append({"section": key, "name": s.get("name") or key, "covered": bool(latest), "latestArticle": (latest or {}).get("id") if latest else None, "latestPublishedAt": (latest or {}).get("publishedAt") if latest else None})
    covered = sum(1 for r in results if r["covered"])
    total = len(results)
    pct = round((covered / total * 100), 2) if total else 0.0
    report = {
        "generatedAt": now.isoformat(),
        "windowStart": cutoff.isoformat(),
        "windowHours": policy.get("coverageWindowHours", 24),
        "activeEditorialSections": total,
        "coveredSections": covered,
        "coveragePercent": pct,
        "articlesPublishedInStore": len(articles),
        "qualifyingGenuineArticles": len(qualifying),
        "aiGeneratedSubstantiveArticles": 0,
        "unsupportedFactualParagraphs": 0 if not qualifying else sum(int(a.get("unsupportedFactualParagraphs", 0)) for a in qualifying),
        "unverifiedQuotations": 0 if not qualifying else sum(int(a.get("unverifiedQuotations", 0)) for a in qualifying),
        "rejectedArticles": rejected,
        "duplicateExclusions": dups,
        "sections": results,
        "status": "PASS" if total > 0 and covered == total and not rejected and not dups else "FAIL"
    }
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write state and timestamped report")
    args = ap.parse_args()
    report = audit()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.write:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        (REPORT_DIR / f"coverage-{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if report["status"] == "PASS" else 2)

if __name__ == "__main__":
    main()
