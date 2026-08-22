# AUTO CHILDREN MEDIA & STORY COMPLETION PROMPT

GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md

This is a standing automation instruction for the Prophet Muhammad biography website children section «أَحْبَابُ اللهِ». It is subordinate to `MASTER_OVERRIDING_INSTRUCTION.md`; if any rule conflicts, the overriding master instruction wins.

## 1. Objective

Continuously discover, import/index, classify, revise, proofread, audit and publish child-appropriate media and source material on a rotating basis, while continuously extracting/adapting/generating stories according to the controlling master instruction.

Always read the live children taxonomy from `data/children/taxonomy.json`. Every current and future active children content section must be included automatically; do not hard-code a permanently closed list.

Current children content sections include:

1. `verified-readings` — قراءات موثقة / Verified readings;
2. `illustrated-stories` — قصص مصوّرة / Illustrated stories;
3. `very-short-stories` — قصص قصيرة جدًا / Very short stories;
4. `animated-stories` — قصص متحركة / Animated stories;
5. `media` — فيديو وصوت / Video & audio.

Any later children content type added to the live taxonomy automatically becomes part of this rotating system.

## 2. All-children-section rotation

Maintain independent resumable queues for every children content section and every source/media class.

Required rotating queues include at least:

1. verified readings;
2. illustrated stories;
3. very short stories;
4. animated stories;
5. videos;
6. audio;
7. channels;
8. books;
9. articles/research;
10. transcripts/captions;
11. source-derived historical/religious stories;
12. source-adapted educational stories;
13. original educational fiction allowed by the master instruction;
14. localization;
15. Arabic tashkīl/proofreading;
16. TTS/audio preparation;
17. artwork/animation metadata and functional-player validation;
18. audit/publication.

Rotate between queues so one unavailable source or unfinished content type never blocks the others.

Recommended cycle:

`CHANNELS -> VIDEOS -> AUDIO -> BOOKS -> ARTICLES -> TRANSCRIPTS -> VERIFIED READINGS -> ILLUSTRATED STORIES -> VERY SHORT STORIES -> ANIMATED STORIES -> LOCALIZATION/TASHKIL -> PLAYER/TTS CHECK -> AUDIT -> PUBLISH -> REPEAT`

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

## 5. Audio, books, articles, transcripts and verified readings

Import/index child-relevant audio, books, articles, transcripts and verified readings continuously on the same rotating basis.

No arbitrary numerical quota is imposed on these media/source types unless a later instruction defines one.

Prefer:

- verified local/repository/Drive resources;
- public-domain/open/authorized works;
- native text before OCR;
- transcripts before guessed summaries;
- exact source metadata and provenance.

For books/articles, extract child-appropriate passages only when the relationship to the source is preserved.

For audio/video transcripts, distinguish official captions/transcripts, verified human transcription and machine transcription.

Verified readings must remain source-grounded and should be classified by live subject category and age suitability where applicable.

## 6. Story-bearing children sections

Every story-bearing children content type is an independent completion dimension.

Current story-bearing types are:

- `illustrated-stories`;
- `very-short-stories`;
- `animated-stories`.

If another story-bearing content type is later added to `data/children/taxonomy.json`, automatically include it.

Do not count the same story record simultaneously as several completed story types unless it genuinely has distinct, validated manifestations for those types. For example, a source story may have a separate illustrated adaptation and animated adaptation, but each manifestation must have its own validated content-type record and functional assets/metadata.

## 7. Story matrix target

Use the live children taxonomy. Treat every combination of:

`STORY-BEARING CONTENT TYPE × SUBJECT CATEGORY × AGE GROUP`

as an independent story target cell.

Target per cell: **5,000 unique publishable stories**.

The current taxonomy contains 3 story-bearing content types, 12 subject categories and 8 age-group entries. Therefore the current matrix contains 288 independent story cells and the present maximum completion target is:

**3 × 12 × 8 × 5,000 = 1,440,000 story manifestations**

subject to future taxonomy changes.

The controller must recalculate this matrix from `data/children/taxonomy.json` on every cycle rather than assuming the current counts forever.

Prioritize:

1. empty content-type × subject × age cells;
2. lowest-count cells;
3. empty/short existing stories that can be safely enriched;
4. underrepresented age groups;
5. underrepresented subjects;
6. source-derived historical/religious stories with verified evidence;
7. allowed original educational fiction for general values/learning.

Never create filler merely to reach 5,000.

## 8. Content-type requirements

### Illustrated stories

Each publishable illustrated-story record should include, as applicable:

- complete age-adapted story text;
- Arabic/English/French localization;
- verified Arabic tashkīl;
- cover/illustration metadata or usable illustration assets;
- accessibility text;
- source/origin class;
- subject and age classification;
- source provenance when source-derived;
- duplicate/story fingerprint;
- real reader/display behavior.

### Very short stories

Each publishable very-short-story record should include:

- genuinely concise age-appropriate narrative rather than a truncated long story;
- complete AR/EN/FR localization;
- verified Arabic tashkīl;
- clear value/learning objective;
- origin/provenance class;
- subject and age classification;
- duplicate fingerprint;
- no invented historical/religious detail.

### Animated stories

Each publishable animated-story record should include, as applicable:

- complete story/script;
- scene structure/storyboard;
- age-adaptive pacing;
- AR/EN/FR localization;
- verified vocalized Arabic for display and TTS;
- character/setting/scene metadata;
- animation/visual instructions or validated local assets;
- narration/TTS metadata;
- accessibility metadata;
- functional watch/listen behavior or an explicit availability state;
- origin/provenance class;
- duplicate/episode fingerprint.

Do not mark `animationReady`, `audioReady`, `watchMode`, or equivalent fields as ready if the actual function/assets do not support that claim.

### Verified readings

Continuously extract and publish child-appropriate verified readings from project sources. Preserve citations/provenance, adapt explanation to age without altering quotations or facts, and apply mandatory Arabic tashkīl to child-facing Arabic.

### Video & audio media

Continuously index/import qualified channels, videos and audio, classify them by age/subject/language, validate real playback paths, and extract transcripts/source material where lawful and useful.

## 9. Story origin classes

Every story must be explicitly classified internally as one of:

- `SOURCE_EXTRACTED_CHILD_STORY`
- `SOURCE_ADAPTED_CHILD_STORY`
- `SOURCE_TRANSLATED_CHILD_STORY`
- `SOURCE_TRANSCRIPT_ADAPTATION`
- `ORIGINAL_EDUCATIONAL_FICTION`
- `LEGACY_UNSOURCED_STORY`

Never relabel generated/original fiction as sourced history.

Legacy unsourced stories may remain but do not count as source-backed historical evidence.

## 10. Sacred/historical safety

For Seerah, Prophet Muhammad ﷺ, Prophets, Ahl al-Bayt, Companions, Followers, Followers of Followers and other historical/religious figures:

- use verified source-derived factual episodes only;
- never invent dialogue, events, chronology, miracles, relationships, quotations or historical details;
- AI may structure, simplify, translate and linguistically revise source-supported material;
- if evidence is insufficient, mark `NEEDS_SOURCE` and move to another queue/cell.

Original educational fiction is permitted only for general values, family, cooperation, curiosity, learning, responsibility, nature, language and similar non-historical themes allowed by the master instruction.

## 11. Age adaptation

Use the live age groups in `data/children/taxonomy.json` and apply the age-adaptive rules from the overriding master.

Age adaptation changes presentation, sentence length, vocabulary, pacing, visual complexity and interaction depth; it must never alter source truth.

Each story must carry explicit `contentType`, `ageGroup` and `subjectCategory` values matching a live taxonomy cell.

## 12. Arabic tashkīl requirement

All child-facing Arabic must satisfy the master instruction's mandatory vocalization rule.

Before publication:

`ARABIC TEXT -> LINGUISTIC REVIEW -> TASHKIL -> PROOFREAD -> DISPLAY/TTS CONSISTENCY -> TTS TEST -> PUBLISH`

Maintain:

- vocalized display/TTS Arabic;
- separate diacritic-stripped search-normalized Arabic.

Never publish insufficiently vocalized Arabic child content merely to satisfy story targets.

## 13. Localization

Every publishable child story/content record should support Arabic, English and French according to the master localization rules.

Do not mark a locale complete when substantial content remains untranslated.

For source quotations, preserve authentic wording and clearly distinguish translation from original text.

## 14. Uniqueness and duplication control

Before creating a story, compare:

- content type;
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

## 15. Media-to-story extraction

When a video/audio/book/article/verified reading contains usable child material:

1. register the source;
2. obtain lawful/usable transcript or text;
3. retain provenance;
4. classify factual vs educational/fictional material;
5. extract source-supported facts/episodes;
6. determine eligible story content types;
7. adapt independently for the appropriate story type and age group;
8. apply Arabic tashkīl;
9. localize;
10. proofread;
11. audit historical/source fidelity;
12. validate reader/player/animation metadata where relevant;
13. publish only after passing the children publication gate.

Do not treat a secondary children's cartoon invention as historical evidence merely because it mentions a historical figure.

## 16. Rotating batch behavior

Use small resumable batches rather than attempting the entire target in one run.

Recommended priorities per scheduled run:

- one acquisition/media queue;
- one lowest-count children content section;
- one or more lowest-count story-type × subject × age cells;
- deterministic checkpoint;
- strict validation;
- commit/publish only verified output.

If a source/network/API is unavailable, mark it retryable and continue with another queue. Ordinary acquisition misses must not create notification storms.

## 17. Publication states

Use explicit states:

`DISCOVERED`
`SOURCE_VERIFIED`
`TRANSCRIPT_READY`
`TEXT_READY`
`ADAPTATION_READY`
`TASHKIL_REQUIRED`
`PROOFREAD`
`ASSET_REQUIRED`
`AUDIO_REQUIRED`
`ANIMATION_REQUIRED`
`READY_TO_PUBLISH`
`PUBLISHED`
`NEEDS_SOURCE`
`NEEDS_RIGHTS_REVIEW`
`NEEDS_REVIEW`
`FAILED_RETRYABLE`

Do not call an item published unless it is at the publication stage defined by the overriding master.

## 18. Machine-readable state

Maintain a status ledger with at least:

- `verifiedChannelCount`
- `channelTarget = 100`
- `CHANNEL_TARGET_COMPLETE`
- `verifiedVideoCount`
- `videoTarget = 1000`
- `VIDEO_TARGET_COMPLETE`
- counts for audio/books/articles/transcripts/verified readings
- live children content types
- live story-bearing content types
- counts by children content type
- live subject categories
- live age groups
- `storyTargetPerCell = 5000`
- `storyCountsByContentTypeSubjectAgeCell`
- `underTargetStoryCells`
- `emptyStoryCells`
- `nextStoryTargetCell`
- `totalStoryManifestationCount`
- `calculatedStoryMatrixTarget`
- `STORY_TARGET_COMPLETE`
- `CHILDREN_MEDIA_STORY_COMPLETION_COMPLETE`

`CHILDREN_MEDIA_STORY_COMPLETION_COMPLETE=true` only when:

- at least 100 verified channels exist;
- at least 1,000 verified videos exist;
- every live story-bearing content type × subject × age-group cell has at least 5,000 qualifying stories;
- all current children content sections are represented and functional according to their type;
- all publication/integrity requirements remain satisfied.

Even after target completion, lightweight availability/provenance maintenance may continue without creating filler.

## 19. Absolute hierarchy

Targets are operational goals only.

The controlling order remains:

`AUTHENTICITY -> SOURCE FIDELITY -> PROVENANCE -> CHILD SAFETY/TASHKIL -> LOCALIZATION -> RIGHTS -> FUNCTIONALITY -> QUALITY -> NUMERICAL TARGETS`

Never reduce a higher-priority requirement to reach 100 channels, 1,000 videos or 5,000 stories per story-content-type × taxonomy cell.
