# Resource lifecycle

This directory is the control plane for all old and new resources.

Lifecycle order:

1. `incoming/` — catalogued/source-pending resources not yet acquired.
2. `processing/import/` — download, mirror and import jobs in progress.
3. `processing/conversion/` — PDF→EPUB, OCR, text extraction and format conversion in progress.
4. `processing/revision/` — metadata/content/edition validation or revision in progress.
5. `ready/` — validated source/EPUB/PDF ready to be promoted.
6. `published/` — control metadata for resources already published. The actual public binary remains at `library/works/<workId>/editions/<editionId>/original.<format>`.
7. `failed/` — failed/invalid items retained for retry; never exposed as publication links.

## External source archive

The first-party source archive remains organized as:

- `Prophet Muhammad Resources — Archive.org/PDF/`
- `Prophet Muhammad Resources — Archive.org/EPUB/`

Do not flatten these folders. File type and lifecycle are separate concerns.

## Running jobs

No destructive move is performed while import, conversion, OCR, revision, acquisition or publication work is active. The lifecycle registry in `data/ingested_library.json` assigns every tracked resource one logical folder while existing workflows keep their current file paths until promotion is complete.

Only validated local assets can enter `published/*` and receive a reader URL.
