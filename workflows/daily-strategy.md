# Hermes Workflow: Daily Strategy

## Purpose
Turn the latest deterministic YouTube research run into a short, evidence-backed decision brief containing the best content opportunities for Joel. This is Milestone 2: choose opportunities and angles, but do not write full scripts, create thumbnails, or publish content.

## Agent boundary
- Deterministic Python owns metrics, source data, velocity calculation, validation, persistence, and report rendering.
- One Hermes Strategist subagent owns judgment: relevance, transferability, timing, packaging insight, and prioritization.
- The Strategist must never invent metrics or use unsourced evidence.

## Run procedure
1. Change into the `yt-manager` repository and activate its virtual environment.
2. Run `python scripts/run_daily_research.py` and confirm it succeeds.
3. Run `python scripts/prepare_daily_strategy.py`.
4. Read the generated `outputs/YYYY-MM-DD-strategist-input.json`.
5. Delegate one focused Strategist subagent using `prompts/strategist.md` as its instructions and the strategist-input JSON as its evidence.
6. Require JSON-only output matching `schemas/strategist-output.schema.json`.
7. Save that raw agent output as `outputs/YYYY-MM-DD-strategy-draft.json`.
8. Run:
   `python scripts/finalize_strategy.py outputs/YYYY-MM-DD-strategist-input.json outputs/YYYY-MM-DD-strategy-draft.json`
9. If finalization fails, give the validation error back to the Strategist for one correction attempt. Do not manually weaken validation or invent missing source IDs.
10. Read `outputs/YYYY-MM-DD-strategy.md` and return a concise operational summary of the ranked opportunities.

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

## Success criteria
A successful daily strategy run produces:
- one strategist-input JSON
- one validated canonical strategy JSON
- one human-readable strategy Markdown report
- one persisted strategy report in SQLite
- up to three ranked, source-backed opportunities for Joel
