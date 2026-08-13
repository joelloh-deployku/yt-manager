# AGENTS.md

## Mission
Build and maintain a reliable AI-assisted YouTube content operations system. Hermes operates the workflow on the home server. Codex owns engineering, testing, debugging, and maintainability.

## Established foundation
- Milestone 1: deterministic YouTube research, 14-day candidate window, historical baselines, outlier scoring, snapshots/velocity, SQLite, Markdown reporting.
- Milestone 2: versioned channel profile, source-backed Hermes Strategist, deterministic strategy validation/persistence.
- Milestone 3: explicit human strategy approval, one Hermes Script Writer, creator placeholders, verification notes, deterministic script validation/persistence.
- Milestone 4: one Hermes Thumbnail Director, exactly three distinct concepts plus a recommended rank, text/source/originality checks, creator-asset requirements, SQLite persistence. No image generation.
- Milestone 5: one Hermes QA subagent, PASS/NEEDS_CHANGES gate, structured findings, deterministic QA persistence. QA is non-mutating.

## Milestone 6 scope
Milestone 6 adds a QA-PASS-gated human production handoff:
- deterministic input containing the validated script, QA PASS, recommended thumbnail concept, creator inputs, verification notes, and approval lineage
- one focused Hermes Delivery Producer subagent
- ordered recording segments, creator-input mapping, verification plan, thumbnail handoff, asset plan, editing notes, checklist, and risks
- deterministic coverage validation, Markdown rendering, and additive SQLite production persistence

Milestone 6 does not automatically resolve creator inputs or fact checks. It does not generate images, edit video, upload, publish, schedule, or mutate a YouTube account.

## Human boundaries
1. Hermes must not approve a strategy opportunity on Joel's behalf.
2. Script writing requires explicit human approval recorded in `script_approvals`.
3. A validated script remains a draft for Joel's review.
4. Thumbnail concepts do not authorize image generation.
5. QA `PASS` means ready for the next human production step, not fact-check completion or publishing approval.
6. A delivery report organizes recording/editing work; it does not prove Joel completed the work or authorize publishing.

## Agent boundaries
1. Deterministic Python owns API calls, scoring, approval records, context construction, validation, persistence, limits, gates, and report rendering.
2. Hermes delegates judgment/creative work to focused subagents.
3. Strategist: select source-backed opportunities only from supplied research.
4. Script Writer: develop only the approved opportunity; never fabricate Joel's experience.
5. Thumbnail Director: develop packaging directions only; never infer competitor thumbnail visuals from titles.
6. QA: review the supplied validated script + thumbnail package; do not rewrite either asset.
7. Delivery Producer: sequence and package human production work only; do not rewrite upstream script/thumbnail/QA assets or claim open work is complete.
8. Competitor titles/performance are topic/packaging evidence, not transcripts or factual sources.
9. Missing Joel evidence stays in `[JOEL: ...]` placeholders / `creator_inputs_needed`; unresolved facts stay in `verification_notes` until Joel resolves them.

## Delivery rules
- Delivery preparation requires a persisted QA report with status `PASS`.
- Every creator placeholder must appear exactly once across `recording_plan[].creator_inputs`.
- Every verification-note `item` must appear exactly once in `verification_plan`.
- Preserve the recommended thumbnail rank, concept name, thumbnail text, and creator-assets list exactly.
- Required thumbnail assets must appear in `asset_plan`.
- Recording segments may reference only deterministic script sections supplied in the input.
- Use the real Hermes `delegate_task(goal="...", context="...")` interface exactly once; never narrate or simulate delegation.

## Engineering rules
1. Inspect existing code/docs before changes.
2. Prefer deterministic Python for API, scoring, approval, persistence, validation, and reporting.
3. Use agents only for genuine judgment or creative synthesis.
4. Never commit secrets, credentials, database files, logs, or generated reports.
5. Add/update tests for meaningful behavior changes.
6. Fail loudly with actionable errors.
7. Keep runtime state in SQLite, not Git.
8. Do not publish or mutate creator accounts without explicit human approval.
9. Do not call image generation from Thumbnail Director, QA, or Delivery workflows.
10. QA and Delivery are advisory/non-mutating; revisions require an explicit later workflow or human action.

## Milestone 6 verification
- `python -m pytest`
- run `python scripts/prepare_delivery.py` against the existing QA-passed server state
- confirm preparation refuses non-PASS QA state
- one real Hermes Delivery Producer delegation following `workflows/delivery-handoff.md`
- confirm every creator placeholder and verification item is covered exactly once
- confirm the validated recommended thumbnail is preserved
- run the real finalizer and verify canonical JSON/Markdown plus SQLite rows
- confirm upstream script/thumbnail/QA assets and external accounts remain unchanged

## Architecture ownership
Hermes: operations plus Strategist, Script Writer, Thumbnail Director, QA, and Delivery Producer delegation.
Codex: codebase, tests, integrations, migrations, debugging, deployment improvements.
