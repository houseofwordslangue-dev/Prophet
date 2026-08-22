#!/usr/bin/env python3
# GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
EDITORIAL = ROOT / "data" / "editorial"
DRAFTS = EDITORIAL / "drafts" / "2026-08-21"
SUPPLEMENT = EDITORIAL / "publication_supplement.json"
AUDIT = EDITORIAL / "khadija_1000_audit.json"
INDEX = EDITORIAL / "person_article_index.json"

PERSON_NAME = "خديجة بنت خويلد"
PERSON_KEY = "khadija-bint-khuwaylid"
PERSON_URL = "person.html?name=" + quote(PERSON_NAME)
PREFIX = "20260821-khadija-compiled-"


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main():
    files = sorted(DRAFTS.glob("khadija-long-batch-*.json"))
    if len(files) != 20:
        raise SystemExit(f"Expected 20 Khadija batches, found {len(files)}")

    articles = []
    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        drafts = data.get("drafts", [])
        for article in drafts:
            if not str(article.get("id", "")).startswith(PREFIX):
                continue
            section = article.get("section")
            subsection = article.get("subsection")
            category_ar = article.get("categoryAr") or subsection or "مادة بحثية"
            number = str(article["id"]).rsplit("-", 1)[-1]

            # One person = one canonical biography. These are supporting thematic articles.
            article["articleRole"] = "supporting-research"
            article["canonicalBiography"] = False
            article["relatedPerson"] = {
                "key": PERSON_KEY,
                "nameAr": PERSON_NAME,
                "canonicalUrl": PERSON_URL,
            }
            article["subjectPerson"] = PERSON_KEY
            article["title"] = f"{category_ar}: خديجة رضي الله عنها — مادة مصدرية {number}"
            article["sections"] = [f"{section}/{subsection}"]
            article["placementPolicy"] = "single-thematic-home-section"
            articles.append(article)

        data["organizationPolicy"] = {
            "personPage": "canonical-biography-only",
            "articleRole": "supporting-research",
            "placement": "relevant-thematic-section",
        }
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if len(articles) != 1000:
        raise SystemExit(f"Expected 1000 reorganized Khadija articles, got {len(articles)}")
    if len({a["id"] for a in articles}) != 1000:
        raise SystemExit("Duplicate Khadija article IDs")
    if any(a.get("canonicalBiography") is not False for a in articles):
        raise SystemExit("Supporting article incorrectly marked canonical")
    if any(len(a.get("sections", [])) != 1 for a in articles):
        raise SystemExit("Every supporting article must have exactly one thematic home")

    section_counts = Counter(a["section"] for a in articles)
    category_counts = Counter(a.get("category") for a in articles)
    article_index = {
        "schema": "person-article-index-v1",
        "generatedAt": now(),
        "policy": {
            "canonicalBiographyPerPerson": 1,
            "supportingArticlesRemainThematic": True,
            "personPagesDoNotDuplicateSupportingArticles": True,
        },
        "people": {
            PERSON_KEY: {
                "nameAr": PERSON_NAME,
                "canonicalUrl": PERSON_URL,
                "canonicalBiographyCount": 1,
                "supportingArticleCount": 1000,
                "sectionCounts": dict(section_counts),
                "categoryCounts": dict(category_counts),
                "articles": [
                    {
                        "id": a["id"],
                        "title": a["title"],
                        "section": a["section"],
                        "subsection": a["subsection"],
                        "url": "feature.html?id=" + a["id"],
                    }
                    for a in articles
                ],
            }
        },
    }
    INDEX.write_text(json.dumps(article_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    supplement = json.loads(SUPPLEMENT.read_text(encoding="utf-8"))
    kh = supplement.setdefault("khadija1000", {})
    kh.update({
        "organization": "one-canonical-biography-plus-thematic-supporting-articles",
        "canonicalPersonKey": PERSON_KEY,
        "canonicalPersonName": PERSON_NAME,
        "canonicalPersonUrl": PERSON_URL,
        "canonicalBiographyCount": 1,
        "supportingArticleCount": 1000,
        "personAreaSupportingArticleCount": 0,
        "siteSections": dict(section_counts),
    })
    supplement["personPublicationPolicy"] = {
        "canonicalBiographyPerPerson": 1,
        "supportingArticlesPlacement": "relevant-section-only",
        "supportingArticlesLinkedToCanonicalPerson": True,
    }
    SUPPLEMENT.write_text(json.dumps(supplement, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if AUDIT.exists():
        audit = json.loads(AUDIT.read_text(encoding="utf-8"))
        audit["reorganizedAt"] = now()
        audit["canonicalBiographyCount"] = 1
        audit["supportingArticleCount"] = 1000
        audit["personAreaSupportingArticleCount"] = 0
        audit["siteSections"] = dict(section_counts)
        audit["organizationPolicy"] = "one-person-one-canonical-biography; supporting articles live in relevant thematic sections"
        AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "canonicalBiography": 1,
        "supportingArticles": 1000,
        "personAreaSupportingArticles": 0,
        "siteSections": dict(section_counts),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
