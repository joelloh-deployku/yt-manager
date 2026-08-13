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
2. `python scripts/prepare_daily_strategy.py` packages the latest completed research run into structured strategist input.
3. Hermes delegates one focused Strategist subagent using `prompts/strategist.md`.
4. The Strategist returns three ranked opportunities tied to real source video IDs.
5. `python scripts/finalize_strategy.py ...` validates the evidence, stores the strategy in SQLite, and renders a Markdown brief.

## Milestone 3: Human-approved Script Writer

Milestone 3 adds script writing behind a hard human approval boundary:

1. Joel explicitly approves one validated strategist opportunity with `python scripts/approve_strategy.py --rank <N>`.
2. The approval is persisted in SQLite; without it, script preparation fails.
3. `python scripts/prepare_script.py` packages exactly that approved opportunity, channel profile, human notes, and permitted inspiration sources into script-input JSON.
4. Hermes delegates one focused Script Writer subagent using `prompts/script-writer.md`.
5. The Script Writer returns three original title options, a video brief, a full script, source IDs, creator-input placeholders, and verification notes.
6. `python scripts/finalize_script.py ...` enforces the approval IDs, source IDs, minimum structure/word count, title-copy protection, persistence, and Markdown rendering.

Competitor source records contain titles and performance metadata only. They are useful for topic/packaging evidence, but they are not transcripts or factual sources for the script. Missing Joel-specific results must remain explicit `[JOEL: ...]` placeholders rather than fabricated first-person claims.

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

### Research and strategy

```bash
python scripts/run_daily_research.py
python scripts/prepare_daily_strategy.py
```

After Hermes produces `outputs/YYYY-MM-DD-strategy-draft.json`:

```bash
python scripts/finalize_strategy.py \
  outputs/YYYY-MM-DD-strategist-input.json \
  outputs/YYYY-MM-DD-strategy-draft.json
```

### Explicitly approve one opportunity for scripting

Review the validated strategy first. Then, as the human approval action:

```bash
python scripts/approve_strategy.py --rank 1
```

Optional creative direction can be captured with:

```bash
python scripts/approve_strategy.py --rank 1 --notes "Make the demo practical and show the failure mode first."
```

Hermes must not choose or run this approval on Joel's behalf unless Joel explicitly instructs Hermes to approve that exact rank.

### Prepare and finalize the script

```bash
python scripts/prepare_script.py
```

After the real Hermes Script Writer produces `outputs/YYYY-MM-DD-script-draft.json`:

```bash
python scripts/finalize_script.py \
  outputs/YYYY-MM-DD-script-input.json \
  outputs/YYYY-MM-DD-script-draft.json
```

The default minimum full-script length is `SCRIPT_MIN_WORDS=600`. This is a completeness floor, not a target duration.

Reports are written to `outputs/`. Runtime state is stored in `data/yt_manager.db`. Both are ignored by Git.

The default candidate window is 14 days (`CANDIDATE_WINDOW_DAYS=14`). Repeated research runs append view observations to `video_snapshots`, allowing strategist context to include measured view velocity once multiple observations exist.

See:
- `docs/hermes-server-setup.md` for the home-server walkthrough
- `workflows/daily-research.md` for deterministic research
- `workflows/daily-strategy.md` for the Hermes Strategist procedure
- `workflows/script-writing.md` for the approved Script Writer procedure
- `schemas/strategist-output.schema.json` for the Strategist contract
- `schemas/script-writer-output.schema.json` for the Script Writer contract

## Division of responsibility

- **Hermes:** runs operational workflows and delegates focused Strategist/Script Writer subagents.
- **Codex:** engineers, tests, debugs, and improves this repository from the main machine.
- **Deterministic Python:** API ingestion, scoring, velocity, human approval records, context construction, persistence, validation, word counting, and reporting.
- **Hermes Strategist:** qualitative opportunity selection using supplied source-backed research context.
- **Hermes Script Writer:** creative development of exactly one human-approved opportunity into a source-aware first-draft script.
- **Joel:** selects the opportunity and reviews the script before recording or any later publishing step.

## After Milestone 3

Once the Script Writer is reliable, the next layers are thumbnail direction, QA, delivery, analytics, additional research agents, and the weekly channel audit.
