# Hermes Workflow: Approved Script Writing

## Purpose
Turn exactly one human-approved Strategist opportunity into a validated video brief and full first-draft script. This is Milestone 3. It does not create thumbnails, publish, schedule, or modify any YouTube account.

## Hard human approval gate
Hermes must never approve an opportunity on Joel's behalf.

The approval command is human-only:

`python scripts/approve_strategy.py --rank <N> [--notes "optional direction"]`

Hermes may explain this command, but must not run it unless Joel explicitly instructs Hermes to approve that exact rank in the current conversation. Without an approval record, stop before Script Writer delegation.

## Agent boundary
- Deterministic Python owns approval records, context construction, source IDs, evidence limits, validation, persistence, word counting, and Markdown rendering.
- One Hermes Script Writer subagent owns creative development of the approved idea into a brief and full script.
- Competitor records are inspiration/performance evidence only; they are not transcripts or substantive factual sources.

## Run procedure after human approval
1. Change into the `yt-manager` repository and activate its virtual environment.
2. Do **not** rerun strategy or choose a different opportunity.
3. Run `python scripts/prepare_script.py`.
4. Read the generated `outputs/YYYY-MM-DD-script-input.json` completely.
5. Read `prompts/script-writer.md` and `schemas/script-writer-output.schema.json` completely.
6. Call the built-in `delegate_task` tool exactly once for the Script Writer step. Do not invent a script-generation Python command and do not simulate the subagent yourself.
7. In the delegated context, explicitly provide the project root, prompt path, script-input path, schema path, and output path.
8. Require the delegated Script Writer to write JSON only to `outputs/YYYY-MM-DD-script-draft.json`.
9. Verify the draft file exists and parses as JSON.
10. Run:
    `python scripts/finalize_script.py outputs/YYYY-MM-DD-script-input.json outputs/YYYY-MM-DD-script-draft.json`
11. If finalization fails, give the exact validation error back to the same Script Writer for at most one correction attempt. Do not weaken validation.
12. Only after finalization exits successfully, read `outputs/YYYY-MM-DD-script.md` and summarize the working title, brief, word count, creator inputs needed, and verification items for Joel.

## Script integrity rules
- Never fabricate Joel's first-hand experience. Use `[JOEL: ...]` placeholders when his real result or opinion is required.
- Never infer competitor video contents from a title.
- Do not invent product facts, prices, benchmarks, release details, or statistics.
- Put unresolved current/technical facts in `verification_notes`.
- Preserve the approved strategic angle, but make title and script original.
- A valid script draft is still subject to Joel's review before recording.

## Guardrails
- No thumbnail prompts or thumbnail generation.
- No automatic fact browsing in this milestone.
- No video editing.
- No YouTube publishing or scheduling.
- No account mutation.
- No automatic approval of another opportunity.

## Success criteria
A successful Milestone 3 run produces:
- an explicit human approval row in SQLite
- one script-input JSON for that approval
- one real delegated Script Writer result
- one validated canonical script JSON
- one human-readable Markdown brief + full script
- one persisted script report in SQLite
- explicit creator placeholders and factual verification notes where needed
