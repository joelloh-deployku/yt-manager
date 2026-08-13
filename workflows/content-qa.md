# Hermes Workflow: Content QA Gate

## Purpose
Review the latest validated script + thumbnail package as one unit and produce a deterministic QA decision: `PASS` or `NEEDS_CHANGES`.

Milestone 5 is a review gate. It does not rewrite the script, rewrite thumbnail concepts, generate images, edit video, publish, schedule, or mutate any YouTube account.

## Agent boundary
- Deterministic Python owns package selection, IDs, QA input construction, validation, persistence, and Markdown rendering.
- One Hermes QA subagent owns judgment about coherence, alignment, evidence hygiene, creator-input hygiene, and workflow integrity.
- The QA subagent must review only what is present in the QA input.

## Meaning of PASS
`PASS` means the generated package is coherent enough for Joel's next human production step.

It does **not** mean:
- factual verification is complete;
- creator placeholders have been filled;
- recording/editing is complete;
- Joel approved publishing;
- YouTube publishing or account mutation is authorized.

Existing `[JOEL: ...]` placeholders and `verification_notes` are expected open human tasks. Their existence alone is not a QA failure when they are explicit and honest.

## Run procedure
1. Change into the `yt-manager` repository and activate its virtual environment.
2. Run `python scripts/prepare_qa.py`.
3. Read the generated `outputs/YYYY-MM-DD-qa-input.json` completely.
4. Read `prompts/qa.md` and `schemas/qa-output.schema.json` completely.
5. Call the built-in `delegate_task` tool exactly once for the QA step. Do not invent a QA-generation Python command and do not simulate the subagent yourself.
6. In the delegated context, provide the project root, prompt path, QA-input path, schema path, and output path.
7. Require JSON-only output written to `outputs/YYYY-MM-DD-qa-draft.json`.
8. Verify the draft exists and parses as JSON.
9. Run:
   `python scripts/finalize_qa.py outputs/YYYY-MM-DD-qa-input.json outputs/YYYY-MM-DD-qa-draft.json`
10. If finalization fails, give the exact validation error back to the same QA subagent for at most one correction attempt. Do not weaken validation.
11. Only after finalization succeeds, read `outputs/YYYY-MM-DD-qa.md` and report the status, strengths, findings, open creator inputs, verification items, and recommended next action.

## Decision rules
- A `BLOCKER` or `HIGH` finding requires `NEEDS_CHANGES`.
- Any finding with `blocks_next_step=true` requires `NEEDS_CHANGES`.
- `PASS` may still include `MEDIUM` or `LOW` non-blocking observations.
- `NEEDS_CHANGES` must identify at least one real blocking/HIGH/BLOCKER defect.
- Do not manufacture findings merely to avoid returning an empty list.

## Review dimensions
- script integrity and promise consistency;
- title/thumbnail alignment;
- evidence and source hygiene;
- creator-input honesty;
- factual verification hygiene;
- packaging originality within the supplied evidence;
- workflow and approval integrity.

## Evidence limits
- No rendered thumbnail image is present unless a later workflow explicitly supplies one.
- Do not claim visual defects that are not described in the concept data.
- Do not infer competitor thumbnail visuals from competitor video titles.
- Do not browse for outside facts in this milestone.
- Do not mark verification notes as resolved.

## Guardrails
- No automatic script revisions.
- No automatic thumbnail revisions.
- No image generation.
- No video editing.
- No publishing or scheduling.
- No YouTube account mutation.
- A QA PASS is not publishing approval.

## Success criteria
A successful run produces:
- one deterministic QA-input JSON tied to a validated script + thumbnail report;
- one real delegated QA result;
- one validated canonical QA JSON;
- one human-readable QA Markdown report;
- one persisted QA report plus structured findings in SQLite;
- a clear PASS/NEEDS_CHANGES decision without modifying upstream content assets.
