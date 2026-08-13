# AGENTS.md

## Mission
Build and maintain a reliable AI-assisted YouTube content operations system. Hermes operates the daily content workflow on the home server. Codex owns engineering, testing, debugging, and maintainability.

## Milestone 1 foundation
Milestone 1 established:
- SQLite runtime state
- YouTube Data API ingestion for configured competitor channels
- configurable 14-day candidate research
- historical channel baselines and deterministic outlier scoring
- repeated view snapshots
- one Markdown daily research report

## Milestone 2 scope
Milestone 2 adds the Hermes Strategist above the research foundation:
- a versioned channel profile
- deterministic strategist-input JSON built from the latest completed research run
- one focused Hermes Strategist subagent for judgment-heavy prioritization
- a strict JSON output contract with source video IDs
- deterministic validation, Markdown rendering, and SQLite persistence

Do not add full script writing, thumbnail generation, publishing, X/Twitter research, dashboards, scheduling, or the weekly audit in Milestone 2.

## Agent boundary
1. Deterministic Python owns API calls, raw metrics, scoring, snapshot/velocity calculations, validation, persistence, and report rendering.
2. Hermes owns operational execution and strategy judgment.
3. The Strategist must reason from supplied evidence; it must not invent metrics, URLs, source videos, or research findings.
4. Strategy recommendations must remain auditable to source video IDs from the current research run.
5. Relevance and measured performance are separate concepts. A performance tier is evidence, not the final decision.

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
- run the relevant deterministic preparation/validation scripts
- perform a real Hermes strategy run manually before scheduling it
- update documentation when configuration or behavior changes

## Architecture ownership
Hermes: operations, strategist execution, and later research/content subagents.
Codex: codebase, tests, integrations, migrations, debugging, deployment improvements.
