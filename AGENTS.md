# AGENTS.md

## Mission
Build and maintain a reliable AI-assisted YouTube content operations system. Hermes operates the workflow on the home server. Codex owns engineering, testing, debugging, and maintainability.

## Established foundation
- Milestone 1: deterministic YouTube research, 14-day candidate window, historical baselines, outlier scoring, snapshots/velocity, SQLite, Markdown reporting.
- Milestone 2: versioned channel profile, source-backed Hermes Strategist, deterministic strategy validation/persistence.
- Milestone 3: explicit human strategy approval, one Hermes Script Writer, creator placeholders, verification notes, deterministic script validation/persistence.
- Milestone 4: one Hermes Thumbnail Director, exactly three distinct concepts plus a recommended rank, text/source/originality checks, creator-asset requirements, SQLite persistence. No image generation.

## Milestone 5 scope
Milestone 5 adds a non-mutating QA gate after the validated script + thumbnail package:
- deterministic QA input tied to the validated package lineage
- one focused Hermes QA subagent
- `PASS` or `NEEDS_CHANGES`
- structured strengths and findings with severity, area, evidence, recommended action, and blocking flag
- deterministic status validation, Markdown rendering, and additive SQLite QA persistence

Milestone 5 does not automatically revise scripts or thumbnail concepts. It does not generate images, edit video, publish, schedule, or mutate any YouTube account.

## Human boundaries
1. Hermes must not approve a strategy opportunity on Joel's behalf.
2. Script writing requires explicit human approval recorded in `script_approvals`.
3. A validated script remains a draft for Joel's review.
4. Thumbnail concepts do not authorize image generation.
5. QA `PASS` means ready for the next human production step, not fact-check completion or publishing approval.

## Agent boundaries
1. Deterministic Python owns API calls, scoring, approval records, context construction, validation, persistence, limits, and report rendering.
2. Hermes delegates judgment/creative work to focused subagents.
3. Strategist: select source-backed opportunities only from supplied research.
4. Script Writer: develop only the approved opportunity; never fabricate Joel's experience.
5. Thumbnail Director: develop packaging directions only; never infer competitor thumbnail visuals from titles.
6. QA: review the supplied validated script + thumbnail package; do not rewrite either asset in the QA response.
7. Competitor titles/performance are topic/packaging evidence, not transcripts or factual sources.
8. Missing Joel evidence stays in `[JOEL: ...]` placeholders / `creator_inputs_needed`; unresolved facts stay in `verification_notes`.

## QA rules
- Allowed statuses: `PASS`, `NEEDS_CHANGES`.
- Any `BLOCKER` or `HIGH` finding requires `NEEDS_CHANGES`.
- Any finding explicitly marked as blocking requires `NEEDS_CHANGES`.
- `PASS` may include non-blocking `MEDIUM` or `LOW` observations.
- `NEEDS_CHANGES` must identify at least one real material defect; do not manufacture findings.
- Explicit creator placeholders and verification notes are expected open human work, not automatic QA defects when clearly surfaced.
- Findings must cite evidence present in the supplied QA input.
- Do not claim to inspect rendered thumbnail pixels when only concept descriptions are available.

## Engineering rules
1. Inspect existing code/docs before changes.
2. Prefer deterministic Python for API, scoring, approval, persistence, validation, and reporting.
3. Use agents only for genuine judgment or creative synthesis.
4. Never commit secrets, credentials, database files, logs, or generated reports.
5. Add/update tests for meaningful behavior changes.
6. Fail loudly with actionable errors.
7. Keep runtime state in SQLite, not Git.
8. Do not publish or mutate creator accounts without explicit human approval.
9. Do not call image generation from Thumbnail Director or QA workflows.
10. QA is advisory/non-mutating; revisions require a later explicit workflow or human action.

## Milestone 5 verification
- `python -m pytest`
- `python scripts/init_db.py` against the existing server database
- `python scripts/prepare_qa.py`
- one real Hermes QA delegation following `workflows/content-qa.md`
- validate PASS/NEEDS_CHANGES blocking logic
- confirm open creator/fact-check items remain separately visible
- confirm QA persistence/rendering does not modify upstream assets or external accounts

## Architecture ownership
Hermes: operations plus Strategist, Script Writer, Thumbnail Director, and QA delegation.
Codex: codebase, tests, integrations, migrations, debugging, deployment improvements.
