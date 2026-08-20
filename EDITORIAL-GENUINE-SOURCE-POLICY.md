# Automated Genuine-Source Editorial Coverage

## Enforcement status

This repository applies a strict **source-only editorial rule** to every article published by the Prophet Muhammad site.

**AI is the linguistic editor, not the author or source.**

## Absolute rule

Substantive article prose MUST originate from approved, genuine source material already available to the editorial system, including approved books, scholarly/historical articles, research papers, manuscripts, verified OCR, lectures, lessons, conferences, verified audio/video transcriptions, approved translations, and other approved ingested resources.

AI MAY ONLY perform linguistic correction, grammar, spelling, punctuation, typography, readability improvements, removal of obvious repetition, heading organization, correction of OCR/ASR errors when the source clearly establishes the correction, and faithful translation when required.

AI MUST NOT invent, expand, interpret from its own knowledge, summarize from its own knowledge, create facts, arguments, examples, quotations, missing information, or original substantive paragraphs.

## Author attribution rule

Public bylines MUST reflect provenance rather than editorial convenience.

- If an article is 100% source-authentic, contains no AI-original substantive prose, passes provenance verification, and is derived from one attributable source only, display that source author's name.
- If the source is the Qur'an, display `القرآن الكريم` as the source attribution rather than inventing a human author.
- If an article combines two or more references/sources, display `هيئة تحرير الموقع`.
- If a single authentic source has no reliably established author identity, display `هيئة تحرير الموقع` rather than guessing an author.
- AI must never be displayed as the author.

## Production pipeline

REAL SOURCE MATERIAL → extract passages → OCR/transcribe when necessary → verify against original → select coherent source material → arrange into article structure → linguistic revision only → source-fidelity validation → publish.

## Rolling 24-hour coverage

Every active editorial section and relevant subsection must receive at least one new genuine source-derived article in each rolling 24-hour window.

For each cycle:

1. Discover active editorial sections/subsections from the current site and editorial configuration.
2. Determine the latest qualifying genuine article in each.
3. Prioritize uncovered sections.
4. Find unused approved material relevant to each uncovered section.
5. Extract/verify/assemble source material.
6. Apply linguistic revision only.
7. Validate every substantive paragraph against its source.
8. Reject duplicates rather than AI-rewriting them to look different.
9. Publish only after all integrity gates pass.
10. If authentic material is insufficient, record `SOURCE GAP — NO GENUINE ARTICLE PUBLISHED` and leave that section uncovered.

## Provenance

Every article must retain an internal provenance map containing every available field:

- source title;
- author/source attribution;
- edition;
- volume;
- page(s);
- chapter/section;
- original URL/resource ID;
- OCR extraction reference;
- audio/video title;
- timestamp(s);
- transcription reference;
- translation source.

Every substantive paragraph must carry one or more source references.

## Allowed internal content types

- `SOURCE ARTICLE`
- `EXTRACTED BOOK MATERIAL`
- `TRANSCRIBED LECTURE`
- `TRANSLATED SOURCE`
- `EDITORIALLY COMPILED SOURCE ARTICLE`

## Quotations

Quoted text must be copied from a verified source. It may not be fabricated, reconstructed from memory, silently changed, or attributed without evidence. Linguistic revision must not alter quoted text.

## Mandatory publication gates

An article may be published only when all are true:

- `SOURCE COVERAGE = 100%`
- `AI-ORIGINAL SUBSTANTIVE CONTENT = 0%`
- `QUOTATION VERIFICATION = PASS`
- `PROVENANCE = PASS`
- `UNSUPPORTED FACTUAL PARAGRAPHS = 0`
- `UNVERIFIED QUOTATIONS = 0`
- duplicate check passes against all published articles

Anything failing any gate MUST NOT be published.

## Administrator report

After each coverage cycle send a concise report to `houseofwords.langue@gmail.com` with subject `24-Hour Genuine Editorial Coverage Report`.

Report: period, sections scanned, already covered, requiring articles, articles published, titles, assignments, source types, principal sources, pages/timestamps, article URLs, OCR/ASR warnings, rejected drafts, duplicate exclusions, source gaps, remaining uncovered sections, overall coverage percentage, and these integrity metrics:

- Articles published: X
- Genuine source-derived articles: X
- AI-generated substantive articles: 0
- Articles with 100% source provenance: X
- Unsupported factual paragraphs: 0
- Unverified quotations: 0

Final status is `PASS` only when every eligible section has a qualifying genuine source-derived article within the preceding 24 hours and zero substantive articles were AI-generated.
