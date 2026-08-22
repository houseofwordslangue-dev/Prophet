# Project Process Governance

## Sole governing authority

`MASTER-OVERRIDING-SITE-INSTRUCTION.md` is the controlling project instruction for every existing and future process in this repository and connected project infrastructure.

Every new process MUST:

1. Read and apply `MASTER-OVERRIDING-SITE-INSTRUCTION.md` before executing substantive project work.
2. Treat that file as higher priority than any workflow-specific prompt, script comment, policy file, template, importer, generator, renderer, manifest, cached report, or automation configuration.
3. Preserve compatible specialized policies, but never allow them to weaken or override the master instruction.
4. Resolve conflicts using the priority order defined by the master instruction.
5. Preserve historical/source truth, provenance, canonical ownership, legal/security requirements, public-page purity, and functioning UI requirements defined there.
6. Re-check the current master instruction whenever a process is created, materially modified, or resumed after an interruption.

## Required declaration for new process files

Every newly created process file under `.github/workflows/`, `scripts/`, or other executable automation/process directories must contain this exact declaration in a comment or documentation string:

`GOVERNED_BY: MASTER-OVERRIDING-SITE-INSTRUCTION.md`

This declaration is an acknowledgement, not a substitute for reading and complying with the master instruction.

## Subordinate policies

Files such as `EDITORIAL-GENUINE-SOURCE-POLICY.md`, `CONTENT_SOURCE_POLICY.md`, `MASTER-FIVE-SECTIONS-EXTRACTION-PROMPT.md`, `MASTER-PUBLIC-PAGE-CONTENT-PURITY-RULE.md`, data policies, and workflow-local instructions are subordinate implementation policies. They apply only where compatible with `MASTER-OVERRIDING-SITE-INSTRUCTION.md`.

## New-process rule

No new ingestion, OCR, extraction, transcription, article, biography, story, media, resource, localization, publication, search/indexing, player/reader, security, restoration, audit, or deployment process is considered project-compliant unless it abides by the controlling master instruction.
