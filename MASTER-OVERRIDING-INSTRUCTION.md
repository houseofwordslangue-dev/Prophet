<!-- AUTHORITATIVE MASTER INSTRUCTION — assembled from the user's three supplied parts; chunk markers are transport boundaries only. -->

<!-- MASTER_CHUNK_01_BEGIN -->
[[MASTER_CHUNK_01]]
<!-- MASTER_CHUNK_01_END -->

<!-- ============================================================ -->
<!-- MASTER_CHUNK_02_BEGIN -->

==================================================
18. ARTICLE METADATA
==================================================

Retain internally, as applicable:

- article title;
- author;
- editorial author;
- extracted-from title;
- source author;
- publisher;
- edition;
- volume;
- page range;
- transcription source;
- timestamp/timecode;
- source IDs;
- language;
- provenance type;
- verification status.

Where several sources are synthesized under site editorial authorship, use the site's agreed editorial attribution such as:

هيئة تحرير الموقع

where appropriate.


==================================================
19. MASTER OCR RESTORATION POLICY
==================================================

Continuously scan:

- website content;
- biography passages;
- articles;
- book extractions;
- transcripts;
- archival material;

for material previously rejected, downgraded, quarantined or corrupted because of:

- collapsed Arabic OCR;
- corrupt Arabic;
- missing spaces;
- merged words;
- broken letters;
- reversed text;
- displaced lines;
- mixed columns;
- page-layout contamination;
- headers/footers inside paragraphs;
- duplicated OCR;
- incorrect line ordering;
- malformed Unicode;
- scan artifacts;
- encoding corruption;
- incomplete segmentation.

DO NOT permanently discard potentially recoverable material.


==================================================
20. OCR SOURCE PRIORITY
==================================================

Use this recovery priority:

1. Exact original scan/page.
2. Another edition/copy of the same work in Google Drive.
3. Another edition/copy in GitHub.
4. EPUB/native-text version.
5. Other verified copies in the site library.
6. Corresponding passages in authoritative listed resources.
7. Other legally usable/public/open copies when needed.

Prefer comparison of several witnesses whenever possible.


==================================================
21. PERMITTED OCR REPAIR
==================================================

AI may:

- restore spaces;
- repair obvious OCR substitutions;
- restore strongly supported missing letters;
- reconstruct broken words;
- remove duplicated OCR noise;
- normalize Unicode;
- restore sentence/paragraph boundaries;
- restore punctuation;
- reorder lines when page layout clearly proves the order;
- remove page numbers/headers/footers accidentally inserted;
- join page-crossing fragments;
- correct obvious typographical OCR errors;
- perform necessary linguistic proofreading.

AI must NOT:

- invent historical information;
- rewrite an author's substantive wording;
- paraphrase genuine quotations merely for elegance;
- silently merge contradictory readings;
- manufacture text where witnesses do not support reconstruction.


==================================================
22. OCR CROSS-VERIFICATION
==================================================

For every repaired passage:

- identify person/work/article;
- retain original corrupted extraction;
- identify page/source;
- locate corroborating witnesses;
- compare variants;
- choose best-supported reading;
- retain consulted sources;
- retain original OCR separately;
- retain corrected OCR;
- calculate verification/confidence status.

Historical spelling should be preserved when meaningful.


==================================================
23. OCR PUBLICATION RULE
==================================================

Preferred workflow:

VERIFIED REPAIR
→ AUTOMATIC PUBLICATION

UNRESOLVED
→ REVIEW QUEUE

NEVER:

UNRESOLVED
→ INVENTED RECONSTRUCTION.

Do not allow one uncertain word to block an otherwise safely separable verified passage.

Publish verified portions where this can be done without distorting meaning.


==================================================
24. OCR QUALITY GATE
==================================================

Before publication verify:

- Arabic readability;
- correct spacing;
- removal of scan noise;
- coherent paragraph order;
- no accidental Latin OCR on Arabic public pages;
- source attribution;
- person ownership;
- duplicate detection;
- canonical placement;
- agreement with corroborating sources;
- preservation of genuine quotation wording;
- no invented history.


==================================================
25. OCR INTERNAL METADATA
==================================================

Retain:

- source title;
- author;
- edition;
- volume;
- page/page range;
- resource/file ID;
- Drive/GitHub provenance;
- original OCR;
- corrected text;
- corroborating witnesses;
- correction method;
- verification status;
- confidence;
- revision date.

Do not clutter normal public reading pages with technical OCR diagnostics.

Expose detailed provenance through research/admin interfaces.


==================================================
26. CONTINUOUS OCR REPROCESSING
==================================================

Re-run OCR validation whenever:

- new OCR arrives;
- OCR fails quality gates;
- corrupted existing text is discovered;
- better editions are added;
- previously unresolved material gains new evidence.

Previously rejected material must not remain permanently forgotten.


==================================================
27. AUTO-PUBLISH AFTER VERIFICATION
==================================================

Once validated:

- update canonical biography/article;
- update indexes;
- update search;
- update source counts;
- invalidate caches;
- regenerate affected static/data assets;
- run integrity checks;
- verify correct placement;
- verify no duplicates.

No manual approval is required for passages that fully satisfy the automated validation gates.


==================================================
28. RESOURCE LIBRARY
==================================================

المصادر والدراسات is the canonical resource and research library.

It should contain and organize:

- books;
- editions;
- scans;
- EPUBs;
- native text;
- research;
- articles;
- manuscripts where available;
- lectures;
- audio;
- video;
- transcripts;
- translations;
- archival materials.

Resource records remain resource objects even when they are cited from biographies or articles.

Do not duplicate a full resource merely because several sections use it.


==================================================
29. RESOURCE TARGETS
==================================================

Continue expanding toward broad resource collections including requested targets such as:

- 100 Qur'an interpretation resources;
- 100 Hadith resources;
- 100 Seerah resources;
- 100 Shamāʾil resources;
- 100 Ahl al-Bayt resources;
- 100 teaching/ethics resources;
- 600+ total resources;
- unresolved works not covered by OpenITI;
- additional editions and media manifestations.

These numbers are acquisition goals.

Do not create fake resource records to reach them.


==================================================
30. IMPORTANT WORKS
==================================================

Ensure important requested works, including:

الشفا بتعريف حقوق المصطفى

and other major listed works are properly represented where legitimately available as:

- readable text/book;
- searchable content;
- audio;
- video;
- related editions;
- source metadata.

Do not create fake Read / Listen / Watch buttons.

Every button must correspond to a functioning capability or be hidden/disabled.


==================================================
31. READER / PLAYER SYSTEM
==================================================

The site must provide an advanced internal reader/player experience inspired functionally by high-quality digital libraries.

Capabilities should include as applicable:

READ
- page navigation;
- thumbnails;
- zoom;
- fit modes;
- full screen;
- selectable text where possible;
- OCR layer;
- search within book;
- bookmarks where supported.

LISTEN
- actual audio playback;
- playlist/source selection;
- playback rate;
- seek;
- resume;
- language/edition selection where applicable.

WATCH
- actual video playback;
- source switching;
- captions/transcripts where available;
- seek;
- full screen.

SEARCH
- within resource;
- global catalogue search;
- person/title/subject filters.

Never display a capability that does not actually work.


==================================================
32. MULTI-SOURCE DELIVERY
==================================================

Where legitimate and technically feasible, maintain multiple source/origin options for important resources.

The goal is:

- resilience;
- faster worldwide access;
- fallback availability;
- reduced dependence on one server.

A target of several viable origins/copies may be maintained where available.

Do not fabricate mirrors.

Do not duplicate content illegally merely to satisfy a mirror count.

The site's own player/reader should be the primary user experience wherever technically possible.


==================================================
33. EXTERNAL SOURCES VS INTERNAL EXPERIENCE
==================================================

"No external links" should be interpreted as:

DO NOT unnecessarily force the user out of the website.

It does NOT prohibit:

- external media origins;
- lawful APIs;
- archive servers;
- remote storage;
- backend mirrors;
- embedded delivery;

when they support the internal site reader/player.

External-source provenance may remain available through research metadata.


==================================================
34. LICENSING / HOSTING GOVERNANCE
==================================================

Public internet availability does not automatically mean unrestricted redistribution.

Separate:

A. DISCOVERY / INDEXING / REFERENCE

A relevant source may be catalogued and referenced when appropriate.

B. LOCAL HOSTING / COPYING / REDISTRIBUTION

Only locally host or redistribute where the project is legally entitled to do so.

Examples may include:

- public domain;
- open licence;
- permissive licence;
- user-owned copy;
- licensed use;
- otherwise authorized hosting.

Do not bypass access restrictions or falsely classify material as unrestricted.

Preserve actual licence metadata where known.

OpenITI and similar corpora must retain the applicable licence obligations.
<!-- MASTER_CHUNK_02_END -->

<!-- ============================================================ -->
<!-- MASTER_CHUNK_03_BEGIN -->
[[MASTER_CHUNK_03]]
<!-- MASTER_CHUNK_03_END -->

<!-- ============================================================ -->
<!-- MASTER_CHUNK_04_BEGIN -->
[[MASTER_CHUNK_04]]
<!-- MASTER_CHUNK_04_END -->

<!-- ============================================================ -->
<!-- MASTER_CHUNK_05_BEGIN -->
[[MASTER_CHUNK_05]]
<!-- MASTER_CHUNK_05_END -->

<!-- ============================================================ -->
<!-- MASTER_CHUNK_06_BEGIN -->
[[MASTER_CHUNK_06]]
<!-- MASTER_CHUNK_06_END -->
