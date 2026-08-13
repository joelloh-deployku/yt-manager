# yt-manager

AI-assisted YouTube research and content operations system powered by an always-on Hermes operator and a Codex-maintained codebase.

## Milestone 1: Research foundation

Milestone 1 established:

1. Hermes runs on the home server.
2. GitHub is the shared source of truth for code and workflow instructions.
3. SQLite stores research runs, candidate videos, and repeated view snapshots locally on the server.
4. YouTube Data API collects uploads from configured competitor channels.
5. A configurable 14-day candidate window is compared against older historical uploads from each channel.
6. Deterministic raw outlier scoring classifies candidates as breakouts, watchlist items, or underperformers.
7. Each run produces one Markdown daily research report with candidate age and source links.

## Milestone 2: Hermes Strategist

Milestone 2 adds a judgment layer without weakening the deterministic research foundation:

1. `config/channel-profile.json` defines Joel's positioning, audience, pillars, and strategist preferences.
2. `python scripts/prepare_daily_strategy.py` packages the latest completed research run into a structured strategist-input JSON.
3. Hermes delegates one focused Strategist subagent using `prompts/strategist.md`.
4. The Strategist returns up to three ranked opportunities as JSON, each tied to source video IDs from the current research run.
5. `python scripts/finalize_strategy.py ...` validates the evidence, stores the strategy in SQLite, and renders a human-readable Markdown brief.

The agent makes qualitative decisions about relevance, timing, transferability, and packaging. Deterministic Python remains responsible for metrics, velocity, validation, persistence, and rendering.

No automatic publishing is included.

## Setup

```bash
git clone https://github.com/joelloh-deployku/yt-manager.git
cd yt-manager
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Configure `.env`, then initialize and test:

```bash
python scripts/init_db.py
python -m pytest
```

Run research:

```bash
python scripts/run_daily_research.py
```

Prepare the strategy context:

```bash
python scripts/prepare_daily_strategy.py
```

After Hermes produces `outputs/YYYY-MM-DD-strategy-draft.json`, validate and finalize it with:

```bash
python scripts/finalize_strategy.py \
  outputs/YYYY-MM-DD-strategist-input.json \
  outputs/YYYY-MM-DD-strategy-draft.json
```

Reports are written to `outputs/`. Runtime state is stored in `data/yt_manager.db`. Both are ignored by Git.

The default candidate window is 14 days (`CANDIDATE_WINDOW_DAYS=14`). Repeated research runs append view observations to `video_snapshots`, allowing strategist context to include measured view velocity once multiple observations exist.

See:
- `docs/hermes-server-setup.md` for the home-server walkthrough
- `workflows/daily-research.md` for deterministic research
- `workflows/daily-strategy.md` for the Hermes Strategist procedure
- `schemas/strategist-output.schema.json` for the agent output contract

## Division of responsibility

- **Hermes:** runs operational workflows and delegates the Strategist.
- **Codex:** engineers, tests, debugs, and improves this repository from the main machine.
- **Deterministic Python:** API ingestion, scoring, velocity calculation, persistence, validation, and reporting.
- **Hermes Strategist:** qualitative opportunity selection using only the supplied source-backed research context.

## After Milestone 2

Once strategy selection is reliable, the next layers are script writer, thumbnail director, QA, delivery, analytics, additional research agents, and the weekly channel audit.
