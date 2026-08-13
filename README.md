# yt-manager

AI-assisted YouTube research and content operations system powered by an always-on Hermes operator and a Codex-maintained codebase.

## Milestone 1: Research foundation

Milestone 1 established deterministic competitor research, a configurable 14-day candidate window, historical channel baselines, outlier scoring, repeated view snapshots, velocity, and Markdown daily research reports stored against SQLite runtime state.

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
3. `python scripts/prepare_script.py` packages exactly that approved opportunity, channel profile, human notes, and permitted inspiration sources.
4. Hermes delegates one focused Script Writer using `prompts/script-writer.md`.
5. The Script Writer returns three original title options, a video brief, a full script, source IDs, creator-input placeholders, and verification notes.
6. `python scripts/finalize_script.py ...` enforces approval IDs, source IDs, minimum structure/word count, title-copy protection, persistence, and Markdown rendering.

Competitor source records contain titles and performance metadata only. They are useful for topic/packaging evidence, but they are not transcripts or factual sources for the script. Missing Joel-specific results remain explicit `[JOEL: ...]` placeholders rather than fabricated first-person claims.

## Milestone 4: Thumbnail Director

Milestone 4 turns one validated Script Writer report into auditable packaging directions without generating an image:

1. `python scripts/prepare_thumbnail.py` packages the latest validated script, approved strategy angle, channel profile, title/brief/hook, permitted source IDs, creator-input needs, and evidence limits.
2. Hermes delegates exactly one Thumbnail Director using `prompts/thumbnail-director.md`.
3. The Thumbnail Director returns exactly three distinct concepts plus one recommended rank.
4. Each concept contains short optional thumbnail text, a single visual hook, composition, title alignment, emotional tone, rationale, render-ready direction, creator assets needed, source IDs, and risks.
5. `python scripts/finalize_thumbnail.py ...` validates concept count/ranks, source IDs, text length, distinct visual hooks, and persistence before rendering Markdown.

There are **no competitor thumbnail images** in the Milestone 4 evidence set. The Thumbnail Director may use competitor performance as evidence that a topic territory is interesting, but it must not infer or copy competitor visual composition, colors, faces, objects, or text.

Milestone 4 deliberately stops before image generation. A render prompt is only a handoff for a later, separately human-triggered design step.

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

Optional direction can be captured with:

```bash
python scripts/approve_strategy.py --rank 1 --notes "Make the demo practical and show the failure mode first."
```

Hermes must not choose or run this approval on Joel's behalf unless Joel explicitly instructs Hermes to approve that exact rank.

### Prepare and finalize the script

```bash
python scripts/prepare_script.py
```

After Hermes produces `outputs/YYYY-MM-DD-script-draft.json`:

```bash
python scripts/finalize_script.py \
  outputs/YYYY-MM-DD-script-input.json \
  outputs/YYYY-MM-DD-script-draft.json
```

The default minimum full-script length is `SCRIPT_MIN_WORDS=600`. This is a completeness floor, not a target duration.

### Prepare and finalize thumbnail direction

```bash
python scripts/prepare_thumbnail.py
```

After Hermes produces `outputs/YYYY-MM-DD-thumbnail-draft.json`:

```bash
python scripts/finalize_thumbnail.py \
  outputs/YYYY-MM-DD-thumbnail-input.json \
  outputs/YYYY-MM-DD-thumbnail-draft.json
```

Thumbnail defaults are three concepts with at most five words of thumbnail text. They can be overridden locally with `THUMBNAIL_CONCEPT_COUNT` and `THUMBNAIL_MAX_TEXT_WORDS`; no `.env` change is required for the defaults.

Canonical thumbnail outputs are:
- `outputs/YYYY-MM-DD-thumbnails.json`
- `outputs/YYYY-MM-DD-thumbnails.md`

Reports are written to `outputs/`. Runtime state is stored in `data/yt_manager.db`. Both are ignored by Git.

See:
- `docs/hermes-server-setup.md` for the home-server walkthrough
- `workflows/daily-research.md` for deterministic research
- `workflows/daily-strategy.md` for the Hermes Strategist procedure
- `workflows/script-writing.md` for the approved Script Writer procedure
- `workflows/thumbnail-direction.md` for Thumbnail Director procedure
- `schemas/strategist-output.schema.json` for the Strategist contract
- `schemas/script-writer-output.schema.json` for the Script Writer contract
- `schemas/thumbnail-director-output.schema.json` for the Thumbnail Director contract

## Division of responsibility

- **Hermes:** runs operational workflows and delegates focused Strategist, Script Writer, and Thumbnail Director subagents.
- **Codex:** engineers, tests, debugs, and improves this repository from the main machine.
- **Deterministic Python:** API ingestion, scoring, velocity, human approval records, context construction, persistence, validation, word/text limits, and reporting.
- **Hermes Strategist:** selects source-backed opportunities.
- **Hermes Script Writer:** develops exactly one human-approved opportunity into a first-draft script.
- **Hermes Thumbnail Director:** develops three packaging concepts from the validated script without generating an image.
- **Joel:** selects the opportunity, reviews the script, and controls any later image generation or publishing action.

## After Milestone 4

Once thumbnail direction is reliable, the next layers are content QA, human delivery/review, optional image generation, editing/publishing integrations, analytics, additional research agents, and the weekly channel audit.
