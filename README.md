# yt-manager

AI-assisted YouTube research and content operations system powered by an always-on Hermes operator and a Codex-maintained codebase.

## Milestone 1

The first milestone is intentionally narrow:

1. Hermes runs on the home server.
2. GitHub is the shared source of truth for code and workflow instructions.
3. SQLite stores research runs and candidate videos locally on the server.
4. YouTube Data API collects recent uploads from configured competitor channels.
5. Deterministic scoring ranks videos against each channel's recent median views.
6. Each run produces one Markdown daily research report.

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

Configure `.env`, then:

```bash
python scripts/init_db.py
python -m pytest
python scripts/run_daily_research.py
```

Reports are written to `outputs/`. Runtime state is stored in `data/yt_manager.db`. Both are ignored by Git.

See `docs/hermes-server-setup.md` for the home-server walkthrough and `workflows/daily-research.md` for Hermes's operating procedure.

## Division of responsibility

- **Hermes:** runs operational workflows on the home server.
- **Codex:** engineers, tests, debugs, and improves this repository from the main machine.
- **Deterministic Python:** API ingestion, scoring, persistence, validation, and reporting.

## After Milestone 1

Once daily research is reliable, the next layers are research subagents, strategist, script writer, thumbnail director, QA, delivery, analytics, and the weekly channel audit.
