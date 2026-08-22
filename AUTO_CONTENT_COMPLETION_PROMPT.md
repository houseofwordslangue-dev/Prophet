# AUTO CONTENT COMPLETION PROMPT

GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md

This is a standing automation instruction for the Prophet Muhammad biography website. It is subordinate to `MASTER-OVERRIDING-SITE-INSTRUCTION.md`; when any rule conflicts, the overriding master instruction wins.

## Objective

Continuously repair, extract, source-ground, revise, proofread, audit and publish content for every currently active editorial section that is empty or short, and complete canonical biographies for every biography-required person who currently has no usable biography.

## Article completion target

1. Read the live section registry in `data/editorial_sections.json` on every cycle.
2. Treat every active `editorial=true` section/subsection slot as an independent completion target.
3. Count only unique articles that are actually represented as public/ready/published source-grounded content. Do not inflate counts with duplicates, audit copies, aliases, manifests, placeholders, empty shells or repeated IDs.
4. For every slot with fewer than 50 qualifying articles, continue source recovery and article production.
5. Prioritize in this order:
   - empty slots;
   - slots with the lowest article count;
   - short/thin articles that can be enriched from verified sources;
   - remaining under-50 slots.
6. Prefer extraction from verified source text. AI may organize, summarize, translate, synthesize and linguistically revise verified source material, but may never invent historical/religious facts, quotations, events, relationships, dates or evidence.
7. Every newly produced source-derived article must retain source provenance and pass the existing publication integrity gate before publication.
8. Never manufacture filler simply to reach 50.
9. If no suitable source exists for a slot, record `NEEDS_SOURCE`, continue with another eligible slot when possible, and retry after additional source ingestion.
10. Once every active editorial slot has at least 50 qualifying articles, set `ARTICLE_FILL_COMPLETE=true` and STOP creating additional articles under this completion prompt. Existing normal editorial rotation may continue only if separately instructed.

## Empty/short content repair

For existing pages and articles:

- detect empty bodies, placeholder bodies, broken OCR, fragments, insufficiently sourced summaries and obviously short content;
- search repository/Drive/local ingested resources first;
- recover native text before OCR where possible;
- repair and proofread source-supported material;
- merge/enrich rather than duplicate;
- preserve the stronger verified version;
- publish verified repairs automatically;
- quarantine unresolved text rather than inventing completion.

## Biography completion target

1. Rebuild the live biography-required registry on every cycle from the current people/family/ancestor/companion/follower indexes and canonical biography data.
2. Detect every biography-required person with no current usable canonical biography.
3. Do not use a fixed hard-coded target list. The target list must be generated dynamically from the live missing-biography audit.
4. For each missing person, search existing repository content, ingested books, verified extracts, source passages, transcripts and other project resources for person-specific evidence.
5. Verify identity/ownership before attaching source text to that person. Name-only incidental mentions are insufficient.
6. Produce a canonical biography or canonical biography extension only from verified person-specific evidence.
7. AI may structure and linguistically revise the evidence, but must not invent missing life details.
8. Preserve source citations/provenance and conflicting source traditions where relevant.
9. If evidence remains insufficient, retain `SOURCE_REQUIRED` / `NEEDS_SOURCE` and retry later; never fabricate a biography.
10. Continue biography completion until `missingCanonicalBiographyCount = 0`.

## Publication and quality gate

Before publication, require the rules of `MASTER-OVERRIDING-SITE-INSTRUCTION.md`, including authenticity, provenance, verified OCR repair, canonical person placement, localization, rights, no-degradation and functional publication status.

Numerical targets are operational goals only. They never override source truth.

## Automation state

Maintain a machine-readable state containing at least:

- activeEditorialSlotCount
- targetArticlesPerSlot = 50
- articleCountsBySlot
- underTargetSlots
- emptySlots
- nextTargetSlot
- ARTICLE_FILL_COMPLETE
- biographyRequiredPersonCount
- missingCanonicalBiographyCount
- missingBiographyIds
- BIOGRAPHY_FILL_COMPLETE
- COMPLETION_PROMPT_COMPLETE

`COMPLETION_PROMPT_COMPLETE=true` only when:

- every active editorial slot has at least 50 qualifying articles; AND
- every biography-required person has a usable source-backed canonical biography.

When complete, future scheduled executions must exit successfully without creating filler or additional completion-target content.
