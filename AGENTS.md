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

## Milestone 3 foundation
Milestone 3 established script writing behind an explicit human approval gate:
- SQLite approval records tied to one validated strategy opportunity
- `approve_strategy.py` as the explicit human approval action
- deterministic script-input JSON containing exactly one approved opportunity
- one focused Hermes Script Writer subagent
- a strict script JSON contract with title options, brief, full script, source IDs, verification notes, and creator placeholders
- deterministic word counting, evidence validation, Markdown rendering, and SQLite script persistence

## Milestone 4 scope
Milestone 4 adds thumbnail direction after a validated Script Writer report:
- deterministic thumbnail-input JSON built from the validated script, approved strategy, channel profile, and permitted source IDs
- one focused Hermes Thumbnail Director subagent
- exactly three distinct packaging concepts and one recommended rank
- thumbnail-text word limits, creator-asset requirements, and render-ready visual direction
- deterministic source validation, originality checks, Markdown rendering, and SQLite thumbnail persistence

Milestone 4 does **not** generate thumbnail images. It also excludes image editing, thumbnail upload, publishing, scheduling, video editing, X/Twitter research, dashboards, and the weekly audit.

## Human approval boundary
1. Hermes must not approve a strategist opportunity on Joel's behalf.
2. Script writing requires a row in `script_approvals` created by an explicit human action.
3. `python scripts/approve_strategy.py --rank <N>` is the canonical strategy-to-script approval action.
4. A validated script remains a draft for Joel's review; it is not publishing approval.
5. Thumbnail concepts may be generated from a validated script, but actual thumbnail image generation remains a separate human-triggered action.

## Agent boundary
1. Deterministic Python owns API calls, raw metrics, scoring, snapshot/velocity calculations, approval records, context construction, validation, persistence, word counting, and report rendering.
2. Hermes owns operational execution and delegates judgment/creative work to focused subagents.
3. The Strategist reasons from supplied research evidence and must not invent metrics or sources.
4. The Script Writer develops only the approved opportunity and must not silently switch topics.
5. The Thumbnail Director develops packaging directions only from the validated script and approved evidence.
6. Competitor titles/performance are topic and packaging-territory evidence, not transcripts, factual sources, or evidence of competitor thumbnail visuals.
7. The Thumbnail Director must never infer a competitor's thumbnail composition, colors, objects, facial expression, or text from a video title.
8. Missing Joel-specific script results or opinions use `[JOEL: ...]` placeholders; missing thumbnail assets are listed in `creator_assets_needed`.
9. Unsupported current or technical script facts remain in `verification_notes` rather than being asserted as settled fact.

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
11. Do not call an image-generation tool from the Milestone 4 Thumbnail Director workflow.

## Verification
Before considering Milestone 4 complete:
- run `python -m pytest`
- run `python scripts/init_db.py` against the existing server database
- run `python scripts/prepare_thumbnail.py` and confirm it selects the validated script
- perform one real Hermes Thumbnail Director delegation
- confirm finalization rejects hallucinated source IDs, excessive thumbnail text, and duplicate visual hooks
- confirm exactly three concepts plus one recommended rank are persisted and rendered
- confirm no image generation, upload, publishing, scheduling, or account mutation occurs
- update documentation when configuration or behavior changes

## Architecture ownership
Hermes: operations plus focused Strategist, Script Writer, and Thumbnail Director delegation.
Codex: codebase, tests, integrations, migrations, debugging, deployment improvements.
