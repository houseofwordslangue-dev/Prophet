<!-- AUTHORITATIVE MASTER INSTRUCTION — assembled from the user's three supplied parts; chunk markers are transport boundaries only. -->

<!-- MASTER_CHUNK_01_BEGIN -->
[[MASTER_CHUNK_01]]
<!-- MASTER_CHUNK_01_END -->

<!-- ============================================================ -->
<!-- MASTER_CHUNK_02_BEGIN -->
[[MASTER_CHUNK_02]]
<!-- MASTER_CHUNK_02_END -->

<!-- ============================================================ -->
<!-- MASTER_CHUNK_03_BEGIN -->

==================================================
35. GOOGLE DRIVE / GITHUB / STORAGE
==================================================

Use connected repositories/storage according to their intended roles.

Possible roles:

GOOGLE DRIVE
- source files;
- scans;
- user-owned editions;
- archival editions;
- ingestion source.

GITHUB
- source code;
- structured metadata;
- small textual datasets;
- deployment configuration;
- tests;
- controlled content manifests.

Avoid storing unnecessarily large media files in GitHub when a better storage system exists.

Do not delete a source file until successful ingestion and integrity have been verified where deletion has been explicitly requested.


==================================================
36. FAILED / AMBIGUOUS ACQUISITION RECORDS
==================================================

Do not silently discard ambiguous matches.

Maintain:

- failed acquisition queue;
- ambiguous candidate queue;
- unavailable-resource queue;
- metadata-mismatch queue;
- unresolved edition queue.

Where appropriate retain candidate links/identifiers for later review.


==================================================
37. LANGUAGE AND LOCALIZATION
==================================================

The site is fully localized in:

- Arabic;
- English;
- French.

Each version must be genuinely localized.

ARABIC VERSION
- Arabic UI;
- Arabic headings;
- Arabic metadata labels;
- Arabic article content;
- avoid accidental Latin text except necessary technical terms, names without established Arabic forms, bibliographic identifiers or technical standards.

ENGLISH VERSION
- English UI/content.

FRENCH VERSION
- French UI/content.

Do not rely on mixed-language fallback as the normal public experience.


==================================================
38. LANGUAGE ROUTING
==================================================

Ensure:

- language selector visible and functional;
- mobile language selector functional;
- URLs retain relevant content/person/resource while switching language;
- `hreflang` is correctly generated;
- canonical URLs are coherent;
- translation does not create duplicate SEO conflicts.


==================================================
39. DESIGN SYSTEM
==================================================

Maintain a refined visual identity based on the project's established direction:

- green primary palette;
- Moroccan zellige/mosaic influence;
- restrained gold/cream accents where suitable;
- high-quality Arabic typography;
- responsive layout;
- excellent mobile usability;
- accessible contrast;
- polished research-oriented design.

Use the current approved dome imagery consistently where it is part of the design.

Remove obsolete imagery where superseded.

Do not allow decorative design to compromise readability.


==================================================
40. MOBILE FUNCTIONALITY
==================================================

Continuously test:

- menu;
- language selector;
- search;
- quote bar;
- reader;
- audio player;
- video player;
- story controls;
- filters;
- biography navigation;
- resource navigation.

No desktop-only functionality should be treated as complete if the mobile experience is broken.


==================================================
41. MEDIA CSP / SERVICE WORKER
==================================================

Ensure the site CSP and service worker allow required legitimate media origins.

Known classes of failures to prevent include:

- blocked YouTube thumbnails;
- blocked images;
- blocked media fetches;
- stale cached media;
- source selection not updating players;
- play buttons displaying temporary status without actual playback.

Do not weaken CSP indiscriminately.

Add only the origins/capabilities that the site legitimately requires.


==================================================
42. CHILDREN'S ANIMATED STORIES
==================================================

Animated stories should be implemented as genuine interactive/animated experiences rather than static placeholder pages.

Support as appropriate:

- scene-based storytelling;
- captions;
- voice/audio;
- animation;
- progress;
- previous/next;
- auto-play;
- pause;
- age filters;
- topic filters;
- source/provenance class;
- mobile support.

Respect editorial treatment of historical/religious figures.

Use visual alternatives such as:

- landscapes;
- architecture;
- calligraphy;
- symbolic objects;
- silhouettes where appropriate;

according to the site's visual policy.


==================================================
43. AUTOMATED CONTENT EXPANSION
==================================================

Continuously scan all site sections for underdeveloped content.

Automatically prepare new:

- source extractions;
- articles;
- biographies;
- stories;
- media records;
- OCR recoveries;
- resource records.

Distribution should prioritize:

- sections with little recent content;
- high-value missing biographies;
- uncovered important works;
- missing child content;
- unresolved OCR material;
- underrepresented languages.


==================================================
44. DAILY ARTICLE TARGET
==================================================

Maintain an operational objective that every active editorial section receives meaningful new or improved material regularly, including the previously requested goal of at least one meaningful article/update per active section per approximately 24 hours where sufficient verified material exists.

This is a TARGET, not a licence to publish weak or fabricated text.

If adequate source material is unavailable:

- continue acquisition;
- extraction;
- OCR recovery;
- transcription;
- source-grounded preparation;

instead of fabricating an article.


==================================================
45. AUTOMATION REPORTING
==================================================

Maintain administrative reporting for automated publication/ingestion where the implementation supports it.

Reports may include:

- new articles;
- updated biographies;
- OCR repairs;
- new resources;
- unresolved items;
- failed acquisitions;
- source counts;
- publication counts;
- quality failures.

Existing designated administrator contact may continue to be used where already configured.


==================================================
46. SOURCE INGESTION
==================================================

Continuously derive genuine material from:

- books;
- native text;
- EPUB;
- PDFs;
- manuscripts;
- research;
- lectures;
- podcasts;
- audio;
- video;
- transcripts;
- archival collections.

OCR and transcription are legitimate acquisition methods.

AI may linguistically revise the output but must preserve historical substance.


==================================================
47. SEARCH AND INDEXING
==================================================

Maintain a unified search index covering as appropriate:

- articles;
- biographies;
- books;
- passages;
- OCR text;
- transcripts;
- media;
- names;
- aliases;
- subjects;
- sources.

Reindex automatically after publication or major correction.

Search should respect canonical routing so duplicate biography pages do not appear as separate people.


==================================================
48. DUPLICATE DETECTION
==================================================

Continuously detect:

- duplicate people;
- duplicate biographies;
- duplicate resources;
- duplicate articles;
- duplicate OCR fragments;
- duplicate media manifestations.

Duplicates should be merged when they represent the same canonical object.

Do not merge genuinely distinct editions, articles or historical persons merely because names/titles are similar.


==================================================
49. SOURCE DEDUPLICATION
==================================================

Different editions of the same work should share a canonical work identity while retaining edition-specific metadata.

Example:

WORK
→ edition A
→ edition B
→ EPUB
→ scan
→ audio
→ video
→ transcript

Do not flatten these manifestations into one ambiguous record.


==================================================
50. SCHOLARLY SOURCE DISPLAY
==================================================

Normal pages should display clean scholarly citations.

Detailed technical metadata should remain available through:

- source details;
- research view;
- administrative audit;
- provenance interface.

Avoid cluttering general reading pages with internal pipeline diagnostics.


==================================================
51. PUBLIC RESOURCE BROWSING
==================================================

Users should be able, where supported, to:

- browse;
- read;
- listen;
- watch;
- search;
- compare editions;
- navigate references.

Important works should show all available legitimate manifestations in one coherent record.
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
