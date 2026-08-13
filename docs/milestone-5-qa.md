# Milestone 5: Content QA Gate

Milestone 5 reviews the validated Script Writer + Thumbnail Director package as one unit. It is a non-mutating quality gate.

## Flow

`validated script -> validated thumbnail direction -> deterministic QA input -> one Hermes QA subagent -> deterministic QA validation -> SQLite + Markdown`

## Status semantics

- `PASS`: the generated package is coherent enough for Joel's next human production step.
- `NEEDS_CHANGES`: a material generated-package defect should be fixed before proceeding.

A QA status is never publishing approval.

## Expected open human work

The Script Writer may intentionally leave:
- `[JOEL: ...]` creator placeholders
- `creator_inputs_needed`
- `verification_notes`

These are displayed separately in the QA report. Their existence alone does not force `NEEDS_CHANGES` when they are explicit and honest.

## Blocking logic

A `BLOCKER` or `HIGH` finding requires `NEEDS_CHANGES`. Any finding with `blocks_next_step=true` also requires `NEEDS_CHANGES`.

`PASS` may include non-blocking `MEDIUM` or `LOW` observations.

`NEEDS_CHANGES` must contain at least one real blocking/HIGH/BLOCKER finding.

## Server commands

```bash
python scripts/init_db.py
python -m pytest
python scripts/prepare_qa.py
```

Hermes then follows `workflows/content-qa.md`, delegates exactly one QA subagent with `prompts/qa.md`, and saves JSON to `outputs/YYYY-MM-DD-qa-draft.json`.

Finalize with:

```bash
python scripts/finalize_qa.py \
  outputs/YYYY-MM-DD-qa-input.json \
  outputs/YYYY-MM-DD-qa-draft.json
```

Canonical outputs:
- `outputs/YYYY-MM-DD-qa.json`
- `outputs/YYYY-MM-DD-qa.md`

## Guardrails

Milestone 5 does not rewrite the script or thumbnail concepts, generate images, edit video, publish, schedule, upload, or mutate any YouTube account.
