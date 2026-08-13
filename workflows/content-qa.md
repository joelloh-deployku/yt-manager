# Hermes Workflow: Content QA Gate

## Purpose
Review the latest validated script + thumbnail package as one unit and produce a deterministic QA decision: `PASS` or `NEEDS_CHANGES`.

Milestone 5 is a review gate. It does not rewrite the script, rewrite thumbnail concepts, generate images, edit video, publish, schedule, or mutate any YouTube account.

## Agent boundary
- Deterministic Python owns package selection, IDs, QA input construction, validation, persistence, and Markdown rendering.
- One Hermes QA subagent owns judgment about coherence, alignment, evidence hygiene, creator-input hygiene, and workflow integrity.
- The QA subagent must review only what is present in the QA input.
- The parent Hermes agent must not perform, simulate, or narrate the QA review itself.

## Meaning of PASS
`PASS` means the generated package is coherent enough for Joel's next human production step.

It does **not** mean:
- factual verification is complete;
- creator placeholders have been filled;
- recording/editing is complete;
- Joel approved publishing;
- YouTube publishing or account mutation is authorized.

Existing `[JOEL: ...]` placeholders and `verification_notes` are expected open human tasks. Their existence alone is not a QA failure when they are explicit and honest.

## Required Hermes delegation interface
Hermes must use the built-in `delegate_task` tool, not bash and not a fabricated command.

The single-task interface is:

`delegate_task(goal="...", context="...")`

Do **not** use invented arguments such as `workflow_path`, `input_path`, or `output_path` on `delegate_task`. Do not print a pseudo-call in a code block and then continue as if it ran.

For this workflow, make exactly one real tool call equivalent to:

`delegate_task(goal="Review the validated YouTube content package for Milestone 5 QA and write the required QA JSON draft", context="Project root: /home/ubuntu/yt-manager. Read /home/ubuntu/yt-manager/prompts/qa.md, /home/ubuntu/yt-manager/outputs/YYYY-MM-DD-qa-input.json, and /home/ubuntu/yt-manager/schemas/qa-output.schema.json completely. Review only that supplied package. Write JSON only to /home/ubuntu/yt-manager/outputs/YYYY-MM-DD-qa-draft.json. Do not browse, rewrite upstream assets, generate images, publish, schedule, or mutate accounts. Existing [JOEL: ...] placeholders and verification_notes are open human tasks, not defects by themselves.")`

The child starts with a fresh conversation, so the `goal` and `context` must contain every required path, constraint, and output requirement.

If `delegate_task` is unavailable, errors, is interrupted, or no real child completion is received, **stop and report the failure**. Do not substitute parent-agent QA and do not fabricate output.

## Run procedure
1. Change into `/home/ubuntu/yt-manager` and activate its virtual environment.
2. Run `python scripts/prepare_qa.py`.
3. Read the generated `outputs/YYYY-MM-DD-qa-input.json` completely.
4. Read `prompts/qa.md` and `schemas/qa-output.schema.json` completely.
5. Call the built-in `delegate_task` tool **exactly once**, using only its real single-task interface with `goal` and `context` as described above.
6. After Hermes returns a delegation handle/status, do not advance merely because a tool call was described. Wait for the real child completion/result notification.
7. The delegated child must write JSON only to `outputs/YYYY-MM-DD-qa-draft.json`.
8. After child completion, verify the artifact with real filesystem checks. At minimum run:
   - `test -f outputs/YYYY-MM-DD-qa-draft.json`
   - `python -m json.tool outputs/YYYY-MM-DD-qa-draft.json >/dev/null`
   If either command fails, stop and report the exact failure.
9. Actually run:
   `python scripts/finalize_qa.py outputs/YYYY-MM-DD-qa-input.json outputs/YYYY-MM-DD-qa-draft.json`
10. Capture and inspect the real finalizer exit status/stdout. Do not say finalization succeeded unless the command exited successfully.
11. If finalization fails, give the exact validation error back to the same QA subagent for at most one correction attempt. Do not weaken validation and do not spawn a second QA subagent.
12. Only after successful finalization, verify that both canonical files exist:
   - `outputs/YYYY-MM-DD-qa.json`
   - `outputs/YYYY-MM-DD-qa.md`
13. Read the real `outputs/YYYY-MM-DD-qa.md` and report the status, strengths, findings, open creator inputs, verification items, and recommended next action.

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
- No parent-agent simulation of `delegate_task`.
- No fabricated child result, draft path, finalizer result, QA status, finding, or canonical output.
- No automatic script revisions.
- No automatic thumbnail revisions.
- No image generation.
- No video editing.
- No publishing or scheduling.
- No YouTube account mutation.
- A QA PASS is not publishing approval.

## Success criteria
A successful run requires observable evidence of all of the following:
- one deterministic QA-input JSON tied to a validated script + thumbnail report;
- one real built-in `delegate_task(goal=..., context=...)` invocation;
- one real child completion result;
- a real `outputs/YYYY-MM-DD-qa-draft.json` file written by the delegated child;
- successful JSON parsing of that draft;
- successful execution of `finalize_qa.py`;
- one validated canonical QA JSON;
- one human-readable QA Markdown report;
- one persisted QA report plus structured findings in SQLite;
- a clear PASS/NEEDS_CHANGES decision without modifying upstream content assets.
