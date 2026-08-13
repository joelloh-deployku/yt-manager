# AGENTS.md

## Mission
Build and maintain a reliable AI-assisted YouTube content operations system. Hermes operates the content workflow on the home server. Codex owns engineering, testing, debugging, and maintainability.

## Milestone 1 foundation
Milestone 1 established:
- SQLite runtime state
- YouTube Data API ingestion for configured competitor channels
- configurable 14-day candidate research
- historical channel baselines and deterministic outlier scoring
- repeated view snapshots and velocity
- one Markdown daily research report

## Milestone 2 foundation
Milestone 2 established:
- a versioned channel profile
- deterministic strategist-input JSON
- one focused Hermes Strategist subagent
- a strict source-backed JSON output contract
- deterministic validation, Markdown rendering, and SQLite strategy persistence

## Milestone 3 scope
Milestone 3 adds script writing behind an explicit human approval gate:
- SQLite approval records tied to one validated strategy opportunity
- `approve_strategy.py` as the explicit human approval action
- deterministic script-input JSON containing exactly one approved opportunity
- one focused Hermes Script Writer subagent
- a strict script JSON contract with title options, brief, full script, source IDs, verification notes, and creator placeholders
- deterministic word counting, evidence validation, Markdown rendering, and SQLite script persistence

Do not add thumbnail generation, publishing, X/Twitter research, dashboards, automated scheduling, video editing, or the weekly audit in Milestone 3.

## Human approval boundary
1. Hermes must not approve a strategist opportunity on Joel's behalf.
2. Script writing requires a row in `script_approvals` created by an explicit human action.
3. `python scripts/approve_strategy.py --rank <N>` is the canonical approval action.
4. Hermes may run that command only when Joel explicitly instructs Hermes to approve that exact rank in the current conversation.
5. A generated script remains a draft for Joel's review; it is not publishing approval.

## Agent boundary
1. Deterministic Python owns API calls, raw metrics, scoring, snapshot/velocity calculations, approval records, context construction, validation, persistence, word counting, and report rendering.
2. Hermes owns operational execution and delegates judgment/creative work to focused subagents.
3. The Strategist reasons from supplied research evidence and must not invent metrics or sources.
4. The Script Writer develops only the approved opportunity and must not silently switch topics.
5. Competitor titles/performance are inspiration evidence, not transcripts or factual sources for script claims.
6. Missing Joel-specific results or opinions must use `[JOEL: ...]` placeholders rather than fabricated first-person claims.
7. Unsupported current or technical facts must be surfaced in `verification_notes` rather than asserted as settled fact.

## Engineering rules
1. Inspect existing code and docs before changing them.
2. Prefer deterministic Python for API calls, scoring, persistence, validation, approval gates, and reporting.
3. Use LLM/agent reasoning only where judgment or creative synthesis is genuinely required.
4. Never commit secrets, API keys, credentials, database files, logs, or generated reports.
5. Add or update tests for meaningful behavior changes.
6. Fail loudly with actionable errors; do not silently swallow API/database failures.
7. Keep external API boundaries small and mockable.
8. Keep runtime state in SQLite, not Git.
9. Keep source URLs and raw metrics with research candidates for auditability.
10. Do not publish content or mutate external creator accounts without explicit human approval.

## Verification
Before considering a change complete:
- run `python -m pytest`
- run the relevant deterministic preparation/validation scripts
- verify script preparation fails without human approval
- perform one real Hermes Script Writer delegation after a human-approved opportunity
- confirm finalization rejects hallucinated source IDs and undersized scripts
- update documentation when configuration or behavior changes

## Architecture ownership
Hermes: operations plus focused Strategist/Script Writer delegation.
Codex: codebase, tests, integrations, migrations, debugging, deployment improvements.
