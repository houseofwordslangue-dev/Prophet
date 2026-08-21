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

## Exclusive semantic extraction rules for the five core Muhammad ﷺ sections

Classification MUST be based on the **dominant/main idea, object, and research purpose of the passage/article**, not on incidental keyword occurrence.

A passage may mention words belonging to several sections. That does **not** make it eligible for all of them. Assign the passage/article to the one section whose subject is the principal object of discussion. Cross-link elsewhere if useful, but do not duplicate the full content merely because related terms occur.

### 1. النور — The Light
Extract and publish here **exclusively** content whose dominant/main idea or object is:
- **الحقيقة المحمدية**
- **النور المحمدي**

Do not classify ordinary biography, prophecy, mission, mercy, daily life, battles, family events, or companion stories here merely because the Prophet ﷺ is mentioned or because the word نور appears incidentally.

### 2. النبي — The Prophet
Extract and publish here **exclusively** content whose dominant/main idea or object is:
- **النبي**
- **النبوة**

The passage must principally discuss Muhammad ﷺ specifically in his capacity as Prophet, or the meaning, characteristics, signs, dimensions, functions, or reality of prophethood. Do not place material here when the main subject is الرسالة, daily personal life, mercy, family, companions, or historical biography.

### 3. الرسول — The Messenger
Extract and publish here **exclusively** content whose dominant/main idea or object is:
- **الرسول**
- **الرسالة**

The passage must principally concern Muhammad ﷺ in his capacity as Messenger, the delivery/content/function of the message,بلاغ, communication of revelation, mission, invitation, or responsibilities of الرسالة. Do not classify content here merely because رسول الله is used as an honorific inside a passage whose real subject belongs elsewhere.

### 4. الإنسان — The Human Being
Extract and publish here **exclusively** content whose dominant/main idea or object is the lived, personal, human experience of Muhammad ﷺ, especially:
- **الحياة اليومية لمحمد صلى الله عليه وسلم**
- **المشاكل الزوجية لمحمد صلى الله عليه وسلم**
- **قصص محمد صلى الله عليه وسلم مع الصحابة**
- **معاناة محمد صلى الله عليه وسلم في تبليغ الدعوة** when the emphasis is his personal/human experience of hardship rather than the doctrine/function of الرسالة
- **القصص الشخصية لمحمد صلى الله عليه وسلم**

This section is for the human, personal, domestic, relational, emotional, practical, social, and lived dimensions of his life. Do not place abstract discussions of الحقيقة المحمدية, النبوة, الرسالة, or الرحمة here unless the principal object is a concrete personal-life episode.

### 5. الرحمة العظمى — The Great Mercy
Extract and publish here **exclusively** content whose dominant/main idea or object is:
- **رحمة محمد صلى الله عليه وسلم**
- **الرحمة** as embodied, taught, demonstrated, or communicated through Muhammad ﷺ
- **الرحمة العظمى**

The passage must principally analyze, narrate, demonstrate, or explain mercy. Do not classify an event here merely because it contains a kind act if the real subject is biography, war, family, prophethood, الرسالة, or another primary topic.

## Exclusive-classification decision test
Before assigning any content to one of these five sections, answer in order:
1. What is the passage/article principally **about**?
2. If its title were rewritten as one precise research question, what would that question be?
3. Which one of the five section definitions answers that question most directly?
4. Would the passage still belong to that section if incidental keywords from the other four were removed? If NO, reject that classification.
5. If no one section clearly dominates, do not force it into these five sections. Route it to the appropriate family, companions, biography, research, media, or other section.

**One article/passage = one primary section.** Cross-references may point to related sections, but primary placement must remain exclusive.

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
