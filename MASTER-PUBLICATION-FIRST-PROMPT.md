# MASTER PROMPT — Publication First / Remove Artificial Obstructions

Apply this policy across the Prophet Muhammad biography site.

## Objective
Publish genuine, source-derived content as soon as it is usable. Do not withhold or hide otherwise publishable material because it mentions additional people, contains cross-references, spans more than one relationship, comes from a mixed source batch, or is not yet perfectly segmented.

## Core rule
**Publication takes priority over artificial isolation rules.**

If a chapter, article, biography passage, source extract, transcript, OCR result, note, or research record is assigned to a canonical person/section and contains meaningful source-derived content relevant to that person/section, publish it there even when other names or related people appear in the same text.

Mentioning another person is contextual information, not contamination.

Examples:
- A chapter about Khadija bint Khuwaylid may mention the Prophet Muhammad ﷺ, other wives, children, relatives, companions, merchants, narrators, or contemporaries. This does **not** justify hiding the chapter.
- A biography may discuss family relationships, events involving several participants, transmission chains, battles, journeys, marriages, disputes, chronology, or later consequences. Keep and publish the relevant narrative.
- A source batch may cover several people. If a resulting chapter has been assigned to a canonical person and contains material relevant to that person, display it. Improve segmentation later without blocking publication now.

## Primary-home architecture
Every content object has one primary public home based on the site's taxonomy. Cross-references are allowed and encouraged.

For people already assigned to a named section, publish their biography in that section rather than duplicating it in السير والتراجم.

Examples:
- الأسرة النبوية → الزوجات / أمهات المؤمنين → خديجة بنت خويلد
- الأسرة النبوية → الأبناء → [person]
- الأسرة النبوية → الأحفاد → [person]
- الصحابة → [person]
- التابعون → [person]
- تابعو التابعين → [person]
- السير والتراجم → الرواة + people not already assigned to another named primary section

A shared rendering component may be reused technically, but the visible breadcrumb, canonical route, menu ownership, backlinks, structured data, and SEO identity must reflect the person's correct primary section.

## Do NOT block publication merely because
- another person's name occurs in the text;
- several people are discussed in the same historical event;
- the chapter came from a multi-person batch;
- the text includes contextual genealogy or relationship material;
- a source contains OCR imperfections that do not prevent meaningful reading;
- perfect semantic segmentation has not yet been completed;
- the biography is shorter than the long-term target;
- translations are not yet equally complete in all three languages;
- a richer version may be produced later.

Publish the best currently usable version and continue improving it non-destructively.

## What may still block publication
Only hard failures may block the affected object/function, such as:
1. empty or meaningless content;
2. fabricated historical facts, quotations, events, dialogue, or attributions;
3. content with no identifiable provenance where provenance is required;
4. technically broken media controls falsely claiming read/listen/watch functionality;
5. malicious/insecure executable content;
6. an object that cannot be connected to any legitimate site subject at all.

When only part of an object has a problem, publish the usable part and flag/repair the defective part. Do not suppress the whole page unnecessarily.

## Biography rule
For a canonical biography page:
- aggregate all currently available source-derived material relevant to that person;
- preserve contextual mentions of other people;
- preserve chronology, family relations, events, stories, battles, sayings, narrations, scholarship, disagreements, and source notes where available;
- do not delete existing valid content when a shorter overlay or newer summary is loaded;
- merge richer material non-destructively;
- expose references clearly;
- continue expanding toward the professional target without using the target as a publication gate.

The long-term professional target remains ≥5,000 genuine source-derived words where sufficient source material exists, but **being below 5,000 words is not itself a reason to hide the biography**.

## Articles
Publish genuine source-derived articles even if they mention multiple people or overlap with another subject. Assign one primary section/person based on dominant relevance and add cross-links to the other relevant pages.

Do not duplicate the full article merely to satisfy multiple sections.

## OCR / transcripts
Use OCR/transcription material when meaningfully readable. Correct obvious OCR errors linguistically while preserving the source meaning. Do not invent missing historical content. Imperfect OCR should trigger review/improvement, not automatic suppression of usable text.

## Localization
Do not hide the Arabic original merely because English/French is incomplete. Publish available localized versions independently and mark missing translations for follow-up. Do not mix interface languages inside one locale except legitimate bibliographic/technical terms.

## Source disagreements
Disagreement among sources is not a publication blocker. Present the differing reports with attribution and uncertainty instead of suppressing the subject.

## Publication state
Use a publication-first state model:
- `published-current`: usable now, may still be expanded/polished;
- `published-with-review-note`: usable but contains a known non-fatal issue;
- `blocked-hard-failure`: only for the hard failures listed above.

Avoid states such as `quarantined`, `hidden`, `pending-perfect-segmentation`, or `blocked-because-other-names-appear` for otherwise usable content.

## Acceptance test
For every person/article/resource:
1. Is there meaningful genuine/source-derived content? If YES → publish.
2. Does it mention other people? Ignore that as a blocker.
3. Is it assigned to the correct primary section/person? If NO → route it correctly, then publish.
4. Is some part imperfect but still usable? Publish usable content and keep repair metadata internally.
5. Is there a hard factual/provenance/security/functionality failure? Block only the affected defective part until repaired.

## Explicit Khadija rule
All five existing chapters currently assigned to `khadija-bint-khuwaylid` must be visible under:

**الأسرة النبوية → الزوجات / أمهات المؤمنين → خديجة بنت خويلد**

Do not hide them merely because they mention Sawda, Aisha, Hafsa, Zaynab, Juwayriya, Umm Habiba, Safiyya, Maymuna, Mariya, Ibrahim, or other related persons. Their presence is contextual and does not prevent publication.

Continue improving Khadija's biography by extracting and integrating additional genuine material from the listed resources, but never replace richer valid content with a shorter summary and never make future perfection a precondition for present publication.
