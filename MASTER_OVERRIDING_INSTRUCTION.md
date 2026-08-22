# FINAL OVERRIDING MASTER INSTRUCTION

This file is the controlling instruction hierarchy for the Prophet Muhammad biography website and all related content pipelines, imports, OCR repair, generation, localization, children content, players, publication workflows, and future automation.

If any earlier prompt, script, template, importer, generator, renderer, data file, workflow, or automation conflicts with this instruction, **this instruction takes precedence** unless a later instruction explicitly states that it supersedes this file.

## 1. HIGHEST PRIORITY — AUTHENTICITY, SOURCE FIDELITY, AND NO FABRICATION

1. Historical facts, biographies, events, battles, sayings, Qur'anic passages, Hadith, classical quotations, chains of transmission, dates, relationships, and source attributions must never be invented.
2. Source quotations must preserve authentic wording. Editorial cleanup may correct OCR, spacing, punctuation, encoding, and verified vocalization, but must not silently change substantive meaning.
3. For historical or religious content, when the evidence is insufficient, ambiguous, contradictory, or unrecoverable, mark it for review rather than inventing a completion.
4. Numerical production targets, publication quotas, page-count targets, word-count targets, and automation speed must never override source truth or quality gates.
5. Source-derived content and original/generated educational content must remain distinguishable in the content system and provenance metadata.

## 2. SOURCE PRIORITY AND PROVENANCE

For source recovery, verification, OCR repair, quotation checking, and article extraction, prefer witnesses in this order when practical:

1. original scan or photographed source witness;
2. verified editions already stored in Google Drive or repository storage;
3. repository copies and previously ingested verified extracts;
4. EPUB, native text, or searchable text derived from the same edition;
5. other listed site resources and corroborating editions;
6. legally usable/open copies from reliable external repositories.

Always retain provenance sufficient to identify the source, edition or witness where known, repository/Drive path or identifier when available, extraction record, and repair history.

## 3. OCR REPAIR, PROOFREADING, CROSS-VERIFICATION, AND AUTO-PUBLICATION

Corrupted Arabic OCR must not be discarded by default.

For collapsed, merged, broken, corrupted, or previously rejected OCR:

1. retain the original OCR for audit;
2. compare against the original scan and alternate witnesses;
3. restore missing spaces, letters, broken words, line order, paragraph boundaries, punctuation, page splits, and Unicode normalization;
4. correct OCR substitutions and duplicated scanning noise only when supported by the source;
5. use AI only as a linguistic repair/proofreading assistant, never as a substitute for source evidence;
6. preserve the authentic source wording;
7. verify exact person ownership before attaching repaired material to a biography;
8. automatically publish the repaired passage when sufficiently corroborated, coherent, correctly attributed, and free of unresolved substantive contradiction;
9. keep truly unresolved material in review/quarantine;
10. automatically reconsider quarantined OCR when new source witnesses become available.

**Rule:** VERIFIED REPAIR -> AUTO PUBLICATION. UNRESOLVED TEXT -> REVIEW. NEVER INVENT RECONSTRUCTION.

## 4. CANONICAL PERSON / BIOGRAPHY PLACEMENT

1. One person = one canonical biography page.
2. Explicit biography/life-profile material about a person belongs on that person's canonical page.
3. Supporting source extracts may appear as canonical biography chapters/extensions attached to that person.
4. Thematic articles may remain in thematic sections when their primary purpose is thematic rather than biographical.
5. Name-only incidental mentions do not justify reassignment to a person's biography.
6. Cross-person or incidental-name matches must not be used as biography evidence.
7. Narrators, family members, companions, followers, ancestors, and other indexed people should route to their canonical person page where such a page exists.

## 5. CHILDREN SECTION — MANDATORY ARABIC DIACRITICS

For every child-facing Arabic text in the children section «أَحْبَابُ اللهِ», correct Arabic diacritics (التَّشْكِيلُ) are mandatory.

This includes, without limitation:

- story titles and subtitles;
- narration and scene text;
- dialogue;
- moral/value summaries;
- player controls, buttons, instructions, and labels;
- age-group descriptions and category names;
- educational notes and captions;
- quizzes and exercises;
- illustrated stories;
- animated stories;
- very short stories;
- children's biographies;
- children's media descriptions;
- accessibility text intended to be read aloud;
- Arabic text sent to TTS/narration.

### Tashkil rules

1. Vocalization must be linguistically reviewed, not mechanically guessed.
2. Determine intended meaning and grammatical context before adding diacritics.
3. Verify names, uncommon vocabulary, homographs, passive/active forms, and classical wording.
4. Preserve correct hamza forms, shadda, sukun, tanwin, ta marbuta, alif maqsurah, and orthographic conventions.
5. Historical/religious names must use established pronunciation.
6. For Qur'anic, Hadith, or classical quotations, use an authoritative vocalized witness where available; do not alter the underlying wording.
7. If a verified vocalized version exists, it must never be overwritten by an unvocalized version.

### Display and search separation

Maintain two forms where needed:

- **DISPLAY/TTS FORM:** verified vocalized Arabic;
- **SEARCH-NORMALIZED FORM:** internal Arabic with diacritics removed for forgiving search only.

The normalized search form must never replace the public display or TTS form.

### Publication gate

If child-facing Arabic is insufficiently vocalized:

`STATUS = FAIL_TASHKIL`

Route automatically through:

`AI LINGUISTIC REVISION -> TASHKIL -> PROOFREADING -> TTS TEST -> PUBLICATION`

## 6. CHILDREN CONTENT ORIGIN AND HISTORICAL SAFETY

1. Source-extracted children's stories and original/generated educational stories must remain clearly distinguishable.
2. Original educational fiction is allowed for general values, learning, language, family, cooperation, curiosity, and similar modern educational themes.
3. Generated fiction must never masquerade as a real historical event, Prophetic saying, Companion story, Qur'anic account, Hadith, or source-derived report.
4. For Seerah, Prophets, Ahl al-Bayt, Companions, Followers, and other historical/religious figures, use verified source-derived material for factual episodes.
5. Numerical goals such as "100 stories per section" do not authorize invented sacred or historical material.
6. Children animation must follow the site's existing non-depiction policy for sacred historical figures where applicable.

## 7. CHILDREN AGE-ADAPTIVE STORY SYSTEM

Age range may change presentation, but never source truth.

### Ages 5–7
- short sentences;
- large readable typography;
- gentle pacing;
- simple cause-and-effect;
- bright, soft visual style;
- minimal interaction complexity.

### Ages 8–10
- clearer adventure structure;
- teamwork/problem-solving;
- richer movement;
- moderate sentence length;
- simple interactive choices where appropriate.

### Ages 11–13
- deeper questions;
- observation and learning structure;
- more visual layers;
- richer vocabulary;
- reflective endings.

### Ages 14–16
- mature but age-appropriate narrative structure;
- ethical tension and responsibility;
- subtler visual style;
- more cinematic motion;
- longer scenes and more nuanced language.

Age adaptation may simplify explanation but must never change quotations, historical facts, attribution, or source meaning.

## 8. AUDIO / TTS / NARRATION

1. Arabic narration must receive the same verified vocalized Arabic displayed to the child.
2. Do not strip tashkil before Arabic TTS.
3. Language-specific voices must be verified before use.
4. Arabic path: prefer `ar-SA` or another verified Arabic voice.
5. French path: prefer `fr-FR` or another verified French voice.
6. English path: prefer `en-US`, `en-GB`, or another verified English voice.
7. Reject Chinese, Japanese, Korean, or other mismatched voices from the English path even if a browser incorrectly exposes them as defaults.
8. If no safe local voice exists, use the approved network TTS fallback used by the children player.
9. Never silently claim that narration played when it failed; expose a clear user-visible audio status/fallback message.
10. Playback speed may vary by age but must remain intelligible.

## 9. LOCALIZATION

1. Arabic, English, and French public versions must be fully localized.
2. Arabic pages should not leak Latin-script content except necessary technical terms, language selectors, identifiers, or source metadata where unavoidable.
3. English pages should present English UI/content.
4. French pages should present French UI/content.
5. Language switching must change interface text, story text, narration locale, controls, metadata labels, and directionality consistently.
6. Arabic children content must remain vocalized after localization and rendering.

## 10. ARTICLES, SAYINGS, AND EDITORIAL CONTENT

1. Sayings attributed to the Prophet, Companions, Followers, or Followers of Followers must be preserved as actually found in listed sources and clearly attributed.
2. Other unattributed sayings may remain unattributed according to the existing site editorial policy.
3. Research articles must be extracted from, or written strictly on the basis of, listed/site resources.
4. No unsupported external ideas or invented historical details may be integrated into source-derived research articles.
5. AI may organize, translate, summarize, linguistically revise, or structure source-supported material, but may not fabricate evidence.
6. Metadata should retain author, extracted-from title, publisher, source list, and editorial attribution where applicable.

## 11. RESOURCE INGESTION AND RIGHTS

1. Prefer public-domain, open, authorized, or otherwise legally usable materials for local ingestion.
2. Respect applicable license terms, including attribution/share-alike/non-commercial requirements where relevant.
3. Do not infer that a modern edition is unrestricted merely because an older underlying work is public domain.
4. Multiple mirrors/servers may be used for availability and resilience where lawful.
5. A source being discoverable online does not by itself establish permission for unrestricted local republication.

## 12. PLAYERS, READERS, AND FUNCTIONALITY

1. No fake buttons or placeholder actions presented as working features.
2. Read/listen/watch controls must perform the stated action or clearly report why unavailable.
3. Selecting a different media item must actually load the selected media.
4. CSP, service-worker, localization, mobile-navigation, audio, video, and reader failures must be treated as functional defects.
5. Do not mark a player/reader feature complete until it has been tested in the relevant runtime.

## 13. PUBLICATION STATUS VOCABULARY

Never conflate the following states:

1. **SOURCE FOUND / VERIFIED** — source located and identified;
2. **FILE ACQUIRED** — binary/text obtained;
3. **INDEXED IN SITE DATA** — record represented in site data;
4. **LOCAL MATERIALIZED** — content physically exists in repository/storage and is verified;
5. **MERGED TO MAIN** — repository default branch contains it;
6. **DEPLOYED / LIVE** — hosting environment serves it;
7. **TESTED LIVE** — public/runtime behavior verified.

Do not say "published" or "live" when work is only on a feature branch, in a PR, or materialized locally.

## 14. QUALITY GATES AND NO-DEGRADATION

Once a higher-quality verified state exists, later automation must not replace it with a lower-quality state.

Examples:

- verified source text must not be replaced by guessed OCR;
- repaired OCR must not be replaced by corrupted OCR;
- verified tashkīl must not be stripped from child-facing display/TTS;
- verified person ownership must not be replaced by name-only matching;
- verified language voice mapping must not be replaced by a wrong browser default;
- complete localization must not be overwritten by mixed-language UI;
- source provenance must not be removed by later transforms.

Any pipeline that would cause degradation must fail safely and preserve the previous verified version.

## 15. CONFLICT-RESOLUTION ORDER

When two instructions conflict, apply the following order:

1. Authenticity / no fabrication / preservation of source truth;
2. exact source wording and provenance;
3. verified OCR repair and cross-verification;
4. correct canonical person/content placement;
5. mandatory child Arabic tashkīl and child safety;
6. correct localization and TTS voice mapping;
7. rights/license constraints for local ingestion/publication;
8. functional correctness of reader/player/site behavior;
9. editorial style and age-adaptive presentation;
10. numerical targets, speed targets, automation cadence, and volume goals.

**Lower-priority goals must never override higher-priority rules.**

## 16. AUTOMATION AND CONTINUOUS ENFORCEMENT

All future importers, generators, OCR jobs, localization jobs, story generators, article generators, media processors, and publication workflows should enforce this hierarchy automatically.

Recommended validation sequence:

`SOURCE/ORIGIN CHECK -> PROVENANCE -> OCR/CONTENT INTEGRITY -> PERSON OWNERSHIP/PLACEMENT -> CHILD TASHKIL IF APPLICABLE -> LOCALIZATION -> TTS/VOICE CHECK -> RIGHTS/PUBLICATION CHECK -> RENDER/FUNCTION TEST -> PUBLISH`

For children Arabic:

`ARABIC SOURCE/TEXT -> LINGUISTIC REVIEW -> TASHKIL -> PROOFREAD -> DISPLAY/TTS CONSISTENCY -> AUDIO TEST -> PUBLISH`

For repaired OCR:

`ORIGINAL OCR -> SOURCE WITNESS COMPARISON -> VERIFIED REPAIR -> AUDIT RECORD -> AUTO PUBLICATION`

## 17. FINAL OVERRIDING RULE

When in doubt:

- preserve authentic wording;
- preserve provenance;
- do not invent historical or religious content;
- repair rather than discard when a reliable repair is possible;
- quarantine rather than fabricate when it is not;
- show children verified vocalized Arabic;
- send the same vocalized Arabic to TTS;
- use only verified language-appropriate voices;
- keep original/generated educational fiction clearly separate from sourced history;
- never let content quotas override truth or publication quality;
- never call work published until it is actually merged, deployed, and verified at the claimed stage.

This file supersedes conflicting earlier project instructions and should be treated as the final controlling master prompt unless a later explicit instruction states that it replaces this file.