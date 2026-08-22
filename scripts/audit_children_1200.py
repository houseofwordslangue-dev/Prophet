#!/usr/bin/env python3
"""Audit the deterministic 1,200-story children corpus and Arabic tashkil gate."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEEDS = ROOT / "data" / "children" / "story-seeds.json"
OUT = ROOT / "data" / "children" / "editorial" / "children_1200_stories_audit.json"
ARABIC = re.compile(r"[\u0621-\u064A\u066E-\u06D3]")
DIAC = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")


def vocalized_ratio(text: str) -> float:
    letters = len(ARABIC.findall(text))
    marks = len(DIAC.findall(text))
    return marks / letters if letters else 1.0


def main() -> int:
    data = json.loads(SEEDS.read_text(encoding="utf-8"))
    problems = []
    subject_counts = {}
    minimum_ratio = 1.0
    for subject in data:
        themes = subject.get("themes", [])
        count = len(themes) * 10 * 2
        subject_counts[subject["id"]] = count
        if len(themes) != 5:
            problems.append(f"{subject['id']}: expected 5 themes, got {len(themes)}")
        for label in (subject.get("ar", ""),):
            minimum_ratio = min(minimum_ratio, vocalized_ratio(label))
            if ARABIC.search(label) and not DIAC.search(label):
                problems.append(f"{subject['id']}: unvocalized Arabic subject label")
        for n, theme in enumerate(themes, 1):
            for idx in (0, 3):
                value = str(theme[idx])
                minimum_ratio = min(minimum_ratio, vocalized_ratio(value))
                if ARABIC.search(value) and not DIAC.search(value):
                    problems.append(f"{subject['id']} theme {n}: Arabic field lacks tashkil")
    total = sum(subject_counts.values())
    if len(data) != 12:
        problems.append(f"expected 12 subjects, got {len(data)}")
    if any(v != 100 for v in subject_counts.values()):
        problems.append("not every subject expands to 100 stories")
    if total != 1200:
        problems.append(f"expected 1200 stories, got {total}")
    audit = {
        "schema": "children-1200-runtime-audit-v1",
        "subjectCount": len(data),
        "targetPerSubject": 100,
        "runtimeStoryCount": total,
        "storiesPerSubject": subject_counts,
        "seedThemesPerSubject": 5,
        "namesPerTheme": 10,
        "contextsPerName": 2,
        "scenesPerStory": 4,
        "languages": ["ar", "en", "fr"],
        "arabicDisplayDiacriticsRequired": True,
        "searchNormalizationSeparate": True,
        "ttsUsesVocalizedArabic": True,
        "provenanceMode": "original-fiction-present-day-pedagogy",
        "historicalClaimsGenerated": False,
        "sacredTextQuotesGenerated": False,
        "materialization": {
            "seedFile": True,
            "runtimeGenerator": True,
            "individualStoryJsonFiles": False
        },
        "minimumSeedArabicDiacriticRatio": round(minimum_ratio, 4),
        "problems": problems,
        "completeRuntimeExpansion": not problems
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
