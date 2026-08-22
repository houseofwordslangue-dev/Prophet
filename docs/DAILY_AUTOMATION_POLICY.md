# Single Daily Automation Policy

GOVERNED_BY: MASTER_OVERRIDING_INSTRUCTION.md

The repository intentionally has one automatic GitHub Actions workflow only: `.github/workflows/daily-generative-control.yml`.

It runs once per UTC day and consolidates source recovery, ingestion, content completion, biography completion, children completion accounting, provenance checks, gap auditing, publication-state updates, optional live deployment, and one daily report.

All former specialized workflows are retired as independent Actions. Their scripts remain reusable by the daily controller or manual local/Colab execution where relevant.

Recoverable source/network/content deficits are recorded in ledgers and do not create separate failed-action notifications. Hard authenticity, security, corruption, or publication-integrity defects remain visible in the consolidated daily report.
