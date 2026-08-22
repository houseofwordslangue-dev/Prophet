# AUTO CHILDREN MEDIA & STORY COMPLETION PROMPT

GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md

This is a standing automation instruction for the Prophet Muhammad biography website children section «أَحْبَابُ اللهِ». It is subordinate to `MASTER_OVERRIDING_INSTRUCTION.md`; if any rule conflicts, the overriding master instruction wins.

## 1. Objective

Continuously discover, import/index, classify, revise, proofread, audit and publish child-appropriate media and source material on a rotating basis, while continuously extracting/adapting/generating stories according to the controlling master instruction.

The children section includes media, verified readings, illustrated stories, very short stories and animated stories. Use the live taxonomy in `data/children/taxonomy.json`; do not hard-code a taxonomy that can become stale.

## 2. Rotating acquisition queues

Maintain independent resumable queues for:

1. channels;
2. videos;
3. audio;
4. books;
5. articles/research/verified readings;
6. transcripts;
7. source-derived historical/religious stories;
8. original educational fiction allowed by the master instruction.

Rotate between queues so one unavailable source never blocks the others.

Recommended cycle:

`CHANNELS -> VIDEOS -> AUDIO -> BOOKS -> ARTICLES -> TRANSCRIPTS -> SOURCE STORIES -> EDUCATIONAL FICTION -> AUDIT -> PUBLISH -> REPEAT`

## 3. Channel target

Target: **100 verified child-appropriate channels**.

A channel counts only when it has:

- stable canonical identity/URL;
- child-appropriate relevance;
- language metadata;
- subject/category classification;
- provenance/discovery record;
- no duplicate canonical channel ID;
- usable media or educational value relevant to the children taxonomy.

Current known channels in `data/children/media-sources.json` are seed sources, not the final list.

Stop the channel-discovery expansion phase when `verifiedChannelCount >= 100`, but continue refreshing metadata and checking availability.

Do not download or republish copyrighted channel/video media merely because it is publicly viewable. Prefer metadata, embeds/links, transcripts where permitted, or locally ingested media only when rights permit.

## 4. Video target

Target: **1,000 unique verified child-appropriate videos**.

Each video must have, when available:

- canonical video ID;
- channel ID;
- title;
- language;
- subject/category;
- age suitability;
- source URL;
- duration;
- transcript/captions provenance if used;
- publication/playback mode;
- rights/embedding/local-ingestion status;
- duplicate fingerprint.

Videos must be playable through the site's real player/approved embed path or clearly marked unavailable; never expose fake play buttons.

Stop new-video target acquisition when `verifiedVideoCount >= 1000`, while continuing availability checks and replacement of dead/removed items.

## 5. Audio, books and articles

Import/index child-relevant audio, books and articles continuously on the same rotating basis.

No arbitrary numerical quota is imposed on these three media types unless a later instruction defines one.

Prefer:

- verified local/repository/Drive resources;
- public-domain/open/authorized works;
- native text before OCR;
- transcripts before guessed summaries;
- exact source metadata and provenance.

For books/articles, extract child-appropriate passages only when the relationship to the source is preserved.

For audio/video transcripts, distinguish official captions/transcripts, verified human transcription and machine transcription.

## 6. Story matrix target

Use the live children taxonomy. Treat every combination of:

`SUBJECT CATEGORY × AGE GROUP`

as an independent story target cell.

Current taxonomy contains 12 subject categories and 8 age-group entries, therefore the present matrix contains 96 target cells. With a target of 5,000 stories per cell, the current maximum completion target is **480,000 story records**, subject to future taxonomy changes.

Target per cell: **5,000 unique publishable stories**.

The controller must recalculate this matrix from `data/children/taxonomy.json` on every cycle rather than assuming 96 forever.

Prioritize:

1. empty cells;
2. lowest-count cells;
3. underrepresented age groups;
4. underrepresented subjects;
5. source-derived historical/religious stories with verified evidence;
6. allowed original educational fiction for general values/learning.

Never create filler merely to reach 5,000.

## 7. Story origin classes

Every story must be explicitly classified internally as one of:

- `SOURCE_EXTRACTED_CHILD_STORY`
- `SOURCE_ADAPTED_CHILD_STORY`
- `SOURCE_TRANSLATED_CHILD_STORY`
- `SOURCE_TRANSCRIPT_ADAPTATION`
- `ORIGINAL_EDUCATIONAL_FICTION`
- `LEGACY_UNSOURCED_STORY`

Never relabel generated/original fiction as sourced history.

Legacy unsourced stories may remain but do not count as source-backed historical evidence.

## 8. Sacred/historical safety

For Seerah, Prophet Muhammad ﷺ, Prophets, Ahl al-Bayt, Companions, Followers, Followers of Followers and other historical/religious figures:

- use verified source-derived factual episodes only;
- never invent dialogue, events, chronology, miracles, relationships, quotations or historical details;
- AI may structure, simplify, translate and linguistically revise source-supported material;
- if evidence is insufficient, mark `NEEDS_SOURCE` and move to another queue/cell.

Original educational fiction is permitted only for general values, family, cooperation, curiosity, learning, responsibility, nature, language and similar non-historical themes allowed by the master instruction.

## 9. Age adaptation

Use the live age groups in `data/children/taxonomy.json` and apply the age-adaptive rules from the overriding master.

Age adaptation changes presentation, sentence length, vocabulary, pacing, visual complexity and interaction depth; it must never alter source truth.

Each story must carry an explicit `ageGroup` and `subjectCategory` matching a live taxonomy cell.

## 10. Arabic tashkīl requirement

All child-facing Arabic must satisfy the master instruction's mandatory vocalization rule.

Before publication:

`ARABIC TEXT -> LINGUISTIC REVIEW -> TASHKIL -> PROOFREAD -> DISPLAY/TTS CONSISTENCY -> TTS TEST -> PUBLISH`

Maintain:

- vocalized display/TTS Arabic;
- separate diacritic-stripped search-normalized Arabic.

Never publish insufficiently vocalized Arabic child content merely to satisfy story targets.

## 11. Localization

Every publishable story should support Arabic, English and French according to the master localization rules.

Do not mark a locale complete when substantial story content remains untranslated.

For source quotations, preserve authentic wording and clearly distinguish translation from original text.

## 12. Uniqueness and duplication control

Before creating a story, compare:

- source fingerprint;
- plot/episode fingerprint;
- title/slug;
- subject;
- age group;
- characters;
- scene structure;
- moral/value;
- semantic similarity.

Merge/enrich instead of duplicating substantially identical source stories.

For original educational fiction, require a distinct narrative identity; template permutations do not count as unique stories.

## 13. Media-to-story extraction

When a video/audio/book/article contains usable child material:

1. register the source;
2. obtain lawful/usable transcript or text;
3. retain provenance;
4. classify factual vs educational/fictional material;
5. extract source-supported facts/episodes;
6. adapt to the appropriate age group;
7. apply Arabic tashkīl;
8. localize;
9. proofread;
10. audit historical/source fidelity;
11. publish only after passing the children publication gate.

Do not treat a secondary children's cartoon invention as historical evidence merely because it mentions a historical figure.

## 14. Rotating batch behavior

Use small resumable batches rather than attempting the entire target in one run.

Recommended priorities per scheduled run:

- one acquisition/media queue;
- one or more lowest-count story cells;
- deterministic checkpoint;
- strict validation;
- commit/publish only verified output.

If a source/network/API is unavailable, mark it retryable and continue with another queue. Ordinary acquisition misses must not create notification storms.

## 15. Publication states

Use explicit states:

`DISCOVERED`
`SOURCE_VERIFIED`
`TRANSCRIPT_READY`
`TEXT_READY`
`ADAPTATION_READY`
`TASHKIL_REQUIRED`
`PROOFREAD`
`READY_TO_PUBLISH`
`PUBLISHED`
`NEEDS_SOURCE`
`NEEDS_RIGHTS_REVIEW`
`NEEDS_REVIEW`
`FAILED_RETRYABLE`

Do not call an item published unless it is at the publication stage defined by the overriding master.

## 16. Machine-readable state

Maintain a status ledger with at least:

- `verifiedChannelCount`
- `channelTarget = 100`
- `CHANNEL_TARGET_COMPLETE`
- `verifiedVideoCount`
- `videoTarget = 1000`
- `VIDEO_TARGET_COMPLETE`
- counts for audio/books/articles/transcripts
- live subject categories
- live age groups
- `storyTargetPerCell = 5000`
- `storyCountsBySubjectAgeCell`
- `underTargetStoryCells`
- `emptyStoryCells`
- `nextStoryTargetCell`
- `totalStoryCount`
- `calculatedStoryMatrixTarget`
- `STORY_TARGET_COMPLETE`
- `CHILDREN_MEDIA_STORY_COMPLETION_COMPLETE`

`CHILDREN_MEDIA_STORY_COMPLETION_COMPLETE=true` only when:

- at least 100 verified channels exist;
- at least 1,000 verified videos exist;
- every live subject × age-group story cell has at least 5,000 qualifying stories;
- all publication/integrity requirements remain satisfied.

Even after target completion, lightweight availability/provenance maintenance may continue without creating filler.

## 17. Absolute hierarchy

Targets are operational goals only.

The controlling order remains:

`AUTHENTICITY -> SOURCE FIDELITY -> PROVENANCE -> CHILD SAFETY/TASHKIL -> LOCALIZATION -> RIGHTS -> FUNCTIONALITY -> QUALITY -> NUMERICAL TARGETS`

Never reduce a higher-priority requirement to reach 100 channels, 1,000 videos or 5,000 stories per taxonomy cell.
