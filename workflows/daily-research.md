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
   - top 3 outliers
   - their outlier scores
   - report path
7. If execution fails, do not invent results. Report the exact stage that failed and preserve the error for Codex investigation.

## Guardrails
- Do not modify YouTube accounts.
- Do not publish anything.
- Do not expose `.env` values.
- Do not replace deterministic outlier scores with subjective scores.
- Source URLs must remain attached to research findings.

## Later milestone
Once this workflow is reliable, Hermes will add research subagents and a strategist above this deterministic data collection layer.
