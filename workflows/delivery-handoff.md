# Hermes Workflow: Production Handoff / Delivery

## Purpose
Turn the latest QA-passed script + thumbnail package into one actionable recording and editing handoff for Joel.

Milestone 6 organizes human production work. It does not generate a thumbnail image, edit video, upload, publish, schedule, or mutate any YouTube account.

## Preconditions
- Milestone 5 has a persisted QA report with status `PASS`.
- The QA report points to a validated script and validated Thumbnail Director report.
- Open creator inputs and verification notes may still exist; this workflow organizes them rather than pretending they are complete.

## Agent boundary
- Deterministic Python owns QA-PASS gating, package selection, context construction, coverage validation, persistence, and Markdown rendering.
- One Hermes Delivery Producer subagent owns sequencing and production-planning judgment.
- The parent Hermes agent must not write or simulate the delivery plan itself.

## Required Hermes delegation interface
Use the built-in `delegate_task` tool exactly once with its real single-task interface:

`delegate_task(goal="...", context="...")`

Do not use invented arguments such as `workflow_path`, `input_path`, or `output_path`. Do not print a pseudo-call and continue as though it ran.

The child starts with fresh context, so pass every required path and constraint in `goal` and `context`.

If delegation is unavailable, errors, or no real child completion is received, stop and report the failure. Do not substitute parent-agent work.

## Run procedure
1. Change into `/home/ubuntu/yt-manager` and activate the virtual environment.
2. Do not rerun research, strategy, script writing, thumbnail direction, or QA.
3. Run `python scripts/prepare_delivery.py`.
4. Read `outputs/YYYY-MM-DD-production-input.json` completely.
5. Read `prompts/delivery-producer.md` and `schemas/delivery-output.schema.json` completely.
6. Call built-in `delegate_task` exactly once. The call must be equivalent to:
   `delegate_task(goal="Create the Milestone 6 human production handoff from the QA-passed package and write the JSON draft", context="Project root: /home/ubuntu/yt-manager. Read prompts/delivery-producer.md, outputs/YYYY-MM-DD-production-input.json, and schemas/delivery-output.schema.json completely. Preserve the validated script and recommended thumbnail concept. Cover every supplied creator placeholder exactly once and every verification-note item exactly once. Write JSON only to outputs/YYYY-MM-DD-delivery-draft.json. Do not browse, rewrite upstream assets, generate images, edit video, upload, publish, schedule, or mutate accounts.")`
7. Wait for real child completion.
8. Verify the child artifact with real filesystem checks:
   - `test -f outputs/YYYY-MM-DD-delivery-draft.json`
   - `python -m json.tool outputs/YYYY-MM-DD-delivery-draft.json >/dev/null`
   Stop on failure.
9. Actually run:
   `python scripts/finalize_delivery.py outputs/YYYY-MM-DD-production-input.json outputs/YYYY-MM-DD-delivery-draft.json`
10. Do not claim success unless the real finalizer exits successfully.
11. If validation fails, return the exact validation error to the same Delivery Producer for at most one correction attempt. Do not weaken validation or spawn a second producer.
12. After successful finalization, verify:
   - `outputs/YYYY-MM-DD-delivery.json`
   - `outputs/YYYY-MM-DD-delivery.md`
13. Read the real Markdown report and summarize the shoot order, required creator inputs, verification work, thumbnail capture needs, asset plan, editing notes, and pre-recording checklist.

## Coverage rules
- Every creator placeholder from the validated script appears exactly once in `recording_plan[].creator_inputs`.
- Every verification-note `item` appears exactly once in `verification_plan`.
- The recommended thumbnail rank, concept name, thumbnail text, and creator-assets list are preserved exactly.
- Required thumbnail assets appear in `asset_plan`.
- Recording segments use only script sections supplied in the deterministic input.

## Human boundary
The resulting delivery report is a production brief for Joel. It is not proof that creator inputs are completed, facts are verified, footage is recorded, editing is done, or publishing is approved.

## Success criteria
A successful Milestone 6 run produces one QA-PASS-gated input, one real delegated Delivery Producer result, one validated canonical delivery JSON, one human-readable delivery Markdown report, and persisted production report/items without modifying upstream script/thumbnail/QA assets.
