# yt-manager

AI-assisted YouTube research and content operations system powered by an always-on Hermes operator and a Codex-maintained codebase.

## Milestone 1: Research foundation
Milestone 1 established deterministic competitor research, a configurable 14-day candidate window, historical channel baselines, outlier scoring, repeated view snapshots, velocity, and Markdown daily research reports stored against SQLite runtime state.

## Milestone 2: Hermes Strategist
Milestone 2 adds source-backed opportunity selection: `prepare_daily_strategy.py` packages the latest research, Hermes delegates one Strategist, and `finalize_strategy.py` validates/persists three ranked opportunities.

## Milestone 3: Human-approved Script Writer
Milestone 3 adds a hard human strategy-to-script approval boundary. `approve_strategy.py` records Joel's exact chosen rank, `prepare_script.py` packages that opportunity, Hermes delegates one Script Writer, and `finalize_script.py` validates a full source-aware script with creator placeholders and verification notes.

## Milestone 4: Thumbnail Director
Milestone 4 turns a validated script into exactly three distinct thumbnail/packaging concepts plus one recommended rank. It validates short thumbnail text, source IDs, distinct visual hooks, creator-asset needs, and render-ready direction. It does **not** generate a thumbnail image.

## Milestone 5: Content QA Gate
Milestone 5 reviews the validated script + thumbnail package as one unit without modifying either asset:

1. `python scripts/prepare_qa.py` packages the latest validated thumbnail report, its script, approved strategy lineage, creator inputs, verification notes, and deterministic checks.
2. Hermes delegates exactly one QA subagent using `prompts/qa.md`.
3. QA returns `PASS` or `NEEDS_CHANGES`, strengths, structured findings, and a recommended next action.
4. Every finding has severity, area, evidence, recommended action, and a boolean blocking flag.
5. `python scripts/finalize_qa.py ...` enforces status logic, persists one QA report plus findings, and renders Markdown.

`PASS` means the generated package is coherent enough for Joel's next human production step. It is **not** fact-check completion, recording approval, image-generation approval, or publishing approval.

Explicit `[JOEL: ...]` placeholders, `creator_inputs_needed`, and `verification_notes` remain visible as open human work. Their existence alone is not a QA failure when they are explicit and honest.

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

## Operational flow

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

### Human approval and script

```bash
python scripts/approve_strategy.py --rank 1
python scripts/prepare_script.py
```

After Hermes produces `outputs/YYYY-MM-DD-script-draft.json`:

```bash
python scripts/finalize_script.py \
  outputs/YYYY-MM-DD-script-input.json \
  outputs/YYYY-MM-DD-script-draft.json
```

### Thumbnail direction

```bash
python scripts/prepare_thumbnail.py
```

After Hermes produces `outputs/YYYY-MM-DD-thumbnail-draft.json`:

```bash
python scripts/finalize_thumbnail.py \
  outputs/YYYY-MM-DD-thumbnail-input.json \
  outputs/YYYY-MM-DD-thumbnail-draft.json
```

Thumbnail defaults are three concepts with at most five words of thumbnail text. Image generation remains a separate human-triggered step.

### Content QA

```bash
python scripts/prepare_qa.py
```

After Hermes produces `outputs/YYYY-MM-DD-qa-draft.json`:

```bash
python scripts/finalize_qa.py \
  outputs/YYYY-MM-DD-qa-input.json \
  outputs/YYYY-MM-DD-qa-draft.json
```

Canonical QA outputs are:
- `outputs/YYYY-MM-DD-qa.json`
- `outputs/YYYY-MM-DD-qa.md`

Reports are written to `outputs/`. Runtime state is stored in `data/yt_manager.db`. Both are ignored by Git.

## QA decision rules
- `BLOCKER` or `HIGH` findings require `NEEDS_CHANGES`.
- Any finding marked as blocking requires `NEEDS_CHANGES`.
- `PASS` may contain non-blocking `MEDIUM` or `LOW` observations.
- `NEEDS_CHANGES` must contain at least one real material blocking/HIGH/BLOCKER defect.
- QA findings must use evidence present in the supplied QA input.
- QA does not rewrite upstream assets.

## Key workflow files
- `workflows/daily-research.md`
- `workflows/daily-strategy.md`
- `workflows/script-writing.md`
- `workflows/thumbnail-direction.md`
- `workflows/content-qa.md`
- `prompts/strategist.md`
- `prompts/script-writer.md`
- `prompts/thumbnail-director.md`
- `prompts/qa.md`
- `schemas/strategist-output.schema.json`
- `schemas/script-writer-output.schema.json`
- `schemas/thumbnail-director-output.schema.json`
- `schemas/qa-output.schema.json`
- `docs/milestone-5-qa.md`

## Division of responsibility
- **Hermes:** operational execution and focused Strategist, Script Writer, Thumbnail Director, and QA delegation.
- **Codex:** engineering, tests, integrations, migrations, debugging, and maintainability.
- **Deterministic Python:** API ingestion, scoring, velocity, approvals, context construction, validation, persistence, limits, and reports.
- **Joel:** chooses the strategy opportunity, supplies real creator evidence/assets, reviews QA output, and controls any later image generation or publishing action.

## After Milestone 5
The next logical layer is a **human delivery/production handoff** that packages the QA-passed script, recommended thumbnail direction, creator inputs, and verification checklist into one recording/editing brief. Publishing remains a later explicit approval boundary.
