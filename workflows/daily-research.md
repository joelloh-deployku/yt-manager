# Hermes Workflow: Daily Research

## Purpose
Produce one evidence-backed YouTube opportunity report from configured competitor channels. This is Milestone 1: do not write scripts, generate thumbnails, or publish content.

## Run procedure
1. Change into the `yt-manager` repository.
2. Confirm `.env` exists. Never print or expose its secret values.
3. Run `python scripts/run_daily_research.py`.
4. Confirm the command exits successfully.
5. Read the generated `outputs/YYYY-MM-DD-daily-research.md` report.
6. Return a short operational summary containing:
   - number of candidates analyzed
   - breakout count and strongest breakouts
   - relevant watchlist items worth monitoring even if they are not breakouts
   - raw outlier scores and candidate ages
   - report path
7. If execution fails, do not invent results. Report the exact stage that failed and preserve the error for Codex investigation.

## How to interpret the report
- **Breakout (>= 1.25x):** materially above the channel's historical median. Treat this as a performance signal, not automatic proof that Joel should copy the topic.
- **Watchlist (0.80x - 1.24x):** near normal channel performance. A highly relevant topic can still be strategically useful here.
- **Underperformer (< 0.80x):** below the historical median. Keep as negative evidence rather than calling it an opportunity.
- Keep **topic relevance** separate from the deterministic raw outlier score. Do not alter the score to make a topic look more relevant.
- The database records view snapshots on each run. Later milestones will use repeated observations to calculate real view velocity.

## Guardrails
- Do not modify YouTube accounts.
- Do not publish anything.
- Do not expose `.env` values.
- Do not replace deterministic outlier scores with subjective scores.
- Source URLs must remain attached to research findings.

## Later milestone
Once this workflow is reliable, Hermes will add research subagents and a strategist above this deterministic data collection layer.
