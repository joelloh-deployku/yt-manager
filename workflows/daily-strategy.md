# Hermes Workflow: Daily Strategy

## Purpose
Turn the latest deterministic YouTube research run into a short, evidence-backed decision brief containing the best content opportunities for Joel. This is Milestone 2: choose opportunities and angles, but do not write full scripts, create thumbnails, or publish content.

## Agent boundary
- Deterministic Python owns metrics, source data, velocity calculation, validation, persistence, and report rendering.
- One Hermes Strategist subagent owns judgment: relevance, transferability, timing, packaging insight, and prioritization.
- The Strategist must never invent metrics or use unsourced evidence.

## Non-negotiable delegation rule
Use Hermes's built-in `delegate_task` tool exactly once for the Strategist judgment step. Do not invent or call a `generate_strategy.py` script; no such script is part of this workflow. Do not simulate a subagent response in the parent conversation.

If `delegate_task` is unavailable or disabled, stop and report that delegation is unavailable. Do not continue with placeholders, an assumed result, or an "assuming validation passes" summary.

The delegated child starts with fresh context. Pass the project root and all required file paths explicitly in the delegation context. The child must work in the same repository filesystem and write its JSON result to the requested draft path.

## Run procedure
1. Change into the `yt-manager` repository and activate its virtual environment.
2. Run `python scripts/run_daily_research.py` and confirm it actually exits successfully.
3. Run `python scripts/prepare_daily_strategy.py` and confirm the strategist-input file exists.
4. Determine today's exact paths, including:
   - project root
   - `prompts/strategist.md`
   - `schemas/strategist-output.schema.json`
   - `outputs/YYYY-MM-DD-strategist-input.json`
   - `outputs/YYYY-MM-DD-strategy-draft.json`
5. Call Hermes's `delegate_task` tool exactly once. Give the child a focused goal to act as Joel's Strategist. In the delegation context, explicitly provide the project root and instruct the child to:
   - read `prompts/strategist.md`
   - read the strategist-input JSON
   - obey `schemas/strategist-output.schema.json`
   - produce no prose outside the JSON payload
   - write the final JSON payload to `outputs/YYYY-MM-DD-strategy-draft.json`
   - use only source video IDs present in the strategist input
6. Wait for the real delegation result. Verify `outputs/YYYY-MM-DD-strategy-draft.json` exists and parses as JSON. Never substitute placeholder opportunities.
7. Run:
   `python scripts/finalize_strategy.py outputs/YYYY-MM-DD-strategist-input.json outputs/YYYY-MM-DD-strategy-draft.json`
8. Require a real zero exit status from finalization. If it fails, report the exact validator error. For Milestone 2 manual validation, do not silently rewrite or weaken the payload in the parent agent.
9. Confirm `outputs/YYYY-MM-DD-strategy.md` exists, then read the actual file.
10. Return a concise operational summary of the actual ranked opportunities. Do not say a step passed unless its command/tool actually ran successfully.

## What the Strategist should optimize for
- Strong fit with Joel's channel profile.
- Evidence from measured competitor performance, maturity, and velocity where available.
- Original angles Joel can build, test, demonstrate, or explain.
- Useful packaging lessons without copying competitors.
- Honest confidence and explicit caveats.

## Interpretation rules
- A breakout is strong performance evidence, not an automatic recommendation.
- A mature underperformer weakens confidence.
- An upload under 48 hours old is provisional; do not call it a failure solely from raw outlier score.
- When velocity becomes available from repeated daily snapshots, use it to interpret young videos.
- Relevance and measured performance must remain separate concepts.

## Guardrails
- No full script writing in this milestone.
- No thumbnail generation in this milestone.
- No YouTube publishing, scheduling, account mutation, or external posting.
- Never expose `.env` values.
- Every recommendation must trace back to source video IDs in the current strategist input.
- Do not use unrelated external research unless a later workflow explicitly adds another research agent.
- Never fabricate command output, tool output, generated files, or validation success.

## Success criteria
A successful daily strategy run produces:
- one strategist-input JSON
- one real `delegate_task` execution
- one strategist-draft JSON written by the delegated child
- one validated canonical strategy JSON
- one human-readable strategy Markdown report
- one persisted strategy report in SQLite
- up to three ranked, source-backed opportunities for Joel
