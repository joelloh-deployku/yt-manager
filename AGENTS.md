# AGENTS.md

## Mission
Build and maintain a reliable AI-assisted YouTube content operations system. Hermes operates the daily content workflow on the home server. Codex owns engineering, testing, debugging, and maintainability.

## Milestone 1 scope
Milestone 1 is deliberately narrow:
- SQLite runtime state
- YouTube Data API ingestion for configured competitor channels
- deterministic outlier scoring
- one Markdown daily research report
- Hermes workflow instructions for running the pipeline

Do not implement scripting, thumbnail generation, publishing, X/Twitter research, dashboards, or the weekly audit until Milestone 1 is reliable.

## Engineering rules
1. Inspect existing code and docs before changing them.
2. Prefer deterministic Python for API calls, scoring, persistence, validation, and reporting.
3. Use LLM/agent reasoning only where judgment is genuinely required.
4. Never commit secrets, API keys, credentials, database files, logs, or generated reports.
5. Add or update tests for meaningful behavior changes.
6. Fail loudly with actionable errors; do not silently swallow API/database failures.
7. Keep external API boundaries small and mockable.
8. Keep runtime state in SQLite, not Git.
9. Keep source URLs and raw metrics with every research candidate for auditability.
10. Do not publish content or mutate external creator accounts without explicit human approval.

## Verification
Before considering a change complete:
- run `python -m pytest`
- run the relevant script locally where credentials are not required, or use mocked tests
- update documentation when configuration or behavior changes

## Architecture ownership
Hermes: operations, scheduled execution, later research/content subagents.
Codex: codebase, tests, integrations, migrations, debugging, deployment improvements.
